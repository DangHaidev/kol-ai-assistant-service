from app.schemas.criteria import KolSearchCriteria
from app.services.criteria_service import criteria_service


def test_extract_criteria_from_vietnamese_message() -> None:
    criteria = criteria_service.extract_criteria(
        "Toi muon tim KOL thoi trang follower tren 100k, uu tien TikTok, ngan sach duoi 10 trieu"
    )

    assert criteria.category == "fashion"
    assert criteria.platforms == ["tiktok"]
    assert criteria.minFollowers == 100000
    assert criteria.maxFollowers is None
    assert criteria.maxBudget == 10000000


def test_merge_criteria_keeps_old_values_and_adds_new_ones() -> None:
    old = KolSearchCriteria(category="fashion", minFollowers=100000)
    new = KolSearchCriteria(platforms=["tiktok"], maxBudget=10000000)

    merged = criteria_service.merge_criteria(old, new)

    assert merged.category == "fashion"
    assert merged.minFollowers == 100000
    assert merged.platforms == ["tiktok"]
    assert merged.maxBudget == 10000000


def test_extract_criteria_from_accented_message() -> None:
    criteria = criteria_service.extract_criteria(
        "Tôi muốn tìm KOL thời trang follower trên 100k, ưu tiên TikTok, ngân sách dưới 10 triệu"
    )

    assert criteria.category == "fashion"
    assert criteria.platforms == ["tiktok"]
    assert criteria.minFollowers == 100000
    assert criteria.maxFollowers is None
    assert criteria.maxBudget == 10000000


def test_normalize_llm_payload_maps_to_canonical_values() -> None:
    payload = criteria_service._normalize_llm_payload(
        {
            "category": "thoi trang",
            "platforms": ["TikTok"],
            "gender": "FEMALE",
            "campaignGoal": "Awareness",
        }
    )

    assert payload["category"] == "fashion"
    assert payload["platforms"] == ["tiktok"]
    assert payload["gender"] == "female"
    assert payload["campaignGoal"] == "awareness"
