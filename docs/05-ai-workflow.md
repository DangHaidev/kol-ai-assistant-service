# 05 - AI Workflow with LangGraph

## 1. Mục tiêu workflow

Workflow cần xử lý hội thoại có ngữ cảnh:

1. Nhận message mới.
2. Load conversation cũ.
3. Extract intent.
4. Extract criteria.
5. Merge criteria cũ + mới.
6. Kiểm tra thiếu thông tin.
7. Nếu thiếu, hỏi thêm.
8. Nếu đủ, retrieve KOL.
9. Rank KOL.
10. Generate response.
11. Save state.

## 2. State đề xuất

```python
from typing import Any, Optional
from pydantic import BaseModel, Field


class KolSearchCriteria(BaseModel):
    category: Optional[str] = None
    platforms: list[str] = Field(default_factory=list)
    minFollowers: Optional[int] = None
    maxFollowers: Optional[int] = None
    minBudget: Optional[int] = None
    maxBudget: Optional[int] = None
    location: Optional[str] = None
    gender: Optional[str] = None
    campaignGoal: Optional[str] = None
    serviceType: Optional[str] = None


class KolChatState(BaseModel):
    brandId: int
    conversationId: Optional[str] = None
    userMessage: str
    history: list[dict[str, Any]] = Field(default_factory=list)
    intent: Optional[str] = None
    oldCriteria: KolSearchCriteria = Field(default_factory=KolSearchCriteria)
    extractedCriteria: KolSearchCriteria = Field(default_factory=KolSearchCriteria)
    mergedCriteria: KolSearchCriteria = Field(default_factory=KolSearchCriteria)
    needClarification: bool = False
    clarificationQuestions: list[str] = Field(default_factory=list)
    candidates: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[dict[str, Any]] = Field(default_factory=list)
    reply: Optional[str] = None
```

## 3. Graph nodes

```txt
load_conversation
    ↓
extract_intent
    ↓
extract_criteria
    ↓
merge_criteria
    ↓
check_clarification
    ↓
    ├── need clarification → generate_clarification_response
    ↓
retrieve_kol_candidates
    ↓
rank_kols
    ↓
generate_final_response
    ↓
save_conversation
```

## 4. Pseudo-code LangGraph

```python
from langgraph.graph import StateGraph, END
from app.graph.state import KolChatState
from app.graph.nodes import (
    load_conversation,
    extract_intent,
    extract_criteria,
    merge_criteria,
    check_clarification,
    generate_clarification_response,
    retrieve_kol_candidates,
    rank_kols,
    generate_final_response,
    save_conversation,
)


def should_recommend(state: KolChatState) -> str:
    if state.needClarification:
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
```

## 5. Criteria merge rule

Nguyên tắc:

- Field mới có giá trị thì ghi đè hoặc bổ sung field cũ.
- Field mới null thì giữ field cũ.
- Platforms nên merge unique.
- Nếu user nói “không cần TikTok nữa” thì phải remove platform, nhưng MVP có thể chưa cần.

Pseudo-code:

```python
def merge_criteria(old, new):
    return KolSearchCriteria(
        category=new.category or old.category,
        platforms=list(set(old.platforms + new.platforms)),
        minFollowers=new.minFollowers or old.minFollowers,
        maxFollowers=new.maxFollowers or old.maxFollowers,
        minBudget=new.minBudget or old.minBudget,
        maxBudget=new.maxBudget or old.maxBudget,
        location=new.location or old.location,
        gender=new.gender or old.gender,
        campaignGoal=new.campaignGoal or old.campaignGoal,
        serviceType=new.serviceType or old.serviceType,
    )
```

## 6. Clarification rule

MVP nên hỏi thêm nếu thiếu cả `category` và `campaignGoal`.

Ví dụ:

```python
def check_need_clarification(criteria):
    questions = []

    if not criteria.category and not criteria.campaignGoal:
        questions.append("Bạn muốn tìm KOL cho ngành hàng nào? Ví dụ: thời trang, mỹ phẩm, ăn uống, công nghệ hoặc du lịch.")

    if not criteria.platforms:
        questions.append("Bạn muốn ưu tiên nền tảng nào: TikTok, Instagram, Facebook hay YouTube?")

    return len(questions) > 0, questions[:2]
```

Tuy nhiên không nên hỏi quá nhiều. Mỗi lần chỉ nên hỏi tối đa 1-2 câu.

## 7. Khi nào recommend ngay?

Có thể recommend nếu có ít nhất:

```txt
category hoặc campaignGoal
```

Và có thể dùng default:

```txt
topK = 5
platforms = all
minFollowers = null
maxBudget = null
```

Ví dụ user nhập:

```txt
Tìm KOL thời trang nổi bật
```

Có thể recommend luôn, không nhất thiết hỏi thêm.

## 8. Output cuối cùng

Graph trả về object:

```json
{
  "conversationId": "uuid",
  "reply": "Tôi tìm thấy 5 KOL phù hợp...",
  "intent": "recommend_kol",
  "criteria": {},
  "recommendations": [],
  "needClarification": false,
  "clarificationQuestions": []
}
```
