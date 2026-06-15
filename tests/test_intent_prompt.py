from app.prompts.intent_prompt import INTENT_PROMPT_TEMPLATE


def test_intent_prompt_formats_json_schema_without_key_error() -> None:
    prompt = INTENT_PROMPT_TEMPLATE.format(message="Tim KOL thoi trang")

    assert '{"intent": "recommend_kol|compare_kol|booking_help|general_question", "confidence": number}' in prompt
    assert "Tim KOL thoi trang" in prompt
