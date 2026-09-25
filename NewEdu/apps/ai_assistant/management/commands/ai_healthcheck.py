from django.core.management.base import BaseCommand
from apps.ai_assistant.services.ai_service import GeminiService
from apps.ai_assistant.services.exceptions import AIError

class Command(BaseCommand):
    help = 'Performs a real API call to verify Google GenAI SDK configuration.'

    def handle(self, *args, **options):
        self.stdout.write("Initializing GeminiService...")
        try:
            service = GeminiService()
            self.stdout.write(self.style.SUCCESS(f"Configuration loaded. Model: {service.model_name}"))
            
            self.stdout.write("Sending test request to Gemini API...")
            response = service.generate_response("Reply with a single word: OK")
            
            self.stdout.write(self.style.SUCCESS(f"API Connection Successful! Response: {response.text.strip()}"))
        except AIError as e:
            self.stderr.write(self.style.ERROR(f"AI Error: {str(e)}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Unexpected Error: {str(e)}"))
