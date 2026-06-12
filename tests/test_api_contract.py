import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_recommendations_endpoint_matches_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_search_candidates(criteria: dict, limit: int | None = None) -> list[dict]:
        assert criteria["category"] == "fashion"
        assert criteria["platforms"] == ["tiktok"]
        assert criteria["minFollowers"] == 100000
        assert criteria["maxBudget"] == 10000000
        assert limit == 2
        return [
            {
                "kolId": 12,
                "slug": "nguyen-a",
                "displayName": "Nguyen A",
                "avatarUrl": "https://example.com/avatar.jpg",
                "categories": ["fashion", "beauty"],
                "platforms": [{"platform": "tiktok", "followers": 230000, "engagementRate": 0.047}],
                "priceFrom": 8000000,
                "averageRating": 4.8,
                "completedBookingCount": 21,
            },
            {
                "kolId": 13,
                "slug": "nguyen-b",
                "displayName": "Nguyen B",
                "categories": ["fashion"],
                "platforms": [{"platform": "instagram", "followers": 150000, "engagementRate": 0.03}],
                "priceFrom": 9000000,
                "averageRating": 4.5,
                "completedBookingCount": 10,
            },
        ]

    monkeypatch.setattr(
        "app.api.routes.recommendations.kol_retrieval_service.search_candidates",
        fake_search_candidates,
    )

    response = client.post(
        "/api/v1/recommendations",
        json={
            "brandId": 1,
            "criteria": {
                "category": "fashion",
                "platforms": ["tiktok"],
                "minFollowers": 100000,
                "maxBudget": 10000000,
            },
            "topK": 2,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["criteria"]["category"] == "fashion"
    assert payload["criteria"]["platforms"] == ["tiktok"]
    assert payload["recommendations"][0]["kolId"] == 12
    assert payload["recommendations"][0]["slug"] == "nguyen-a"
    assert payload["recommendations"][0]["matchScore"] > 0
    assert payload["recommendations"][0]["reason"]


def test_invalid_request_uses_standard_error_contract() -> None:
    response = client.post(
        "/api/v1/recommendations",
        json={
            "criteria": {
                "category": "fashion",
            },
            "topK": 5,
        },
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["error"]["code"] == "INVALID_REQUEST"
    assert payload["error"]["message"] == "Invalid request"
    assert isinstance(payload["error"]["details"], list)
