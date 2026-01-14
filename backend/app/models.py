"""Modèles Pydantic pour la validation des requêtes/réponses API."""
from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    """Modèle de requête pour le point d'accès chat."""
    message: str
    history: list = Field(default_factory=list)
    latitude: Optional[float] = Field(default=None, description="Position GPS - latitude")
    longitude: Optional[float] = Field(default=None, description="Position GPS - longitude")
