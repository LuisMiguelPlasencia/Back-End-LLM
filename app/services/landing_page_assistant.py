from app.prompting_templates.landing.landing_assistant_prompt import LANDING_ASSISTANT_SYSTEM_PROMPT
from app.utils.openai_client import get_openai_client

class LandingPageAssistant:

    def __init__(self, api_key: str | None = None):
        self.client = get_openai_client(api_key)
            
    def answer_user_question(self, user_question: str) -> str:
        response = self.client.responses.create(
            model="gpt-4.1-mini",  # rápido y económico para landing
            input=[
                {
                    "role": "system",
                    "content": LANDING_ASSISTANT_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": user_question
                }
            ],
            max_output_tokens=300,
            temperature=0.4  # respuestas controladas y profesionales
        )
        return response.output_text
    
if __name__ == "__main__":
    assistant = LandingPageAssistant()
    question = "¿Qué diferencia hay entre conversa y una plataforma normal de cursos?"
    answer = assistant.answer_user_question(question)
    print("Pregunta:", question)
    print("Respuesta:", answer)