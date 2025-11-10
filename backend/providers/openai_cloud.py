import os
from openai import OpenAI
from backend.config import settings
from backend.services.settings_service import settings_service
from .base import LLM

class OpenAIProvider(LLM):
    def __init__(self):
        api_key = settings_service.get_openai_api_key()
        self.client = OpenAI(api_key=api_key)
    
    def complete(self, *, system: str, user: str, max_tokens: int) -> str:
        response = self.client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=max_tokens,
            temperature=0.2,
        )
        content = response.choices[0].message.content or ""
        return content.strip()
