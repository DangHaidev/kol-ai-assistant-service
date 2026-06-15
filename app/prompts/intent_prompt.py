INTENT_PROMPT_TEMPLATE = """
Bạn là bộ phân loại intent cho hệ thống KOL Booking.
Chỉ trả về JSON hợp lệ theo schema:
{{"intent": "recommend_kol|compare_kol|booking_help|general_question", "confidence": number}}

User message:
{message}
""".strip()
