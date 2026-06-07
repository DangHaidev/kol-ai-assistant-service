from typing import Any, TypedDict

from app.schemas.criteria import KolSearchCriteria
from app.schemas.recommendation import RecommendationItem


class KolChatState(TypedDict, total=False):
    brandId: int
    conversationId: str | None
    userMessage: str
    history: list[dict[str, Any]]
    intent: str | None
    oldCriteria: KolSearchCriteria
    extractedCriteria: KolSearchCriteria
    mergedCriteria: KolSearchCriteria
    needClarification: bool
    clarificationQuestions: list[str]
    candidates: list[dict[str, Any]]
    recommendations: list[RecommendationItem]
    reply: str | None
