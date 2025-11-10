import requests
from backend.config import settings
from backend.services.settings_service import settings_service
from .base import LLM

class LMStudioProvider(LLM):
    def complete(self, *, system: str, user: str, max_tokens: int) -> str:
        base_url = settings_service.get_lmstudio_url()
        url = f"{base_url}/chat/completions"
        payload = {
            "model": settings.LMSTUDIO_MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": max_tokens,
            "temperature": 0.2,
        }
        r = requests.post(url, json=payload, timeout=120)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
