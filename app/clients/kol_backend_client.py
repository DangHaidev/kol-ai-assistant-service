from __future__ import annotations

import json
from logging import getLogger
from pathlib import Path

import httpx

from app.core.config import settings


logger = getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MOCK_DATA_PATH = PROJECT_ROOT / "mock_data" / "backend_search_candidates.json"


class KolBackendClient:
    def __init__(
        self,
        base_url: str,
        timeout_seconds: int,
        internal_token: str | None = None,
        mock_data_path: str | None = None,
        max_retries: int = 2,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.internal_token = internal_token
        self.mock_data_path = mock_data_path
        self.max_retries = max_retries

    async def search_candidates(self, criteria: dict, limit: int = 50) -> list[dict]:
        last_error: Exception | None = None
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
                except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError, ValueError) as exc:
                    last_error = exc
                    continue
        if last_error is not None:
            logger.warning("kol_backend_client.mock_fallback reason=%s", last_error.__class__.__name__)
        elif not self.internal_token:
            logger.info("kol_backend_client.mock_fallback reason=missing_internal_token")
        return self._mock_candidates(criteria, limit)

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

    def _mock_candidates(self, criteria: dict, limit: int) -> list[dict]:
        candidates = self._load_mock_candidates_from_file()
        if candidates:
            filtered = [candidate for candidate in candidates if self._matches_criteria(candidate, criteria)]
            return filtered[:limit]

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
                "categories": ["tech"],
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
        filtered = [candidate for candidate in candidates if self._matches_criteria(candidate, criteria)]
        return filtered[:limit]

    def _load_mock_candidates_from_file(self) -> list[dict]:
        path = self._resolve_mock_data_path()
        if not path.exists():
            logger.warning("kol_backend_client.mock_file_missing path=%s", path)
            return []

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("kol_backend_client.mock_file_invalid path=%s reason=%s", path, exc.__class__.__name__)
            return []

        if isinstance(payload, dict):
            return self._extract_items(payload)
        if isinstance(payload, list):
            return [self._normalize_candidate(item) for item in payload if isinstance(item, dict)]

        logger.warning("kol_backend_client.mock_file_invalid path=%s reason=unexpected_payload", path)
        return []

    def _resolve_mock_data_path(self) -> Path:
        if not self.mock_data_path:
            return DEFAULT_MOCK_DATA_PATH

        path = Path(self.mock_data_path)
        if path.is_absolute():
            return path
        return PROJECT_ROOT / path

    def _matches_criteria(self, candidate: dict, criteria: dict) -> bool:
        category = str(criteria.get("category", "")).strip().lower()
        if category:
            categories = {str(item).strip().lower() for item in candidate.get("categories", []) if item}
            if category not in categories:
                return False

        requested_platforms = {
            str(item).strip().lower()
            for item in criteria.get("platforms", [])
            if item
        }
        if requested_platforms:
            candidate_platforms = {
                str(platform.get("platform", "")).strip().lower()
                for platform in candidate.get("platforms", [])
                if isinstance(platform, dict)
            }
            if not requested_platforms.intersection(candidate_platforms):
                return False

        if criteria.get("gender"):
            candidate_gender = str(candidate.get("gender", "")).strip().lower()
            if candidate_gender != str(criteria["gender"]).strip().lower():
                return False

        if criteria.get("location"):
            candidate_location = str(candidate.get("location", "")).strip().lower()
            if str(criteria["location"]).strip().lower() not in candidate_location:
                return False

        price = candidate.get("priceFrom")
        min_budget = criteria.get("minBudget")
        max_budget = criteria.get("maxBudget")
        if min_budget is not None and price is not None and price < min_budget:
            return False
        if max_budget is not None and price is not None and price > max_budget:
            return False

        min_followers = criteria.get("minFollowers")
        max_followers = criteria.get("maxFollowers")
        if min_followers is not None or max_followers is not None:
            platforms = [platform for platform in candidate.get("platforms", []) if isinstance(platform, dict)]
            if not platforms:
                return False

            def in_range(platform: dict) -> bool:
                followers = platform.get("followers")
                if followers is None:
                    return False
                if min_followers is not None and followers < min_followers:
                    return False
                if max_followers is not None and followers > max_followers:
                    return False
                return True

            if not any(in_range(platform) for platform in platforms):
                return False

        return True


kol_backend_client = KolBackendClient(
    base_url=settings.spring_backend_base_url,
    timeout_seconds=settings.request_timeout_seconds,
    internal_token=settings.spring_backend_internal_token,
    mock_data_path=settings.backend_mock_candidates_path,
    max_retries=settings.backend_request_retries,
)
