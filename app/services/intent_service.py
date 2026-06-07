from app.clients.llm_client import llm_client
from app.prompts.intent_prompt import INTENT_PROMPT_TEMPLATE


class IntentService:
    def detect_intent(self, message: str) -> str:
        text = message.lower()
        if any(keyword in text for keyword in ["compare", "so sanh"]):
            return "compare_kol"
        if any(keyword in text for keyword in ["booking", "dat lich", "book lich"]):
            return "booking_help"
        if any(keyword in text for keyword in ["kol", "koc", "influencer", "tim", "goi y"]):
            return "recommend_kol"
        return "general_question"

    async def detect_intent_with_fallback(self, message: str) -> str:
        if llm_client is None:
            return self.detect_intent(message)

        try:
            payload = await llm_client.generate_json(
                INTENT_PROMPT_TEMPLATE.format(message=message)
            )
            intent = payload.get("intent")
            if intent in {"recommend_kol", "compare_kol", "booking_help", "general_question"}:
                return intent
        except Exception:
            pass

        return self.detect_intent(message)


intent_service = IntentService()
