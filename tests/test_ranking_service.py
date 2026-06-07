from app.schemas.criteria import KolSearchCriteria
from app.services.ranking_service import ranking_service


def test_ranking_service_prioritizes_matching_candidate() -> None:
    candidates = [
        {
            "kolId": 1,
            "displayName": "Match",
            "categories": ["fashion"],
            "platforms": [{"platform": "tiktok", "followers": 150000, "engagementRate": 0.04}],
            "priceFrom": 8000000,
            "averageRating": 4.7,
            "completedBookingCount": 10,
        },
        {
            "kolId": 2,
            "displayName": "Mismatch",
            "categories": ["technology"],
            "platforms": [{"platform": "youtube", "followers": 50000, "engagementRate": 0.01}],
            "priceFrom": 20000000,
            "averageRating": 4.0,
            "completedBookingCount": 1,
        },
    ]
    criteria = KolSearchCriteria(category="fashion", platforms=["tiktok"], minFollowers=100000, maxBudget=10000000)

    recommendations = ranking_service.rank_candidates(candidates, criteria, top_k=2)

    assert recommendations[0].kolId == 1
    assert recommendations[0].matchScore > recommendations[1].matchScore
