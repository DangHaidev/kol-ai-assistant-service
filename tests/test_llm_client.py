import pytest

from app.clients.llm_client import OpenAILlmClient


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
