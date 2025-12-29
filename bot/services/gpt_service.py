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
                            "type": "input_text",
                            "text": (
                                "Ты — генератор ЗАВЕРШЁННЫХ астрологических отчётов.\n\n"
                                "СТРОГИЕ ПРАВИЛА:\n"
                                "- НИКОГДА не задавай вопросы\n"
                                "- НИКОГДА не проси подтвердить данные\n"
                                "- НИКОГДА не предлагай продолжить диалог\n"
                                "- НИКОГДА не упоминай дополнительные услуги\n"
                                "- НЕ используй фразы: "
                                "'если хотите', 'могу', 'предлагаю', "
                                "'скажите', 'подтвердите', 'выберите'\n\n"
                                "ФОРМАТ:\n"
                                "- Готовый финальный отчёт\n"
                                "- Утверждения и рекомендации\n"
                                "- Никакого диалога\n"
                                "- Без обращений к читателю"
                            ),
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": prompt,
                        }
                    ],
                },
            ],
        )

        return response.output_text
