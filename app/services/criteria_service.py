import re
from logging import getLogger

from app.clients.llm_client import llm_client
from app.prompts.criteria_prompt import CRITERIA_PROMPT_TEMPLATE
from app.schemas.criteria import KolSearchCriteria
from app.utils.text_normalizer import CANONICAL_CATEGORIES, normalize_category, normalize_platforms, normalize_text


logger = getLogger(__name__)


class CriteriaService:
    async def extract_criteria_with_fallback(
        self,
        message: str,
        history: list[dict] | None = None,
        current_criteria: KolSearchCriteria | None = None,
    ) -> KolSearchCriteria:
        if llm_client is None:
            return self.extract_criteria(message, history=history, current_criteria=current_criteria)

        prompt = CRITERIA_PROMPT_TEMPLATE.format(
            history=history or [],
            current_criteria=(current_criteria or KolSearchCriteria()).model_dump(),
            message=message,
        )
        try:
            payload = await llm_client.generate_json(prompt)
            return KolSearchCriteria(**self._normalize_llm_payload(payload))
        except Exception as exc:
            logger.warning("criteria_service.llm_fallback reason=%s", exc.__class__.__name__)
            return self.extract_criteria(message, history=history, current_criteria=current_criteria)

    def extract_criteria(
        self,
        message: str,
        history: list[dict] | None = None,
        current_criteria: KolSearchCriteria | None = None,
    ) -> KolSearchCriteria:
        del history
        del current_criteria
        normalized_text = normalize_text(message)
        platforms = normalize_platforms(message)
        category = normalize_category(message)

        return KolSearchCriteria(
            category=category,
            platforms=platforms,
            minFollowers=self._extract_followers(normalized_text, "min"),
            maxFollowers=self._extract_followers(normalized_text, "max"),
            minBudget=self._extract_budget(normalized_text, "min"),
            maxBudget=self._extract_budget(normalized_text, "max"),
            gender=self._extract_gender(normalized_text),
            location=self._extract_location(message),
            campaignGoal=self._extract_campaign_goal(normalized_text),
        )

    def merge_criteria(self, old: KolSearchCriteria, new: KolSearchCriteria) -> KolSearchCriteria:
        merged_platforms = list(dict.fromkeys([*old.platforms, *new.platforms]))
        return KolSearchCriteria(
            category=new.category or old.category,
            platforms=merged_platforms,
            minFollowers=new.minFollowers if new.minFollowers is not None else old.minFollowers,
            maxFollowers=new.maxFollowers if new.maxFollowers is not None else old.maxFollowers,
            minBudget=new.minBudget if new.minBudget is not None else old.minBudget,
            maxBudget=new.maxBudget if new.maxBudget is not None else old.maxBudget,
            location=new.location or old.location,
            gender=new.gender or old.gender,
            campaignGoal=new.campaignGoal or old.campaignGoal,
            serviceType=new.serviceType or old.serviceType,
        )

    def check_need_clarification(self, criteria: KolSearchCriteria) -> tuple[bool, list[str]]:
        questions: list[str] = []
        if not criteria.category and not criteria.campaignGoal:
            questions.append(
                "Bạn muốn tìm KOL cho ngành hàng nào? Ví dụ: thời trang, mỹ phẩm, ăn uống, công nghệ hoặc du lịch."
            )
        if not criteria.platforms:
            questions.append("Bạn muốn ưu tiên nền tảng nào: TikTok, Instagram, Facebook hay YouTube?")
        return bool(questions), questions[:2]

    def _extract_followers(self, text: str, bound: str) -> int | None:
        patterns = {
            "min": [
                r"(?:followers?|follower|fl)\s*(?:tren|hon|>=|>|tu)\s*(\d+(?:[.,]\d+)?)\s*(k|m|trieu)?",
                r"(?:tren|hon|>=|>|tu)\s*(\d+(?:[.,]\d+)?)\s*(k|m|trieu)?\s*(?:followers?|follower|fl)",
            ],
            "max": [
                r"(?:followers?|follower|fl)\s*(?:duoi|it hon|<=|<)\s*(\d+(?:[.,]\d+)?)\s*(k|m|trieu)?",
                r"(?:duoi|it hon|<=|<)\s*(\d+(?:[.,]\d+)?)\s*(k|m|trieu)?\s*(?:followers?|follower|fl)",
            ],
        }
        for pattern in patterns[bound]:
            match = re.search(pattern, text)
            if match:
                return self._to_number(match.group(1), match.group(2))
        return None

    def _extract_budget(self, text: str, bound: str) -> int | None:
        patterns = {
            "min": [r"(?:ngan sach|budget|gia)\s*(?:tu|tren|hon)\s*(\d+(?:[.,]\d+)?)\s*(trieu|k|m)?"],
            "max": [r"(?:ngan sach|budget|gia)?\s*(?:duoi|it hon|<=|<)\s*(\d+(?:[.,]\d+)?)\s*(trieu|k|m)?"],
        }
        for pattern in patterns[bound]:
            match = re.search(pattern, text)
            if match:
                return self._to_number(match.group(1), match.group(2))
        return None

    def _to_number(self, raw_number: str, unit: str | None) -> int:
        value = float(raw_number.replace(",", "."))
        if unit in {"k"}:
            value *= 1_000
        elif unit in {"m", "trieu"}:
            value *= 1_000_000
        return int(value)

    def _extract_gender(self, text: str) -> str | None:
        if "nam" in text:
            return "male"
        if any(keyword in text for keyword in ["nu", "female"]):
            return "female"
        return None

    def _extract_location(self, text: str) -> str | None:
        normalized_text = normalize_text(text)
        for location in ["Ho Chi Minh", "TPHCM", "Ha Noi", "Da Nang", "Can Tho"]:
            if normalize_text(location) in normalized_text:
                return location
        return None

    def _extract_campaign_goal(self, text: str) -> str | None:
        if "ra mat" in text:
            return "product_launch"
        if "chuyen doi" in text or "booking" in text:
            return "conversion"
        if "nhan dien" in text or "brand awareness" in text:
            return "awareness"
        return None

    def _normalize_llm_payload(self, payload: dict) -> dict:
        normalized = dict(payload)

        category = payload.get("category")
        if isinstance(category, str):
            normalized_category = normalize_category(category) or category.strip().lower()
            normalized["category"] = normalized_category if normalized_category in CANONICAL_CATEGORIES else None

        platforms = payload.get("platforms")
        if isinstance(platforms, list):
            canonical_platforms: list[str] = []
            for platform in platforms:
                if not isinstance(platform, str):
                    continue
                canonical_platforms.extend(normalize_platforms(platform))
            normalized["platforms"] = list(dict.fromkeys(canonical_platforms))

        gender = payload.get("gender")
        if isinstance(gender, str):
            normalized["gender"] = gender.strip().lower()

        location = payload.get("location")
        if isinstance(location, str):
            normalized["location"] = location.strip()

        campaign_goal = payload.get("campaignGoal")
        if isinstance(campaign_goal, str):
            normalized["campaignGoal"] = campaign_goal.strip().lower()

        service_type = payload.get("serviceType")
        if isinstance(service_type, str):
            normalized["serviceType"] = service_type.strip().lower()

        return normalized


criteria_service = CriteriaService()
