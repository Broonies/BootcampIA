# backend/app/llm.py
from typing import List, Dict
import os
import requests
from dotenv import load_dotenv

load_dotenv()

class EpitechLLMService:
    def __init__(self):
        self.api_url = os.getenv("EPITECH_API_URL", "https://api.ia.epitech.bzh")
        self.model = os.getenv("EPITECH_MODEL", "qwen3:30b")
        self.api_key = os.getenv("EPITECH_API_KEY")

    def _headers(self):
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def chat(
        self,
        message: str,
        context: str = "",
        history: List[Dict[str, str]] | None = None
    ) -> str:

        if history is None:
            history = []

        messages = []

        if context:
            messages.append({
                "role": "system",
                "content": context
            })

        for msg in history:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })

        messages.append({
            "role": "user",
            "content": message
        })

        response = requests.post(
            f"{self.api_url}/api/chat",
            headers=self._headers(),
            json={
                "model": self.model,
                "messages": messages,
                "stream": False
            },
            timeout=120
        )

        response.raise_for_status()
        data = response.json()

        # ⚠️ IMPORTANT : on renvoie TOUJOURS une string
        return str(data["message"]["content"])
