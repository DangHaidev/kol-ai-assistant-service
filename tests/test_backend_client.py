import pytest

from app.clients.kol_backend_client import KolBackendClient


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


class FakeAsyncClient:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url: str, json: dict, headers: dict) -> FakeResponse:
        assert url.endswith("/api/internal/kols/search-candidates")
        assert json["limit"] == 5
        assert headers["X-Internal-Token"] == "secret"
        return FakeResponse(self.payload)


@pytest.mark.asyncio
async def test_backend_client_accepts_wrapped_success_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "success": True,
        "data": {
            "items": [
                {
                    "kolId": 12,
                    "displayName": "Nguyen A",
                    "categories": ["Fashion", "Beauty"],
                    "platforms": [{"platform": "TIKTOK", "followers": 230000}],
                    "gender": "FEMALE",
                }
            ]
        },
    }
    monkeypatch.setattr(
        "app.clients.kol_backend_client.httpx.AsyncClient",
        lambda timeout: FakeAsyncClient(payload),
    )
    client = KolBackendClient("http://localhost:8080", 10, internal_token="secret")

    items = await client.search_candidates({"category": "fashion"}, limit=5)

    assert items[0]["categories"] == ["fashion", "beauty"]
    assert items[0]["platforms"][0]["platform"] == "tiktok"
    assert items[0]["gender"] == "female"


@pytest.mark.asyncio
async def test_backend_client_falls_back_to_mock_when_request_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    class BrokenAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url: str, json: dict, headers: dict):
            raise ValueError("bad payload")

    monkeypatch.setattr(
        "app.clients.kol_backend_client.httpx.AsyncClient",
        lambda timeout: BrokenAsyncClient(),
    )
    client = KolBackendClient("http://localhost:8080", 10, internal_token="secret", max_retries=0)

    items = await client.search_candidates({"category": "fashion"}, limit=2)

    assert len(items) == 2
    assert items[0]["kolId"] == 1
