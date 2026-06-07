from fastapi import APIRouter

from app.graph.kol_chat_graph import chat_graph
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    result = await chat_graph.ainvoke(
        {
            "brandId": request.brandId,
            "conversationId": request.conversationId,
            "userMessage": request.message,
        }
    )
    return ChatResponse(
        conversationId=result["conversationId"],
        reply=result["reply"],
        intent=result["intent"],
        criteria=result["mergedCriteria"],
        recommendations=result["recommendations"],
        needClarification=result["needClarification"],
        clarificationQuestions=result["clarificationQuestions"],
    )
