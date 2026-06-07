from pydantic import BaseModel, Field

from app.schemas.criteria import KolSearchCriteria
from app.schemas.recommendation import RecommendationItem


class ChatRequest(BaseModel):
    brandId: int
    conversationId: str | None = None
    message: str


class ChatResponse(BaseModel):
    conversationId: str
    reply: str
    intent: str
    criteria: KolSearchCriteria
    recommendations: list[RecommendationItem] = Field(default_factory=list)
    needClarification: bool = False
    clarificationQuestions: list[str] = Field(default_factory=list)
