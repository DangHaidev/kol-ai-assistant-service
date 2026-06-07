CRITERIA_PROMPT_TEMPLATE = """
Bạn là bộ trích xuất tiêu chí tìm kiếm KOL.
Chỉ trả về JSON hợp lệ với các field:
category, platforms, minFollowers, maxFollowers, minBudget, maxBudget, location, gender, campaignGoal, serviceType.

Conversation history:
{history}

Current saved criteria:
{current_criteria}

New user message:
{message}
""".strip()
