import os
from openai import OpenAI


class GPTService:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    def generate(self, prompt: str) -> str:
        response = self.client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        # Универсальный и безопасный способ
        for item in response.output:
            if item["type"] == "message":
                for part in item["content"]:
                    if part["type"] == "output_text":
                        return part["text"]

        raise RuntimeError("No text output from OpenAI")
