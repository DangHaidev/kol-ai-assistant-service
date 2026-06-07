from logging import getLogger

from app.graph.state import KolChatState
from app.schemas.criteria import KolSearchCriteria
from app.services.conversation_service import conversation_service
from app.services.criteria_service import criteria_service
from app.services.intent_service import intent_service
from app.services.kol_retrieval_service import kol_retrieval_service
from app.services.ranking_service import ranking_service
from app.services.response_service import response_service


logger = getLogger(__name__)


def _trace(state: KolChatState, node: str, **details: object) -> list[dict]:
    trace = list(state.get("workflowTrace", []))
    trace.append({"node": node, **details})
    return trace


def _warnings(state: KolChatState, *messages: str) -> list[str]:
    merged = list(state.get("warnings", []))
    for message in messages:
        if message and message not in merged:
            merged.append(message)
    return merged


async def load_conversation(state: KolChatState) -> dict:
    conversation = await conversation_service.ensure_conversation(
        state["brandId"],
        state.get("conversationId"),
    )
    history = await conversation_service.get_history(conversation["id"])
    await conversation_service.save_user_message(conversation["id"], state["userMessage"])
    old_criteria = KolSearchCriteria(**conversation.get("currentCriteria", {}))
    logger.info("workflow.load_conversation conversation_id=%s history_len=%s", conversation["id"], len(history))
    return {
        "conversationId": conversation["id"],
        "history": history,
        "oldCriteria": old_criteria,
        "mergedCriteria": old_criteria,
        "workflowTrace": _trace(
            state,
            "load_conversation",
            conversationId=conversation["id"],
            historyCount=len(history),
        ),
    }


async def extract_intent(state: KolChatState) -> dict:
    intent = await intent_service.detect_intent_with_fallback(state["userMessage"])
    logger.info("workflow.extract_intent intent=%s", intent)
    return {
        "intent": intent,
        "workflowTrace": _trace(state, "extract_intent", intent=intent),
    }


async def extract_criteria(state: KolChatState) -> dict:
    extracted_criteria = await criteria_service.extract_criteria_with_fallback(
        state["userMessage"],
        history=state.get("history", []),
        current_criteria=state.get("oldCriteria"),
    )
    logger.info(
        "workflow.extract_criteria category=%s platforms=%s",
        extracted_criteria.category,
        ",".join(extracted_criteria.platforms),
    )
    return {
        "extractedCriteria": extracted_criteria,
        "workflowTrace": _trace(
            state,
            "extract_criteria",
            category=extracted_criteria.category,
            platforms=extracted_criteria.platforms,
        ),
    }


async def merge_criteria(state: KolChatState) -> dict:
    old_criteria = state.get("oldCriteria", KolSearchCriteria())
    extracted_criteria = state.get("extractedCriteria", KolSearchCriteria())
    merged_criteria = criteria_service.merge_criteria(old_criteria, extracted_criteria)
    logger.info(
        "workflow.merge_criteria category=%s platforms=%s",
        merged_criteria.category,
        ",".join(merged_criteria.platforms),
    )
    return {
        "mergedCriteria": merged_criteria,
        "workflowTrace": _trace(
            state,
            "merge_criteria",
            category=merged_criteria.category,
            platforms=merged_criteria.platforms,
        ),
    }


async def check_clarification(state: KolChatState) -> dict:
    merged_criteria = state.get("mergedCriteria", KolSearchCriteria())
    need_clarification, questions = criteria_service.check_need_clarification(merged_criteria)
    if state.get("intent") == "recommend_kol" and (merged_criteria.category or merged_criteria.campaignGoal):
        need_clarification = False
        questions = []
    logger.info("workflow.check_clarification need=%s", need_clarification)
    return {
        "needClarification": need_clarification,
        "clarificationQuestions": questions,
        "workflowTrace": _trace(
            state,
            "check_clarification",
            needClarification=need_clarification,
            questionCount=len(questions),
        ),
    }


async def generate_clarification_response(state: KolChatState) -> dict:
    reply = response_service.build_clarification_reply(state.get("clarificationQuestions", []))
    return {
        "reply": reply,
        "workflowTrace": _trace(state, "generate_clarification_response"),
    }


async def retrieve_kol_candidates(state: KolChatState) -> dict:
    merged_criteria = state.get("mergedCriteria", KolSearchCriteria())
    try:
        candidates = await kol_retrieval_service.search_candidates(merged_criteria.model_dump())
        logger.info("workflow.retrieve_kol_candidates count=%s", len(candidates))
        return {
            "candidates": candidates,
            "workflowTrace": _trace(
                state,
                "retrieve_kol_candidates",
                candidateCount=len(candidates),
            ),
        }
    except Exception as exc:
        logger.exception("workflow.retrieve_kol_candidates_failed")
        warning = f"backend_unavailable:{exc.__class__.__name__}"
        return {
            "candidates": [],
            "warnings": _warnings(state, warning),
            "workflowTrace": _trace(
                state,
                "retrieve_kol_candidates",
                error=exc.__class__.__name__,
                candidateCount=0,
            ),
        }


async def rank_kols(state: KolChatState) -> dict:
    merged_criteria = state.get("mergedCriteria", KolSearchCriteria())
    recommendations = ranking_service.rank_candidates(
        state.get("candidates", []),
        merged_criteria,
    )
    logger.info("workflow.rank_kols count=%s", len(recommendations))
    return {
        "recommendations": recommendations,
        "workflowTrace": _trace(state, "rank_kols", recommendationCount=len(recommendations)),
    }


async def generate_final_response(state: KolChatState) -> dict:
    merged_criteria = state.get("mergedCriteria", KolSearchCriteria())
    reply = response_service.build_recommendation_reply(
        merged_criteria,
        state.get("recommendations", []),
    )
    return {
        "reply": reply,
        "workflowTrace": _trace(state, "generate_final_response"),
    }


async def save_conversation(state: KolChatState) -> dict:
    merged_criteria = state.get("mergedCriteria", KolSearchCriteria())
    trace = _trace(state, "save_conversation")
    warnings = state.get("warnings", [])
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
            "warnings": warnings,
            "workflowTrace": trace,
        },
    )
    return {
        "workflowTrace": trace,
        "warnings": warnings,
    }
