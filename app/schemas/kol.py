from pydantic import BaseModel, Field


class KolPlatform(BaseModel):
    platform: str
    profileUrl: str | None = None
    followers: int = 0
    engagementRate: float | None = None
    averageViews: int | None = None


class KolProfile(BaseModel):
    kolId: int
    displayName: str
    avatarUrl: str | None = None
    bio: str | None = None
    location: str | None = None
    gender: str | None = None
    categories: list[str] = Field(default_factory=list)
    platforms: list[KolPlatform] = Field(default_factory=list)
    priceFrom: int | None = None
    averageRating: float | None = None
    completedBookingCount: int = 0
    bookingAcceptanceRate: float | None = None
