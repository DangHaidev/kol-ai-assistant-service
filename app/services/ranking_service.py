from app.schemas.criteria import KolSearchCriteria
from app.schemas.recommendation import RecommendationItem


RELATED_CATEGORIES = {
    "fashion": {"beauty", "lifestyle"},
    "beauty": {"fashion", "lifestyle"},
    "food": {"lifestyle", "travel", "entertainment"},
    "lifestyle": {"fashion", "beauty", "food", "travel", "fitness", "entertainment"},
    "travel": {"lifestyle", "food", "entertainment"},
    "fitness": {"lifestyle", "beauty"},
    "tech": {"entertainment"},
    "entertainment": {"lifestyle", "travel", "food", "tech"},
}


class RankingService:
    def rank_candidates(
        self,
        candidates: list[dict],
        criteria: KolSearchCriteria,
        top_k: int = 5,
    ) -> list[RecommendationItem]:
        scored: list[RecommendationItem] = []
        for candidate in candidates:
            match_score = self.calculate_match_score(candidate, criteria)
            scored.append(
                RecommendationItem(
                    kolId=candidate["kolId"],
                    displayName=candidate["displayName"],
                    avatarUrl=candidate.get("avatarUrl"),
                    categories=candidate.get("categories", []),
                    platforms=candidate.get("platforms", []),
                    priceFrom=candidate.get("priceFrom"),
                    rating=candidate.get("averageRating"),
                    completedBookingCount=candidate.get("completedBookingCount", 0),
                    matchScore=match_score,
                    reason=self.generate_reason(candidate, criteria),
                )
            )
        scored.sort(key=lambda item: item.matchScore, reverse=True)
        return scored[:top_k]

    def calculate_match_score(self, candidate: dict, criteria: KolSearchCriteria) -> int:
        score = (
            self.calculate_category_score(candidate, criteria) * 0.30
            + self.calculate_platform_score(candidate, criteria) * 0.15
            + self.calculate_follower_score(candidate, criteria) * 0.20
            + self.calculate_budget_score(candidate, criteria) * 0.15
            + self.calculate_engagement_score(candidate) * 0.10
            + self.calculate_rating_score(candidate) * 0.05
            + self.calculate_booking_score(candidate) * 0.05
        )
        return round(score)

    def calculate_category_score(self, candidate: dict, criteria: KolSearchCriteria) -> int:
        if not criteria.category:
            return 80

        categories = {str(category).lower() for category in candidate.get("categories", []) if category}
        target_category = criteria.category.lower()

        if target_category in categories:
            return 100
        if any(category in RELATED_CATEGORIES.get(target_category, set()) for category in categories):
            return 70
        return 0

    def calculate_platform_score(self, candidate: dict, criteria: KolSearchCriteria) -> int:
        if not criteria.platforms:
            return 80
        platforms = {
            str(platform.get("platform", "")).lower()
            for platform in candidate.get("platforms", [])
            if isinstance(platform, dict)
        }
        return 100 if any(platform in platforms for platform in criteria.platforms) else 0

    def calculate_follower_score(self, candidate: dict, criteria: KolSearchCriteria) -> int:
        followers = self._best_followers(candidate, criteria)
        if criteria.minFollowers:
            if followers >= criteria.minFollowers:
                return 100
            if followers >= criteria.minFollowers * 0.8:
                return 70
            if followers >= criteria.minFollowers * 0.5:
                return 40
            return 0
        if followers >= 1_000_000:
            return 100
        if followers >= 500_000:
            return 90
        if followers >= 100_000:
            return 80
        if followers >= 50_000:
            return 60
        if followers >= 10_000:
            return 40
        return 20

    def calculate_budget_score(self, candidate: dict, criteria: KolSearchCriteria) -> int:
        price = candidate.get("priceFrom")
        if price is None:
            return 60
        if criteria.maxBudget is None:
            return 80
        if price <= criteria.maxBudget:
            return 100
        if price <= criteria.maxBudget * 1.2:
            return 70
        if price <= criteria.maxBudget * 1.5:
            return 40
        return 0

    def calculate_engagement_score(self, candidate: dict) -> int:
        rate = self._best_engagement_rate(candidate)
        if rate >= 0.05:
            return 100
        if rate >= 0.03:
            return 80
        if rate >= 0.01:
            return 50
        return 20

    def calculate_rating_score(self, candidate: dict) -> int:
        rating = candidate.get("averageRating")
        if rating is None:
            return 60
        if rating >= 4.8:
            return 100
        if rating >= 4.5:
            return 90
        if rating >= 4.0:
            return 75
        if rating >= 3.5:
            return 50
        return 20

    def calculate_booking_score(self, candidate: dict) -> int:
        bookings = candidate.get("completedBookingCount", 0)
        if bookings >= 20:
            return 100
        if bookings >= 10:
            return 80
        if bookings >= 3:
            return 60
        if bookings > 0:
            return 40
        return 20

    def generate_reason(self, candidate: dict, criteria: KolSearchCriteria) -> str:
        reasons: list[str] = []
        categories = {str(category).lower() for category in candidate.get("categories", []) if category}
        if criteria.category and criteria.category.lower() in categories:
            reasons.append(f"thuoc linh vuc {criteria.category}")
        elif criteria.category and any(
            category in RELATED_CATEGORIES.get(criteria.category.lower(), set()) for category in categories
        ):
            reasons.append(f"co noi dung gan voi linh vuc {criteria.category}")

        best_platform = self._best_platform(candidate, criteria)
        if best_platform:
            platform_name = str(best_platform.get("platform", "")).lower()
            reasons.append(f"co {best_platform.get('followers', 0):,} follower tren {platform_name}")

        price = candidate.get("priceFrom")
        if criteria.maxBudget and price is not None and price <= criteria.maxBudget:
            reasons.append("gia nam trong ngan sach")

        rating = candidate.get("averageRating")
        if rating is not None and rating >= 4.5:
            reasons.append(f"rating cao {rating}/5")

        if not reasons:
            return "KOL nay co thong tin tuong doi phu hop voi yeu cau tim kiem."
        return "Phu hop vi " + ", ".join(reasons) + "."

    def _best_platform(self, candidate: dict, criteria: KolSearchCriteria) -> dict | None:
        platforms = candidate.get("platforms", [])
        if not platforms:
            return None
        if criteria.platforms:
            normalized = [platform.lower() for platform in criteria.platforms]
            for platform in platforms:
                platform_name = str(platform.get("platform", "")).lower()
                if platform_name in normalized:
                    return platform
        return max(platforms, key=lambda item: item.get("followers", 0))

    def _best_followers(self, candidate: dict, criteria: KolSearchCriteria) -> int:
        platform = self._best_platform(candidate, criteria)
        return platform.get("followers", 0) if platform else 0

    def _best_engagement_rate(self, candidate: dict) -> float:
        platforms = [platform for platform in candidate.get("platforms", []) if isinstance(platform, dict)]
        if not platforms:
            return 0.0
        return max(platform.get("engagementRate") or 0.0 for platform in platforms)


ranking_service = RankingService()
