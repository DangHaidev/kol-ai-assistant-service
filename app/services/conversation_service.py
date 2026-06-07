from app.core.exceptions import ConversationNotFoundError
from app.repositories.conversation_repository import conversation_repository
from app.schemas.criteria import KolSearchCriteria


class ConversationService:
    def __init__(self, repository=conversation_repository) -> None:
        self.repository = repository

    async def ensure_conversation(self, brand_id: int, conversation_id: str | None) -> dict:
        if conversation_id:
            conversation = await self.repository.get_conversation(conversation_id, brand_id)
            if not conversation:
                raise ConversationNotFoundError(f"Conversation {conversation_id} not found")
            return conversation
        return await self.repository.create_conversation(brand_id)

    async def get_history(self, conversation_id: str, limit: int = 20) -> list[dict]:
        return await self.repository.get_messages(conversation_id, limit=limit)

    async def save_user_message(self, conversation_id: str, content: str) -> None:
        await self.repository.save_message(conversation_id, "user", content)

    async def save_assistant_message(self, conversation_id: str, content: str, metadata: dict | None = None) -> None:
        await self.repository.save_message(conversation_id, "assistant", content, metadata)

    async def update_current_criteria(
        self,
        conversation_id: str,
        criteria: KolSearchCriteria,
        last_intent: str | None = None,
    ) -> None:
        await self.repository.update_current_criteria(
            conversation_id,
            criteria.model_dump(),
            last_intent=last_intent,
        )


conversation_service = ConversationService()
