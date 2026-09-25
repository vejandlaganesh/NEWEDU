import json
import os
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from apps.accounts.models import User
from apps.ai_assistant.models import AIConversation, AIMessage, AIInteraction
from apps.ai_assistant.services.ai_service import GeminiService
from apps.ai_assistant.services.exceptions import (
    AIConfigurationError,
    AIServiceUnavailable,
    AIRateLimitExceeded,
    AITimeoutError,
    AIInvalidResponse,
    AIValidationError,
)
# pyrefly: ignore [missing-import]
from google.genai.errors import APIError

@override_settings(AI_API_KEY="test_key", AI_MODEL="gemini-1.5-pro")
class AIServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="test@example.com", password="password")

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_configuration(self):
        with override_settings(AI_API_KEY=None, AI_MODEL=None):
            with self.assertRaises(AIConfigurationError):
                GeminiService()

    @patch('apps.ai_assistant.services.ai_service.genai.Client')
    def test_generate_response_success(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.text = "Hello world"
        mock_client.models.generate_content.return_value = mock_response

        service = GeminiService()
        response = service.generate_response("Say hello")
        self.assertEqual(response.text, "Hello world")
        mock_client.models.generate_content.assert_called_once()

    @patch('apps.ai_assistant.services.ai_service.genai.Client')
    def test_rate_limit_error(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Create a mock error that has a 'code' attribute, because APIError might require specific args
        class MockAPIError(APIError):
            def __init__(self):
                self.message = "Rate limit exceeded"
                self.code = 429
            def __str__(self):
                return self.message

        mock_client.models.generate_content.side_effect = MockAPIError()
        
        service = GeminiService()
        with self.assertRaises(AIRateLimitExceeded):
            service.generate_response("Test")

    @patch('apps.ai_assistant.services.ai_service.genai.Client')
    def test_generate_quiz_success(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        
        # Simulate successful JSON structured response
        valid_json = json.dumps({
            "title": "Test Quiz",
            "description": "A test quiz",
            "questions": [
                {
                    "question_text": "What is 2+2?",
                    "option_a": "3",
                    "option_b": "4",
                    "option_c": "5",
                    "option_d": "6",
                    "correct_option": "B",
                    "explanation": "Math",
                    "marks": 1
                }
            ]
        })
        mock_response.text = valid_json
        mock_response.usage_metadata = MagicMock(prompt_token_count=10, candidates_token_count=20)
        mock_client.models.generate_content.return_value = mock_response

        service = GeminiService()
        data, usage = service.generate_quiz("Math")
        
        self.assertEqual(data.title, "Test Quiz")
        self.assertEqual(len(data.questions), 1)
        self.assertEqual(data.questions[0].correct_option, "B")

    @patch('apps.ai_assistant.services.ai_service.genai.Client')
    def test_generate_quiz_validation_error(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        
        # Simulate invalid JSON structure (missing required field)
        invalid_json = json.dumps({
            "title": "Test Quiz",
            # missing description
            "questions": []
        })
        mock_response.text = invalid_json
        mock_client.models.generate_content.return_value = mock_response

        service = GeminiService()
        with self.assertRaises(AIValidationError):
            service.generate_quiz("Math")

    def test_database_models(self):
        conv = AIConversation.objects.create(user=self.user, title="Math Help")
        AIMessage.objects.create(conversation=conv, role='USER', content="Help me with math")
        AIMessage.objects.create(conversation=conv, role='MODEL', content="Sure", prompt_tokens=5, completion_tokens=5)
        
        interaction = AIInteraction.objects.create(
            user=self.user,
            operation="generate_quiz",
            model_name="gemini-1.5-pro",
            status="SUCCESS",
            metadata={"topic": "Algebra"}
        )
        
        self.assertEqual(conv.messages.count(), 2)
        self.assertEqual(interaction.operation, "generate_quiz")


class AIChatAPIEndpointTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(email="student@test.com", password="password", role="STUDENT")
        self.teacher = User.objects.create_user(email="teacher@test.com", password="password", role="TEACHER")
        self.client.login(email="student@test.com", password="password")

    def test_unauthorized_access(self):
        self.client.logout()
        # Anonymous
        response = self.client.post('/ai/api/chat/', json.dumps({"message": "hi"}), content_type="application/json")
        self.assertEqual(response.status_code, 401)
        
        # Logged in but not STUDENT
        self.client.login(email="teacher@test.com", password="password")
        response = self.client.post('/ai/api/chat/', json.dumps({"message": "hi"}), content_type="application/json")
        self.assertEqual(response.status_code, 403)

    @patch('apps.ai_assistant.views.GeminiService')
    def test_chat_new_conversation(self, MockGeminiService):
        mock_service = MockGeminiService.return_value
        mock_service.model_name = "gemini-1.5-pro"
        mock_response = MagicMock()
        mock_response.text = "Hello Student"
        mock_response.usage_metadata.prompt_token_count = 10
        mock_response.usage_metadata.candidates_token_count = 20
        mock_service.generate_response.return_value = mock_response
        
        response = self.client.post('/ai/api/chat/', json.dumps({"message": "Help me"}), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Check DB
        conv = AIConversation.objects.last()
        self.assertEqual(conv.user, self.student)
        self.assertEqual(conv.title, "Help me")
        self.assertEqual(conv.messages.count(), 2)

    @patch('apps.ai_assistant.views.GeminiService')
    def test_chat_existing_conversation(self, MockGeminiService):
        mock_service = MockGeminiService.return_value
        mock_service.model_name = "gemini-1.5-pro"
        mock_response = MagicMock()
        mock_response.text = "Hello Again"
        mock_response.usage_metadata = MagicMock()
        mock_response.usage_metadata.prompt_token_count = 10
        mock_response.usage_metadata.candidates_token_count = 20
        mock_service.generate_response.return_value = mock_response
        
        conv = AIConversation.objects.create(user=self.student, title="Old")
        
        response = self.client.post('/ai/api/chat/', json.dumps({
            "message": "Continue", "conversation_id": conv.id
        }), content_type="application/json")
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(conv.messages.count(), 2)

    def test_cross_tenant_conversation_access(self):
        other_student = User.objects.create_user(email="other@test.com", password="password", role="STUDENT")
        conv = AIConversation.objects.create(user=other_student, title="Private")
        
        response = self.client.post('/ai/api/chat/', json.dumps({
            "message": "Snoop", "conversation_id": conv.id
        }), content_type="application/json")
        
        self.assertEqual(response.status_code, 404)

    def test_archive_conversation(self):
        conv = AIConversation.objects.create(user=self.student, title="To Archive")
        response = self.client.post('/ai/api/chat/archive/', json.dumps({"conversation_id": conv.id}), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        conv.refresh_from_db()
        self.assertTrue(conv.is_archived)
