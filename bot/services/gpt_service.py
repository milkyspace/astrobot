import os
from openai import OpenAI


class GPTService:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        self.model = os.getenv("OPENAI_MODEL", "gpt-5")

    def generate(self, prompt: str) -> str:
        response = self.client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Ты — генератор ЗАВЕРШЁННЫХ астрологических отчётов.\n"
                                "Ты НИКОГДА:\n"
                                "- не задаёшь вопросы\n"
                                "- не просишь подтвердить данные\n"
                                "- не предлагаешь дополнительные услуги\n"
                                "- не продолжаешь диалог\n\n"
                                "Ты ВСЕГДА:\n"
                                "- выдаёшь финальный отчёт\n"
                                "- заканчиваешь текст утверждениями и рекомендациями\n"
                                "- не используешь формулировки: "
                                "'если хотите', 'могу', 'предлагаю', 'скажите', "
                                "'подтвердите', 'выберите'\n\n"
                                "Формат ответа: ГОТОВЫЙ ОТЧЁТ. НЕ ДИАЛОГ."
                            )
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
        )

        return response.output_text