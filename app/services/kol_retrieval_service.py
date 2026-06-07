from app.clients.kol_backend_client import kol_backend_client
from app.core.config import settings


class KolRetrievalService:
    def __init__(self, client=kol_backend_client) -> None:
        self.client = client

    async def search_candidates(self, criteria: dict, limit: int | None = None) -> list[dict]:
        return await self.client.search_candidates(
            criteria=criteria,
            limit=limit or settings.max_recommendation_candidates,
        )


kol_retrieval_service = KolRetrievalService()
