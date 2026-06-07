from __future__ import annotations

import asyncio

from openai import APIConnectionError, APITimeoutError, RateLimitError
from openai import AsyncOpenAI

from app.core.config import settings
from app.utils.json_utils import safe_json_loads


class LlmClient:
    async def generate_json(self, prompt: str) -> dict:
        raise NotImplementedError

    async def generate_text(self, prompt: str) -> str:
        raise NotImplementedError


class OpenAILlmClient(LlmClient):
    def __init__(self, api_key: str, model: str, max_retries: int, base_url: str | None = None) -> None:
        self.model = model
        self.max_retries = max_retries
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )

    async def generate_json(self, prompt: str) -> dict:
        last_error: Exception | None = None
        raw_text = ""

        for attempt in range(self.max_retries + 1):
            raw_text = await self.generate_text(prompt)
            payload = safe_json_loads(raw_text)
            if isinstance(payload, dict):
                return payload

            repaired_payload = await self._repair_invalid_json(raw_text)
            if isinstance(repaired_payload, dict):
                return repaired_payload

            last_error = ValueError("LLM did not return a valid JSON object.")
            if attempt < self.max_retries:
                await asyncio.sleep(0.2 * (attempt + 1))

        raise last_error or ValueError(f"LLM did not return a valid JSON object: {raw_text}")

    async def generate_text(self, prompt: str) -> str:
        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                response = await self.client.responses.create(
                    model=self.model,
                    input=prompt,
                    temperature=0,
                )
                return response.output_text.strip()
            except (APIConnectionError, APITimeoutError, RateLimitError) as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    raise
                await asyncio.sleep(0.5 * (attempt + 1))

        raise last_error or RuntimeError("Unexpected OpenAI retry failure.")

    async def _repair_invalid_json(self, raw_text: str) -> dict | None:
        repair_prompt = (
            "Convert the following content into a valid JSON object only. "
            "Do not add explanation or markdown.\n\n"
            f"{raw_text}"
        )
        payload = safe_json_loads(await self.generate_text(repair_prompt))
        return payload if isinstance(payload, dict) else None


def build_llm_client() -> LlmClient | None:
    if settings.llm_provider.lower() == "openai" and settings.openai_api_key:
        return OpenAILlmClient(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            max_retries=settings.openai_max_retries,
            base_url=settings.openai_base_url,
        )
    return None


llm_client = build_llm_client()
