from __future__ import annotations

import httpx

from app.core.config import settings


class KolBackendClient:
    def __init__(
        self,
        base_url: str,
        timeout_seconds: int,
        internal_token: str | None = None,
        max_retries: int = 2,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.internal_token = internal_token
        self.max_retries = max_retries

    async def search_candidates(self, criteria: dict, limit: int = 50) -> list[dict]:
        if self.internal_token:
            payload = {**criteria, "limit": limit}
            headers = {"X-Internal-Token": self.internal_token}
            for _ in range(self.max_retries + 1):
                try:
                    async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                        response = await client.post(
                            f"{self.base_url}/api/internal/kols/search-candidates",
                            json=payload,
                            headers=headers,
                        )
                        response.raise_for_status()
                        return self._extract_items(response.json())
                except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError, ValueError):
                    continue
        return self._mock_candidates(limit)

    def _extract_items(self, payload: dict) -> list[dict]:
        items = payload.get("items")
        if items is None and payload.get("success") is True:
            data = payload.get("data") or {}
            items = data.get("items") or data.get("content") or []

        if not isinstance(items, list):
            raise ValueError("Backend payload does not contain a valid items list.")

        return [self._normalize_candidate(item) for item in items if isinstance(item, dict)]

    def _normalize_candidate(self, candidate: dict) -> dict:
        normalized = dict(candidate)
        normalized["categories"] = [
            str(category).strip().lower()
            for category in candidate.get("categories", [])
            if category
        ]
        normalized["platforms"] = [
            {
                **platform,
                "platform": str(platform.get("platform", "")).strip().lower(),
            }
            for platform in candidate.get("platforms", [])
            if isinstance(platform, dict)
        ]
        normalized["gender"] = str(candidate["gender"]).strip().lower() if candidate.get("gender") else None
        return normalized

    def _mock_candidates(self, limit: int) -> list[dict]:
        candidates = [
            {
                "kolId": 1,
                "displayName": "Demo Fashion KOL",
                "avatarUrl": "https://example.com/avatar-1.jpg",
                "categories": ["fashion", "beauty"],
                "platforms": [
                    {
                        "platform": "tiktok",
                        "profileUrl": "https://tiktok.com/@demo-fashion",
                        "followers": 150000,
                        "engagementRate": 0.04,
                        "averageViews": 50000,
                    }
                ],
                "priceFrom": 7000000,
                "averageRating": 4.7,
                "completedBookingCount": 12,
                "bookingAcceptanceRate": 0.85,
            },
            {
                "kolId": 2,
                "displayName": "Lifestyle Creator B",
                "avatarUrl": "https://example.com/avatar-2.jpg",
                "categories": ["lifestyle", "fashion"],
                "platforms": [
                    {
                        "platform": "instagram",
                        "profileUrl": "https://instagram.com/lifestyle-b",
                        "followers": 220000,
                        "engagementRate": 0.032,
                        "averageViews": 32000,
                    }
                ],
                "priceFrom": 9000000,
                "averageRating": 4.6,
                "completedBookingCount": 18,
                "bookingAcceptanceRate": 0.81,
            },
            {
                "kolId": 3,
                "displayName": "Tech Reviewer C",
                "avatarUrl": "https://example.com/avatar-3.jpg",
                "categories": ["technology"],
                "platforms": [
                    {
                        "platform": "youtube",
                        "profileUrl": "https://youtube.com/@tech-c",
                        "followers": 450000,
                        "engagementRate": 0.055,
                        "averageViews": 90000,
                    }
                ],
                "priceFrom": 15000000,
                "averageRating": 4.9,
                "completedBookingCount": 25,
                "bookingAcceptanceRate": 0.92,
            },
        ]
        return candidates[:limit]


kol_backend_client = KolBackendClient(
    base_url=settings.spring_backend_base_url,
    timeout_seconds=settings.request_timeout_seconds,
    internal_token=settings.spring_backend_internal_token,
    max_retries=settings.backend_request_retries,
)
