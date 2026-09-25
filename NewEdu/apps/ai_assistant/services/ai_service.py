import os
from typing import Optional
from django.conf import settings
from pydantic import ValidationError

# pyrefly: ignore [missing-import]
from google import genai
# pyrefly: ignore [missing-import]
from google.genai import types
# pyrefly: ignore [missing-import]
from google.genai.errors import APIError

from apps.ai_assistant.services.exceptions import (
    AIConfigurationError,
    AIServiceUnavailable,
    AIRateLimitExceeded,
    AITimeoutError,
    AIInvalidResponse,
    AIValidationError,
)
from apps.ai_assistant.services.schemas import (
    GeneratedQuizSchema,
    GeneratedQuestionsSchema,
    GeneratedExplanationSchema,
    GeneratedSummarySchema,
    LearningRecommendationSchema,
    GeneratedContentSchema,
)

class GeminiService:
    def __init__(self):
        # We assume the env vars are available in settings or os.environ
        api_key = os.environ.get('AI_API_KEY') or getattr(settings, 'AI_API_KEY', None)
        model_name = os.environ.get('AI_MODEL') or getattr(settings, 'AI_MODEL', None)

        if not api_key:
            raise AIConfigurationError("AI_API_KEY is missing from environment or settings.")
        if not model_name:
            raise AIConfigurationError("AI_MODEL is missing from environment or settings.")

        self.model_name = model_name
        self.client = genai.Client(api_key=api_key)

    def _handle_api_call(self, call_func, *args, **kwargs):
        """Wrapper to handle Google GenAI exceptions safely."""
        try:
            return call_func(*args, **kwargs)
        except APIError as e:
            # Analyze error code if possible
            error_message = str(e).lower()
            if e.code == 429 or "quota" in error_message or "rate limit" in error_message:
                raise AIRateLimitExceeded("AI Rate Limit Exceeded.") from None
            if e.code == 503 or e.code == 502 or "unavailable" in error_message:
                raise AIServiceUnavailable("AI Service is currently unavailable.") from None
            if e.code == 408 or "timeout" in error_message:
                raise AITimeoutError("AI Service timed out.") from None
            
            # Generic API fallback
            raise AIServiceUnavailable("An unexpected AI service error occurred.") from None
        except Exception as e:
            # Catch non-API specific network errors
            if "timeout" in str(e).lower():
                raise AITimeoutError("AI Service request timed out.") from None
            raise AIServiceUnavailable("Failed to communicate with AI provider.") from None

    def generate_response(self, prompt: str, system_instruction: Optional[str] = None, history: Optional[list] = None) -> types.GenerateContentResponse:
        """
        Generates standard unstructured text response.
        history: list of AIMessage objects
        """
        config = types.GenerateContentConfig(
            temperature=0.7,
            system_instruction=system_instruction
        )
        
        contents = []
        
        # Keep only the last 10 messages (5 turns) to prevent context unbounded growth
        MAX_HISTORY_MESSAGES = getattr(settings, 'AI_MAX_HISTORY_MESSAGES', 10)
        
        if history:
            # Sort history chronologically if not already, then take the last MAX_HISTORY_MESSAGES
            recent_history = history[-MAX_HISTORY_MESSAGES:]
            for msg in recent_history:
                # Map our internal role (USER/MODEL) to google genai role (user/model)
                role = "user" if msg.role == "USER" else "model"
                # SYSTEM roles from db shouldn't be here, but just in case, ignore them
                if msg.role in ['USER', 'MODEL']:
                    contents.append(
                        types.Content(role=role, parts=[types.Part.from_text(text=msg.content)])
                    )
        
        # Add the current prompt
        contents.append(
            types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
        )

        response = self._handle_api_call(
            self.client.models.generate_content,
            model=self.model_name,
            contents=contents,
            config=config,
        )
        if not response or not response.text:
            raise AIInvalidResponse("AI returned an empty or unparseable response.")
        return response

    def _generate_structured(self, prompt: str, schema_class, system_instruction: Optional[str] = None):
        """Generates structured response using pydantic schema validation."""
        config = types.GenerateContentConfig(
            temperature=0.4,
            response_mime_type="application/json",
            response_schema=schema_class,
            system_instruction=system_instruction
        )
        response = self._handle_api_call(
            self.client.models.generate_content,
            model=self.model_name,
            contents=prompt,
            config=config,
        )
        if not response or not response.text:
            raise AIInvalidResponse("AI returned an empty or unparseable structured response.")
        
        try:
            # Parse the JSON back into the pydantic model to guarantee adherence.
            # The google-genai structured output returns a JSON string in response.text
            validated_data = schema_class.model_validate_json(response.text)
            return validated_data, response.usage_metadata
        except ValidationError as e:
            raise AIValidationError("AI output failed schema validation.") from e
        except Exception as e:
            raise AIInvalidResponse("Failed to parse JSON response from AI.") from e

    def generate_quiz(self, topic: str, num_questions: int = 5):
        prompt = f"Generate a multiple-choice quiz about {topic} with {num_questions} questions."
        system = "You are an expert educator. Create accurate, age-appropriate quizzes."
        return self._generate_structured(prompt, GeneratedQuizSchema, system_instruction=system)

    def generate_questions(self, context: str):
        prompt = f"Based on the following context, generate 5 standalone multiple-choice questions:\n\n{context}"
        system = "You are an expert instructional designer."
        return self._generate_structured(prompt, GeneratedQuestionsSchema, system_instruction=system)

    def generate_explanation(self, topic: str, context: Optional[str] = None):
        prompt = f"Explain the topic: {topic}."
        if context:
            prompt += f"\nContext:\n{context}"
        system = "You are an expert tutor. Explain concepts clearly and concisely."
        return self._generate_structured(prompt, GeneratedExplanationSchema, system_instruction=system)

    def generate_summary(self, text: str):
        prompt = f"Summarize the following educational text:\n\n{text}"
        system = "You are an expert summarizer."
        return self._generate_structured(prompt, GeneratedSummarySchema, system_instruction=system)

    def generate_learning_recommendation(self, performance_data: str):
        prompt = f"Analyze the following student performance data and provide actionable recommendations:\n\n{performance_data}"
        system = "You are an educational advisor. Provide constructive, encouraging, and specific advice."
        return self._generate_structured(prompt, LearningRecommendationSchema, system_instruction=system)
        
    def generate_student_recommendation(self, context_data: dict):
        prompt = (
            f"Analyze the following student performance data and provide actionable, personalized learning recommendations.\n\n"
            f"Context Data:\n{context_data}\n\n"
            f"Please identify strengths, weaknesses, and provide specific actionable advice. Ensure recommended_topics are exactly "
            f"as named in the provided context data. Do not invent any performance metrics or topics."
        )
        system = "You are an expert personalized learning advisor. Your recommendations must be firmly grounded only in the provided data."
        return self._generate_structured(prompt, LearningRecommendationSchema, system_instruction=system)

    def generate_teacher_content(self, class_name: str, subject_name: str, chapter_name: str, topic: str, difficulty: str, content_type: str):
        prompt = (
            f"Generate educational content for a teacher to use in class.\n"
            f"Class: {class_name}\n"
            f"Subject: {subject_name}\n"
            f"Chapter: {chapter_name}\n"
            f"Topic: {topic}\n"
            f"Difficulty: {difficulty}\n"
            f"Content Type: {content_type}\n\n"
            f"Please generate the requested {content_type} in a clear, highly educational manner using Markdown formatting."
        )
        system = "You are an expert educator and instructional designer helping a teacher prepare high-quality class materials."
        return self._generate_structured(prompt, GeneratedContentSchema, system_instruction=system)

    def generate_teacher_quiz(self, class_name: str, subject_name: str, chapter_name: str, difficulty: str, question_count: int, question_type: str):
        prompt = (
            f"Generate a quiz for a teacher to assign to students.\n"
            f"Class: {class_name}\n"
            f"Subject: {subject_name}\n"
            f"Chapter: {chapter_name}\n"
            f"Difficulty: {difficulty}\n"
            f"Question Count: {question_count}\n"
            f"Question Type: {question_type}\n\n"
            f"Please generate exactly {question_count} {question_type} questions."
        )
        system = "You are an expert educator. Create accurate, age-appropriate quizzes that test comprehension and critical thinking."
        return self._generate_structured(prompt, GeneratedQuizSchema, system_instruction=system)
