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
                                "Ты — генератор ЗАВЕРШЁННЫХ астрологических отчётов.\n"
                                "Ты НИКОГДА не задаёшь вопросов и не предлагаешь продолжить.\n"
                                "Ты ВСЕГДА выдаёшь финальный отчёт."
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

        result = self._extract_text(response).strip()

        if not result:
            print("DEBUG RESPONSE:", response)
            raise RuntimeError("OpenAI returned empty output")

        return result

    def _extract_text(self, response) -> str:
        parts: list[str] = []

        for item in response.output:
            content = getattr(item, "content", None)
            if not content:
                continue

            for block in content:
                if getattr(block, "type", None) == "output_text":
                    text = getattr(block, "text", None)
                    if text:
                        parts.append(text)

        return "\n".join(parts)
