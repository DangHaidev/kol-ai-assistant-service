from app.schemas.criteria import KolSearchCriteria
from app.services.ranking_service import ranking_service


def test_ranking_service_prioritizes_matching_candidate() -> None:
    candidates = [
        {
            "kolId": 1,
            "slug": "match",
            "displayName": "Match",
            "categories": ["fashion"],
            "platforms": [{"platform": "tiktok", "followers": 150000, "engagementRate": 0.04}],
            "priceFrom": 8000000,
            "averageRating": 4.7,
            "completedBookingCount": 10,
        },
        {
            "kolId": 2,
            "slug": "mismatch",
            "displayName": "Mismatch",
            "categories": ["tech"],
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


def test_ranking_service_keeps_candidate_without_slug() -> None:
    candidates = [
        {
            "kolId": 1,
            "displayName": "Missing Slug",
            "categories": ["fashion"],
            "platforms": [{"platform": "tiktok", "followers": 150000, "engagementRate": 0.04}],
        },
        {
            "kolId": 2,
            "slug": "has-slug",
            "displayName": "Has Slug",
            "categories": ["fashion"],
            "platforms": [{"platform": "tiktok", "followers": 150000, "engagementRate": 0.04}],
        },
    ]
    criteria = KolSearchCriteria(category="fashion", platforms=["tiktok"])

    recommendations = ranking_service.rank_candidates(candidates, criteria, top_k=2)

    assert [item.kolId for item in recommendations] == [1, 2]
    assert recommendations[0].slug is None
    assert recommendations[1].slug == "has-slug"


def test_related_category_gets_partial_score() -> None:
    candidate = {
        "kolId": 1,
        "displayName": "Related",
        "categories": ["beauty"],
        "platforms": [{"platform": "instagram", "followers": 120000, "engagementRate": 0.04}],
    }
    criteria = KolSearchCriteria(category="fashion")

    score = ranking_service.calculate_category_score(candidate, criteria)

    assert score == 70


def test_platform_score_when_user_does_not_specify_platform() -> None:
    candidate = {
        "kolId": 1,
        "displayName": "No Platform Preference",
        "categories": ["fashion"],
        "platforms": [],
    }
    criteria = KolSearchCriteria(category="fashion")

    score = ranking_service.calculate_platform_score(candidate, criteria)

    assert score == 80


def test_budget_score_when_price_is_null() -> None:
    candidate = {
        "kolId": 1,
        "displayName": "Unknown Price",
        "categories": ["fashion"],
        "platforms": [{"platform": "tiktok", "followers": 110000, "engagementRate": 0.03}],
        "priceFrom": None,
    }
    criteria = KolSearchCriteria(maxBudget=10000000)

    score = ranking_service.calculate_budget_score(candidate, criteria)

    assert score == 60


def test_budget_score_drops_to_zero_when_candidate_far_exceeds_budget() -> None:
    candidate = {
        "kolId": 1,
        "displayName": "Too Expensive",
        "categories": ["fashion"],
        "platforms": [{"platform": "tiktok", "followers": 200000, "engagementRate": 0.04}],
        "priceFrom": 18000000,
    }
    criteria = KolSearchCriteria(maxBudget=10000000)

    score = ranking_service.calculate_budget_score(candidate, criteria)

    assert score == 0


def test_follower_score_handles_threshold_edges() -> None:
    candidate_near = {
        "kolId": 1,
        "displayName": "Near Threshold",
        "categories": ["fashion"],
        "platforms": [{"platform": "tiktok", "followers": 85000, "engagementRate": 0.04}],
    }
    candidate_low = {
        "kolId": 2,
        "displayName": "Too Low",
        "categories": ["fashion"],
        "platforms": [{"platform": "tiktok", "followers": 49000, "engagementRate": 0.04}],
    }
    criteria = KolSearchCriteria(platforms=["tiktok"], minFollowers=100000)

    near_score = ranking_service.calculate_follower_score(candidate_near, criteria)
    low_score = ranking_service.calculate_follower_score(candidate_low, criteria)

    assert near_score == 70
    assert low_score == 0
