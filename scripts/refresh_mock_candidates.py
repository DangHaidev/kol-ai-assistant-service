"""Refresh the mock KOL candidates from the public KOL Booking API."""

from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import httpx


API_BASE_URL = "https://kol-booking-backend.onrender.com"
PAGE_SIZE = 100
SEARCH_SORT = "follower_desc"
DETAIL_WORKERS = 6
REQUEST_TIMEOUT_SECONDS = 45
PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "mock_data" / "backend_search_candidates.json"


def unwrap_data(payload: dict[str, Any]) -> Any:
    if payload.get("success") is False:
        raise RuntimeError(f"API returned an unsuccessful response: {payload}")
    return payload.get("data", payload)


def fetch_json(client: httpx.Client, path: str, params: dict[str, Any] | None = None) -> Any:
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = client.get(path, params=params)
            response.raise_for_status()
            return unwrap_data(response.json())
        except (httpx.HTTPError, ValueError) as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(0.5 * (attempt + 1))
    raise RuntimeError(f"Unable to fetch {path}") from last_error


def fetch_kol_summaries(client: httpx.Client) -> list[dict[str, Any]]:
    summaries_by_id: dict[int, dict[str, Any]] = {}
    fetched_entries = 0
    total_elements: int | None = None
    page = 0
    while True:
        response_data = fetch_json(
            client,
            "/api/v1/kols/search",
            {"page": page, "size": PAGE_SIZE, "sort": SEARCH_SORT},
        )
        content = response_data.get("content")
        if not isinstance(content, list):
            raise ValueError("KOL search response does not contain a content list.")
        fetched_entries += len(content)
        for item in content:
            if not isinstance(item, dict) or not isinstance(item.get("id"), int):
                raise ValueError("A KOL search result is missing an integer id.")
            summaries_by_id.setdefault(item["id"], item)

        if not response_data.get("hasNext", False):
            reported_total = response_data.get("totalElements")
            total_elements = reported_total if isinstance(reported_total, int) else None
            break
        page += 1

    if not summaries_by_id:
        raise ValueError("KOL search did not return any KOLs.")
    if total_elements is not None and total_elements != len(summaries_by_id):
        print(
            f"Search reported {total_elements} entries but returned {len(summaries_by_id)} unique KOL ids "
            f"across {fetched_entries} paginated entries."
        )
    return list(summaries_by_id.values())


def to_number(value: Any) -> int | float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def to_int(value: Any) -> int:
    number = to_number(value)
    return int(number) if number is not None else 0


def build_candidate(detail: dict[str, Any], category_slugs_by_id: dict[int, str]) -> dict[str, Any]:
    category_ids = detail.get("categoryIds")
    categories = [
        category_slugs_by_id[category_id]
        for category_id in category_ids if isinstance(category_id, int) and category_id in category_slugs_by_id
    ] if isinstance(category_ids, list) else []

    channels = detail.get("channels")
    platforms = [
        {
            "platform": str(channel.get("platform", "")).lower(),
            "profileUrl": channel.get("url"),
            "followers": to_int(channel.get("followerCount")),
            "engagementRate": to_number(channel.get("engagementRate")),
            "averageViews": None,
        }
        for channel in channels if isinstance(channel, dict) and channel.get("platform")
    ] if isinstance(channels, list) else []

    pricing_packages = detail.get("pricingPackages")
    prices = [
        number for package in pricing_packages if isinstance(package, dict)
        for number in [to_number(package.get("price"))] if number is not None
    ] if isinstance(pricing_packages, list) else []

    location = ", ".join(
        str(part).strip() for part in (detail.get("city"), detail.get("country")) if part
    ) or None
    gender = detail.get("gender")

    return {
        "kolId": to_int(detail.get("id")),
        "slug": detail.get("slug"),
        "displayName": detail.get("displayName") or f"KOL {detail.get('id')}",
        "avatarUrl": detail.get("avatarUrl"),
        "bio": detail.get("bio"),
        "location": location,
        "gender": str(gender).lower() if gender else None,
        "categories": categories,
        "platforms": platforms,
        "priceFrom": min(prices) if prices else None,
        "averageRating": to_number(detail.get("avgRating")),
        "completedBookingCount": 0,
        "bookingAcceptanceRate": None,
    }


def main() -> None:
    with httpx.Client(base_url=API_BASE_URL, timeout=REQUEST_TIMEOUT_SECONDS, follow_redirects=True) as client:
        categories = fetch_json(client, "/api/v1/categories")
        if not isinstance(categories, list):
            raise ValueError("Categories response is not a list.")
        category_slugs_by_id = {
            category["id"]: category["slug"]
            for category in categories
            if isinstance(category, dict) and isinstance(category.get("id"), int) and isinstance(category.get("slug"), str)
        }

        summaries = fetch_kol_summaries(client)
        kol_ids = [summary["id"] for summary in summaries]

        details: dict[int, dict[str, Any]] = {}
        failures: list[int] = []
        with ThreadPoolExecutor(max_workers=DETAIL_WORKERS) as executor:
            future_to_id = {
                executor.submit(fetch_json, client, f"/api/v1/kols/{kol_id}"): kol_id
                for kol_id in kol_ids
            }
            for future in as_completed(future_to_id):
                kol_id = future_to_id[future]
                try:
                    detail = future.result()
                    if not isinstance(detail, dict):
                        raise ValueError("KOL detail response is not an object.")
                    details[kol_id] = detail
                except Exception:
                    failures.append(kol_id)

    if failures:
        raise RuntimeError(f"Could not fetch {len(failures)} KOL details: {sorted(failures)}")

    candidates = [build_candidate(details[kol_id], category_slugs_by_id) for kol_id in sorted(details)]
    if len(candidates) != len(kol_ids):
        raise RuntimeError(f"Expected {len(kol_ids)} candidates but built {len(candidates)}.")

    payload = {"items": candidates}
    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(candidates)} candidates to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
