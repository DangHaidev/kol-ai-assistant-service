from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_chat_endpoint_returns_mock_recommendations() -> None:
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
