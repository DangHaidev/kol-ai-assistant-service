from __future__ import annotations

import asyncio
from urllib.parse import quote

import httpx
from openai import APIConnectionError, APITimeoutError, RateLimitError
from openai import AsyncOpenAI

from app.core.config import settings
from app.utils.json_utils import safe_json_loads


class LlmClient:
    async def generate_json(self, prompt: str) -> dict:
        last_error: Exception | None = None
        raw_text = ""

        for attempt in range(self.max_retries + 1):
            raw_text = await self._generate_json_response(prompt)
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
        raise NotImplementedError

    async def _generate_json_response(self, prompt: str) -> str:
        return await self.generate_text(prompt)

    async def _repair_invalid_json(self, raw_text: str) -> dict | None:
        repair_prompt = (
            "Convert the following content into a valid JSON object only. "
            "Do not add explanation or markdown.\n\n"
            f"{raw_text}"
        )
        payload = safe_json_loads(await self._generate_json_response(repair_prompt))
        return payload if isinstance(payload, dict) else None


class OpenAILlmClient(LlmClient):
    def __init__(
        self,
        api_key: str,
        model: str,
        max_retries: int,
        timeout_seconds: float,
        base_url: str | None = None,
    ) -> None:
        self.model = model
        self.max_retries = max_retries
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout_seconds,
            max_retries=0,
        )

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
            except APITimeoutError:
                raise
            except (APIConnectionError, RateLimitError) as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    raise
                await asyncio.sleep(0.5 * (attempt + 1))

        raise last_error or RuntimeError("Unexpected OpenAI retry failure.")


class GeminiLlmClient(LlmClient):
    """Gemini client using the native Generative Language API."""

    base_url = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(
        self,
        api_key: str,
        model: str,
        max_retries: int,
        timeout_seconds: float,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.max_retries = max_retries
        self.client = http_client or httpx.AsyncClient(timeout=timeout_seconds)

    async def generate_text(self, prompt: str) -> str:
        return await self._generate_content(prompt)

    async def _generate_json_response(self, prompt: str) -> str:
        return await self._generate_content(prompt, response_mime_type="application/json")

    async def _generate_content(self, prompt: str, response_mime_type: str | None = None) -> str:
        payload: dict = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0},
        }
        if response_mime_type:
            payload["generationConfig"]["responseMimeType"] = response_mime_type

        url = f"{self.base_url}/models/{quote(self.model, safe='')}:generateContent"
        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                response = await self.client.post(
                    url,
                    headers={"x-goog-api-key": self.api_key},
                    json=payload,
                )
                response.raise_for_status()
                return self._extract_text(response.json())
            except httpx.TimeoutException:
                raise
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code < 500 and exc.response.status_code != 429:
                    raise
                last_error = exc
            except httpx.RequestError as exc:
                last_error = exc

            if attempt < self.max_retries:
                await asyncio.sleep(0.5 * (attempt + 1))

        raise last_error or RuntimeError("Unexpected Gemini retry failure.")

    @staticmethod
    def _extract_text(response_payload: dict) -> str:
        candidates = response_payload.get("candidates", [])
        if not candidates:
            raise ValueError("Gemini did not return a response candidate.")

        parts = candidates[0].get("content", {}).get("parts", [])
        text = "".join(part.get("text", "") for part in parts if isinstance(part, dict)).strip()
        if not text:
            raise ValueError("Gemini did not return text content.")
        return text


def build_llm_client() -> LlmClient | None:
    if settings.llm_provider.lower() == "openai" and settings.openai_api_key:
        return OpenAILlmClient(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            max_retries=settings.openai_max_retries,
            timeout_seconds=settings.openai_timeout_seconds,
            base_url=settings.openai_base_url,
        )
    if settings.llm_provider.lower() == "gemini" and settings.gemini_api_key:
        return GeminiLlmClient(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
            max_retries=settings.gemini_max_retries,
            timeout_seconds=settings.gemini_timeout_seconds,
        )
    return None


llm_client = build_llm_client()
