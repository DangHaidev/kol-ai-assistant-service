from fastapi import APIRouter

from app.schemas.recommendation import RecommendationRequest, RecommendationResponse
from app.services.kol_retrieval_service import kol_retrieval_service
from app.services.ranking_service import ranking_service

router = APIRouter()


@router.post("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest) -> RecommendationResponse:
    candidates = await kol_retrieval_service.search_candidates(
        request.criteria.model_dump(),
        limit=request.topK,
    )
    recommendations = ranking_service.rank_candidates(candidates, request.criteria, request.topK)
    return RecommendationResponse(criteria=request.criteria, recommendations=recommendations)
