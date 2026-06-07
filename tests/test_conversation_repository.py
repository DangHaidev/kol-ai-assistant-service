import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.repositories.conversation_repository import (
    HybridConversationRepository,
    InMemoryConversationRepository,
)


class BrokenConversationRepository:
    async def create_conversation(self, brand_id: int) -> dict:
        raise SQLAlchemyError("db down")

    async def get_conversation(self, conversation_id: str, brand_id: int) -> dict | None:
        raise SQLAlchemyError("db down")

    async def update_current_criteria(
        self,
        conversation_id: str,
        criteria: dict,
        last_intent: str | None = None,
    ) -> None:
        raise SQLAlchemyError("db down")

    async def save_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: dict | None = None,
    ) -> None:
        raise SQLAlchemyError("db down")

    async def get_messages(self, conversation_id: str, limit: int = 20) -> list[dict]:
        raise SQLAlchemyError("db down")


@pytest.mark.asyncio
async def test_hybrid_repository_falls_back_to_in_memory() -> None:
    repository = HybridConversationRepository(
        primary=BrokenConversationRepository(),
        fallback=InMemoryConversationRepository(),
    )

    conversation = await repository.create_conversation(brand_id=99)
    await repository.save_message(conversation["id"], "user", "hello")
    await repository.update_current_criteria(conversation["id"], {"category": "fashion"}, last_intent="recommend_kol")

    loaded = await repository.get_conversation(conversation["id"], brand_id=99)
    messages = await repository.get_messages(conversation["id"])

    assert loaded is not None
    assert loaded["currentCriteria"]["category"] == "fashion"
    assert loaded["lastIntent"] == "recommend_kol"
    assert messages[0]["content"] == "hello"
