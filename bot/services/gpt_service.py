import os
from openai import OpenAI

class GPTService:
    """
    Обёртка над OpenAI API.
    """

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-5")

    def generate(self, prompt: str) -> str:
        """
        Отправляет запрос к ChatGPT и возвращает готовый текст.
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
        )

        return response.choices[0].message["content"]
