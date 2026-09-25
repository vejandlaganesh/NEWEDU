import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.conf import settings

from apps.ai_assistant.models import AIConversation, AIMessage, AIInteraction
from apps.ai_assistant.services.ai_service import GeminiService
from apps.ai_assistant.services.exceptions import AIError
from apps.ai_assistant.utils import rate_limit_ai_request
from apps.students.models import StudentProfile
from apps.academics.models import Enrollment, ClassSubject

@csrf_protect
@require_POST
@rate_limit_ai_request
def ai_chat_endpoint(request):
    """
    Handles student chat messages asynchronously.
    """
    if request.user.role != 'STUDENT':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        
    conversation_id = data.get('conversation_id')
    message_text = data.get('message', '').strip()
    subject_id = data.get('subject_id')
    
    # Message length limits
    MAX_LENGTH = getattr(settings, 'AI_MAX_MESSAGE_LENGTH', 2000)
    if not message_text:
        return JsonResponse({'error': 'Message cannot be empty.'}, status=400)
    if len(message_text) > MAX_LENGTH:
        return JsonResponse({'error': f'Message exceeds maximum length of {MAX_LENGTH} characters.'}, status=400)
        
    # Get or create active conversation
    if conversation_id:
        try:
            conversation = AIConversation.objects.get(id=conversation_id, user=request.user, is_archived=False)
        except AIConversation.DoesNotExist:
            return JsonResponse({'error': 'Conversation not found or archived.'}, status=404)
    else:
        # Create new active conversation. Title generated from first message.
        title = message_text[:50] + "..." if len(message_text) > 50 else message_text
        conversation = AIConversation.objects.create(user=request.user, title=title)
        
    # Save user message
    user_msg = AIMessage.objects.create(conversation=conversation, role='USER', content=message_text)
    
    # Build System Instruction (Context)
    system_instruction = "You are the NEWEDU AI Study Assistant. Act as an educational tutor. Guide step-by-step, do not blindly provide final answers for homework."
    
    try:
        student_profile = request.user.student_profile
        # Inject the student's active enrollment context. Academic data is stored on Enrollment,
        # not on StudentProfile, so never assume a current_class field exists.
        active_year = AcademicYear.objects.filter(is_active=True).first()
        enrollment = Enrollment.objects.filter(student=student_profile, academic_year=active_year).select_related(
            'class_level', 'section'
        ).first() if active_year else None
        if enrollment:
            system_instruction += f"\nStudent Class: {enrollment.class_level.name}\nStudent Section: {enrollment.section.name}"

        # Verify subject_id against the student's enrolled class.
        if subject_id and enrollment:
            class_subject = ClassSubject.objects.filter(
                id=subject_id, class_level=enrollment.class_level
            ).select_related('subject').first()
            if class_subject:
                system_instruction += f"\nCurrent Subject Focus: {class_subject.subject.name}"
    except Exception:
        # Failsafe if profile is missing
        pass

    try:
        # Get history (previous AIMessages)
        history = list(conversation.messages.filter(role__in=['USER', 'MODEL']).exclude(id=user_msg.id).order_by('created_at'))
        
        # Call Gemini
        service = GeminiService()
        response = service.generate_response(
            prompt=message_text,
            system_instruction=system_instruction,
            history=history
        )
        
        # Safe AI Interaction Log
        AIInteraction.objects.create(
            user=request.user,
            operation='chat',
            model_name=service.model_name,
            status='SUCCESS',
            prompt_tokens=response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') and response.usage_metadata else None,
            completion_tokens=response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') and response.usage_metadata else None
        )
        
        # Save model message
        model_msg = AIMessage.objects.create(
            conversation=conversation,
            role='MODEL',
            content=response.text,
            prompt_tokens=response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') and response.usage_metadata else None,
            completion_tokens=response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') and response.usage_metadata else None
        )
        
        return JsonResponse({
            'success': True,
            'conversation_id': conversation.id,
            'message': model_msg.content,
            'created_at': model_msg.created_at.isoformat()
        })
        
    except AIError as e:
        # Safe interaction log for errors
        AIInteraction.objects.create(
            user=request.user, operation='chat', model_name='unknown', status='FAILED', metadata={'error': str(e)}
        )
        return JsonResponse({'error': 'The AI assistant is temporarily unavailable. Please try again.'}, status=503)
    except Exception as e:
        AIInteraction.objects.create(
            user=request.user, operation='chat', model_name='unknown', status='FAILED', metadata={'error': 'unexpected server error'}
        )
        return JsonResponse({'error': 'An unexpected error occurred.'}, status=500)


@csrf_protect
@require_POST
def ai_archive_conversation_endpoint(request):
    """
    Archives a conversation.
    """
    if request.user.role != 'STUDENT':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
    conversation_id = data.get('conversation_id')
    if not conversation_id:
        return JsonResponse({'error': 'Missing conversation ID'}, status=400)
        
    try:
        conversation = AIConversation.objects.get(id=conversation_id, user=request.user, is_archived=False)
        conversation.is_archived = True
        conversation.save()
        return JsonResponse({'success': True})
    except AIConversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation not found.'}, status=404)
