from app.graph.state import KolChatState
from app.schemas.criteria import KolSearchCriteria
from app.services.conversation_service import conversation_service
from app.services.criteria_service import criteria_service
from app.services.intent_service import intent_service
from app.services.kol_retrieval_service import kol_retrieval_service
from app.services.ranking_service import ranking_service
from app.services.response_service import response_service


async def load_conversation(state: KolChatState) -> dict:
    conversation = await conversation_service.ensure_conversation(
        state["brandId"],
        state.get("conversationId"),
    )
    history = await conversation_service.get_history(conversation["id"])
    await conversation_service.save_user_message(conversation["id"], state["userMessage"])
    old_criteria = KolSearchCriteria(**conversation.get("currentCriteria", {}))
    return {
        "conversationId": conversation["id"],
        "history": history,
        "oldCriteria": old_criteria,
        "mergedCriteria": old_criteria,
    }


async def extract_intent(state: KolChatState) -> dict:
    return {"intent": await intent_service.detect_intent_with_fallback(state["userMessage"])}


async def extract_criteria(state: KolChatState) -> dict:
    extracted_criteria = await criteria_service.extract_criteria_with_fallback(
        state["userMessage"],
        history=state.get("history", []),
        current_criteria=state.get("oldCriteria"),
    )
    return {"extractedCriteria": extracted_criteria}


async def merge_criteria(state: KolChatState) -> dict:
    old_criteria = state.get("oldCriteria", KolSearchCriteria())
    extracted_criteria = state.get("extractedCriteria", KolSearchCriteria())
    merged_criteria = criteria_service.merge_criteria(old_criteria, extracted_criteria)
    return {"mergedCriteria": merged_criteria}


async def check_clarification(state: KolChatState) -> dict:
    merged_criteria = state.get("mergedCriteria", KolSearchCriteria())
    need_clarification, questions = criteria_service.check_need_clarification(merged_criteria)
    if state.get("intent") == "recommend_kol" and (merged_criteria.category or merged_criteria.campaignGoal):
        need_clarification = False
        questions = []
    return {
        "needClarification": need_clarification,
        "clarificationQuestions": questions,
    }


async def generate_clarification_response(state: KolChatState) -> dict:
    return {"reply": response_service.build_clarification_reply(state.get("clarificationQuestions", []))}


async def retrieve_kol_candidates(state: KolChatState) -> dict:
    merged_criteria = state.get("mergedCriteria", KolSearchCriteria())
    candidates = await kol_retrieval_service.search_candidates(merged_criteria.model_dump())
    return {"candidates": candidates}


async def rank_kols(state: KolChatState) -> dict:
    merged_criteria = state.get("mergedCriteria", KolSearchCriteria())
    recommendations = ranking_service.rank_candidates(
        state.get("candidates", []),
        merged_criteria,
    )
    return {"recommendations": recommendations}


async def generate_final_response(state: KolChatState) -> dict:
    merged_criteria = state.get("mergedCriteria", KolSearchCriteria())
    reply = response_service.build_recommendation_reply(
        merged_criteria,
        state.get("recommendations", []),
    )
    return {"reply": reply}


async def save_conversation(state: KolChatState) -> dict:
    merged_criteria = state.get("mergedCriteria", KolSearchCriteria())
    await conversation_service.update_current_criteria(
        state["conversationId"],
        merged_criteria,
        last_intent=state.get("intent"),
    )
    await conversation_service.save_assistant_message(
        state["conversationId"],
        state.get("reply") or "",
        metadata={
            "intent": state.get("intent"),
            "criteria": merged_criteria.model_dump(),
            "recommendationCount": len(state.get("recommendations", [])),
        },
    )
    return {}
