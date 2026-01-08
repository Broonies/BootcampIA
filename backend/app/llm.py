# backend/app/llm.py
from dotenv import load_dotenv
import os

load_dotenv()

class EpitechLLMService:
    def __init__(self):
        self.api_url = os.getenv("EPITECH_API_URL", "https://api.ia.epitech.bzh")
        self.model = os.getenv("EPITECH_MODEL", "qwen3:30b")
        self.api_key = os.getenv("EPITECH_API_KEY", None)
    
    def _get_headers(self):
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    def chat(self, message: str, context: str = "", history: List[Dict] = []):
        # ... même code mais avec headers
        response = requests.post(
            f"{self.api_url}/v1/chat/completions",
            headers=self._get_headers(),
            json={...}
        )