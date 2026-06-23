import pytest

from app.clients import llm_client as llm_client_module
from app.clients.llm_client import GeminiLlmClient, OpenAILlmClient, build_llm_client


class StubOpenAILlmClient(OpenAILlmClient):
    def __init__(self, responses: list[str], repaired: dict | None = None) -> None:
        self.model = "stub"
        self.max_retries = 1
        self.client = None
        self._responses = responses
        self._repaired = repaired

    async def generate_text(self, prompt: str) -> str:
        return self._responses.pop(0)

    async def _repair_invalid_json(self, raw_text: str) -> dict | None:
        return self._repaired


@pytest.mark.asyncio
async def test_generate_json_extracts_json_from_markdown_block() -> None:
    client = StubOpenAILlmClient(['```json\n{"intent":"recommend_kol"}\n```'])

    payload = await client.generate_json("ignored")

    assert payload == {"intent": "recommend_kol"}


@pytest.mark.asyncio
async def test_generate_json_uses_repair_when_initial_payload_is_invalid() -> None:
    client = StubOpenAILlmClient(["intent=recommend_kol"], repaired={"intent": "recommend_kol"})

    payload = await client.generate_json("ignored")

    assert payload == {"intent": "recommend_kol"}


class StubGeminiResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {"candidates": [{"content": {"parts": [{"text": '{"intent":"recommend_kol"}'}]}}]}


class StubGeminiHttpClient:
    def __init__(self) -> None:
        self.request: dict | None = None

    async def post(self, url: str, **kwargs: object) -> StubGeminiResponse:
        self.request = {"url": url, **kwargs}
        return StubGeminiResponse()


@pytest.mark.asyncio
async def test_gemini_client_requests_structured_json() -> None:
    http_client = StubGeminiHttpClient()
    client = GeminiLlmClient(
        api_key="gemini-key",
        model="gemini-3.1-flash-lite",
        max_retries=0,
        timeout_seconds=15,
        http_client=http_client,  # type: ignore[arg-type]
    )

    payload = await client.generate_json("extract intent")

    assert payload == {"intent": "recommend_kol"}
    assert http_client.request == {
        "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent",
        "headers": {"x-goog-api-key": "gemini-key"},
        "json": {
            "contents": [{"role": "user", "parts": [{"text": "extract intent"}]}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
        },
    }


def test_build_llm_client_selects_gemini(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(llm_client_module.settings, "llm_provider", "gemini")
    monkeypatch.setattr(llm_client_module.settings, "gemini_api_key", "gemini-key")

    client = build_llm_client()

    assert isinstance(client, GeminiLlmClient)
    assert client.model == "gemini-3.1-flash-lite"
