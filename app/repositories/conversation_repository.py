from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import AsyncSessionLocal
from app.models.conversation import Conversation
from app.models.message import Message


class InMemoryConversationRepository:
    """Fallback repository used when PostgreSQL is unavailable."""

    def __init__(self) -> None:
        self._conversations: dict[str, dict] = {}
        self._messages: dict[str, list[dict]] = defaultdict(list)

    async def create_conversation(self, brand_id: int) -> dict:
        conversation_id = str(uuid4())
        now = datetime.now(UTC).isoformat()
        conversation = {
            "id": conversation_id,
            "brandId": brand_id,
            "currentCriteria": {},
            "lastIntent": None,
            "createdAt": now,
            "updatedAt": now,
        }
        self._conversations[conversation_id] = conversation
        return deepcopy(conversation)

    async def get_conversation(self, conversation_id: str, brand_id: int) -> dict | None:
        conversation = self._conversations.get(conversation_id)
        if not conversation or conversation["brandId"] != brand_id:
            return None
        return deepcopy(conversation)

    async def update_current_criteria(
        self,
        conversation_id: str,
        criteria: dict,
        last_intent: str | None = None,
    ) -> None:
        conversation = self._conversations[conversation_id]
        conversation["currentCriteria"] = deepcopy(criteria)
        if last_intent:
            conversation["lastIntent"] = last_intent
        conversation["updatedAt"] = datetime.now(UTC).isoformat()

    async def save_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: dict | None = None,
    ) -> None:
        self._messages[conversation_id].append(
            {
                "role": role,
                "content": content,
                "metadata": deepcopy(metadata) if metadata else {},
                "createdAt": datetime.now(UTC).isoformat(),
            }
        )

    async def get_messages(self, conversation_id: str, limit: int = 20) -> list[dict]:
        return deepcopy(self._messages[conversation_id][-limit:])


class SqlAlchemyConversationRepository:
    def __init__(self, session_factory=AsyncSessionLocal) -> None:
        self.session_factory = session_factory

    async def create_conversation(self, brand_id: int) -> dict:
        async with self.session_factory() as session:
            conversation = Conversation(
                brand_id=brand_id,
                current_criteria={},
            )
            session.add(conversation)
            await session.commit()
            await session.refresh(conversation)
            return self._serialize_conversation(conversation)

    async def get_conversation(self, conversation_id: str, brand_id: int) -> dict | None:
        async with self.session_factory() as session:
            conversation = await session.scalar(
                select(Conversation).where(
                    Conversation.id == UUID(conversation_id),
                    Conversation.brand_id == brand_id,
                )
            )
            if conversation is None:
                return None
            return self._serialize_conversation(conversation)

    async def update_current_criteria(
        self,
        conversation_id: str,
        criteria: dict,
        last_intent: str | None = None,
    ) -> None:
        async with self.session_factory() as session:
            conversation = await session.scalar(
                select(Conversation).where(Conversation.id == UUID(conversation_id))
            )
            if conversation is None:
                raise KeyError(conversation_id)
            conversation.current_criteria = deepcopy(criteria)
            if last_intent:
                conversation.last_intent = last_intent
            await session.commit()

    async def save_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: dict | None = None,
    ) -> None:
        async with self.session_factory() as session:
            session.add(
                Message(
                    conversation_id=UUID(conversation_id),
                    role=role,
                    content=content,
                    message_metadata=deepcopy(metadata) if metadata else {},
                )
            )
            await session.commit()

    async def get_messages(self, conversation_id: str, limit: int = 20) -> list[dict]:
        async with self.session_factory() as session:
            result = await session.scalars(
                select(Message)
                .where(Message.conversation_id == UUID(conversation_id))
                .order_by(Message.created_at.desc(), Message.id.desc())
                .limit(limit)
            )
            messages = list(result)
            messages.reverse()
            return [self._serialize_message(message) for message in messages]

    def _serialize_conversation(self, conversation: Conversation) -> dict:
        return {
            "id": str(conversation.id),
            "brandId": conversation.brand_id,
            "currentCriteria": deepcopy(conversation.current_criteria or {}),
            "lastIntent": conversation.last_intent,
            "createdAt": self._to_iso(conversation.created_at),
            "updatedAt": self._to_iso(conversation.updated_at),
        }

    def _serialize_message(self, message: Message) -> dict:
        return {
            "role": message.role,
            "content": message.content,
            "metadata": deepcopy(message.message_metadata or {}),
            "createdAt": self._to_iso(message.created_at),
        }

    def _to_iso(self, value: datetime | None) -> str | None:
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.isoformat()


class HybridConversationRepository:
    def __init__(self, primary: SqlAlchemyConversationRepository, fallback: InMemoryConversationRepository) -> None:
        self.primary = primary
        self.fallback = fallback

    def _should_fallback(self, exc: Exception) -> bool:
        module_name = exc.__class__.__module__
        return isinstance(exc, (SQLAlchemyError, OSError, ValueError, KeyError)) or module_name.startswith("asyncpg.")

    async def create_conversation(self, brand_id: int) -> dict:
        try:
            return await self.primary.create_conversation(brand_id)
        except Exception as exc:
            if not self._should_fallback(exc):
                raise
            return await self.fallback.create_conversation(brand_id)

    async def get_conversation(self, conversation_id: str, brand_id: int) -> dict | None:
        try:
            return await self.primary.get_conversation(conversation_id, brand_id)
        except Exception as exc:
            if not self._should_fallback(exc):
                raise
            return await self.fallback.get_conversation(conversation_id, brand_id)

    async def update_current_criteria(
        self,
        conversation_id: str,
        criteria: dict,
        last_intent: str | None = None,
    ) -> None:
        try:
            await self.primary.update_current_criteria(conversation_id, criteria, last_intent=last_intent)
        except Exception as exc:
            if not self._should_fallback(exc):
                raise
            await self.fallback.update_current_criteria(conversation_id, criteria, last_intent=last_intent)

    async def save_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: dict | None = None,
    ) -> None:
        try:
            await self.primary.save_message(conversation_id, role, content, metadata)
        except Exception as exc:
            if not self._should_fallback(exc):
                raise
            await self.fallback.save_message(conversation_id, role, content, metadata)

    async def get_messages(self, conversation_id: str, limit: int = 20) -> list[dict]:
        try:
            return await self.primary.get_messages(conversation_id, limit=limit)
        except Exception as exc:
            if not self._should_fallback(exc):
                raise
            return await self.fallback.get_messages(conversation_id, limit=limit)


conversation_repository = HybridConversationRepository(
    primary=SqlAlchemyConversationRepository(),
    fallback=InMemoryConversationRepository(),
)
