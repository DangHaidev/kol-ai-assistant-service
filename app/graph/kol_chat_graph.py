from langgraph.graph import END, StateGraph

from app.graph.nodes import (
    check_clarification,
    extract_criteria,
    extract_intent,
    generate_clarification_response,
    generate_final_response,
    load_conversation,
    merge_criteria,
    rank_kols,
    retrieve_kol_candidates,
    save_conversation,
)
from app.graph.state import KolChatState


def should_recommend(state: KolChatState) -> str:
    if state.get("needClarification"):
        return "clarify"
    return "recommend"


def build_kol_chat_graph():
    workflow = StateGraph(KolChatState)

    workflow.add_node("load_conversation", load_conversation)
    workflow.add_node("extract_intent", extract_intent)
    workflow.add_node("extract_criteria", extract_criteria)
    workflow.add_node("merge_criteria", merge_criteria)
    workflow.add_node("check_clarification", check_clarification)
    workflow.add_node("generate_clarification_response", generate_clarification_response)
    workflow.add_node("retrieve_kol_candidates", retrieve_kol_candidates)
    workflow.add_node("rank_kols", rank_kols)
    workflow.add_node("generate_final_response", generate_final_response)
    workflow.add_node("save_conversation", save_conversation)

    workflow.set_entry_point("load_conversation")
    workflow.add_edge("load_conversation", "extract_intent")
    workflow.add_edge("extract_intent", "extract_criteria")
    workflow.add_edge("extract_criteria", "merge_criteria")
    workflow.add_edge("merge_criteria", "check_clarification")
    workflow.add_conditional_edges(
        "check_clarification",
        should_recommend,
        {
            "clarify": "generate_clarification_response",
            "recommend": "retrieve_kol_candidates",
        },
    )
    workflow.add_edge("generate_clarification_response", "save_conversation")
    workflow.add_edge("retrieve_kol_candidates", "rank_kols")
    workflow.add_edge("rank_kols", "generate_final_response")
    workflow.add_edge("generate_final_response", "save_conversation")
    workflow.add_edge("save_conversation", END)

    return workflow.compile()


chat_graph = build_kol_chat_graph()
