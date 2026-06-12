import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.repositories.conversation_repository import InMemoryConversationRepository


client = TestClient(app)


@pytest.fixture(autouse=True)
def isolate_external_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.services.intent_service.llm_client", None)
    monkeypatch.setattr("app.services.criteria_service.llm_client", None)
    monkeypatch.setattr(
        "app.graph.nodes.conversation_service.repository",
        InMemoryConversationRepository(),
    )


def test_chat_endpoint_returns_mock_recommendations(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_search_candidates(criteria: dict, limit: int | None = None) -> list[dict]:
        assert criteria["category"] == "fashion"
        assert criteria["platforms"] == ["tiktok"]
        assert criteria["minFollowers"] == 100000
        assert criteria["maxBudget"] == 10000000
        assert limit is None
        return [
            {
                "kolId": 12,
                "slug": "nguyen-a",
                "displayName": "Nguyen A",
                "avatarUrl": "https://example.com/avatar.jpg",
                "categories": ["fashion", "beauty"],
                "platforms": [
                    {
                        "platform": "tiktok",
                        "profileUrl": "https://tiktok.com/@nguyena",
                        "followers": 230000,
                        "engagementRate": 0.047,
                        "averageViews": 50000,
                    }
                ],
                "priceFrom": 8000000,
                "averageRating": 4.8,
                "completedBookingCount": 21,
            }
        ]

    monkeypatch.setattr(
        "app.graph.nodes.kol_retrieval_service.search_candidates",
        fake_search_candidates,
    )

    response = client.post(
        "/api/v1/chat",
        json={
            "brandId": 1,
            "conversationId": None,
            "message": "Tôi muốn tìm KOL thời trang follower trên 100k, ưu tiên TikTok, ngân sách dưới 10 triệu",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["intent"] == "recommend_kol"
    assert payload["needClarification"] is False
    assert payload["criteria"]["category"] == "fashion"
    assert payload["recommendations"]


def test_chat_endpoint_asks_for_clarification_when_platform_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fail_if_called(criteria: dict, limit: int | None = None) -> list[dict]:
        raise AssertionError("candidate search should not run while clarification is required")

    monkeypatch.setattr(
        "app.graph.nodes.kol_retrieval_service.search_candidates",
        fail_if_called,
    )

    response = client.post(
        "/api/v1/chat",
        json={
            "brandId": 1,
            "conversationId": None,
            "message": "Toi muon tim KOL thoi trang follower tren 100k",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["intent"] == "recommend_kol"
    assert payload["needClarification"] is True
    assert payload["criteria"]["category"] == "fashion"
    assert payload["criteria"]["minFollowers"] == 100000
    assert payload["recommendations"] == []
    assert payload["clarificationQuestions"]
