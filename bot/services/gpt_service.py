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
                                "- НЕ задавай вопросов\n"
                                "- НЕ проси подтверждений\n"
                                "- НЕ предлагай продолжить диалог\n"
                                "- НЕ упоминай дополнительные услуги\n"
                                "- НЕ используй фразы: "
                                "'если хотите', 'могу', 'предлагаю', "
                                "'скажите', 'подтвердите', 'выберите'\n\n"
                                "ФОРМАТ:\n"
                                "- Финальный готовый отчёт\n"
                                "- Утверждения и рекомендации\n"
                                "- Никакого диалога\n"
                                "- Без обращений к читателю\n"
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

        result = (response.output_text or "").strip()

        if not result:
            print("EMPTY GPT OUTPUT")
            print(response)
            raise RuntimeError("OpenAI returned empty output")

        return result
