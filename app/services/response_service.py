from app.schemas.criteria import KolSearchCriteria
from app.schemas.recommendation import RecommendationItem


class ResponseService:
    def build_clarification_reply(self, questions: list[str]) -> str:
        return " ".join(questions)

    def build_recommendation_reply(
        self,
        criteria: KolSearchCriteria,
        recommendations: list[RecommendationItem],
    ) -> str:
        if not recommendations:
            return "Tôi đã hiểu yêu cầu nhưng hiện chưa tìm thấy KOL phù hợp. Bạn có thể nới follower hoặc ngân sách để tôi lọc lại."

        summary_parts: list[str] = []
        if criteria.category:
            summary_parts.append(criteria.category)
        if criteria.minFollowers:
            summary_parts.append(f"follower trên {criteria.minFollowers:,}")
        if criteria.platforms:
            summary_parts.append(f"ưu tiên {', '.join(criteria.platforms)}")
        if criteria.maxBudget:
            summary_parts.append(f"ngân sách dưới {criteria.maxBudget:,}")

        summary = ", ".join(summary_parts) if summary_parts else "yêu cầu hiện tại"
        return f"Tôi tìm thấy {len(recommendations)} KOL phù hợp với {summary}."


response_service = ResponseService()
