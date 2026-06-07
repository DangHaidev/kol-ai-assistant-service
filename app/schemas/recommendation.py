from pydantic import BaseModel, Field

from app.schemas.criteria import KolSearchCriteria
from app.schemas.kol import KolPlatform


class RecommendationItem(BaseModel):
    kolId: int
    displayName: str
    avatarUrl: str | None = None
    categories: list[str] = Field(default_factory=list)
    platforms: list[KolPlatform] = Field(default_factory=list)
    priceFrom: int | None = None
    rating: float | None = None
    completedBookingCount: int = 0
    matchScore: int
    reason: str


class RecommendationRequest(BaseModel):
    brandId: int
    criteria: KolSearchCriteria
    topK: int = 5


class RecommendationResponse(BaseModel):
    criteria: KolSearchCriteria
    recommendations: list[RecommendationItem] = Field(default_factory=list)
