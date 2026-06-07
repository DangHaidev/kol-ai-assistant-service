import pytest

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
        "T\u00f4i mu\u1ed1n t\u00ecm KOL th\u1eddi trang follower tr\u00ean 100k, \u01b0u ti\u00ean TikTok, ng\u00e2n s\u00e1ch d\u01b0\u1edbi 10 tri\u1ec7u"
    )

    assert criteria.category == "fashion"
    assert criteria.platforms == ["tiktok"]
    assert criteria.minFollowers == 100000
    assert criteria.maxFollowers is None
    assert criteria.maxBudget == 10000000


@pytest.mark.parametrize(
    ("message", "expected_category"),
    [
        ("Tim KOL my pham de review serum", "beauty"),
        ("Can KOL am thuc review nha hang", "food"),
        ("Can creator lifestyle cho chien dich doi song", "lifestyle"),
        ("Tim KOL du lich review resort", "travel"),
        ("Tim creator gym va the hinh", "fitness"),
        ("Can reviewer cong nghe cho smartphone moi", "tech"),
        ("Tim streamer giai tri de quang ba su kien", "entertainment"),
    ],
)
def test_extract_criteria_supports_full_backend_category_set(message: str, expected_category: str) -> None:
    criteria = criteria_service.extract_criteria(message)

    assert criteria.category == expected_category


def test_normalize_llm_payload_maps_to_canonical_values() -> None:
    payload = criteria_service._normalize_llm_payload(
        {
            "category": "Cong nghe",
            "platforms": ["TikTok", "instagram", "TikTok"],
            "gender": "FEMALE",
            "campaignGoal": "Awareness",
        }
    )

    assert payload["category"] == "tech"
    assert payload["platforms"] == ["tiktok", "instagram"]
    assert payload["gender"] == "female"
    assert payload["campaignGoal"] == "awareness"


def test_normalize_llm_payload_drops_unknown_category_slug() -> None:
    payload = criteria_service._normalize_llm_payload(
        {
            "category": "unknown-niche",
            "platforms": ["YouTube"],
        }
    )

    assert payload["category"] is None
    assert payload["platforms"] == ["youtube"]
