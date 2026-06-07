from pydantic import BaseModel, Field


class KolSearchCriteria(BaseModel):
    category: str | None = None
    platforms: list[str] = Field(default_factory=list)
    minFollowers: int | None = None
    maxFollowers: int | None = None
    minBudget: int | None = None
    maxBudget: int | None = None
    location: str | None = None
    gender: str | None = None
    campaignGoal: str | None = None
    serviceType: str | None = None
