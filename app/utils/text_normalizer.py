import unicodedata


CATEGORY_ALIASES = {
    "fashion": ["thoi trang", "fashion", "clothing", "outfit"],
    "beauty": ["my pham", "lam dep", "beauty", "skincare", "makeup", "cosmetics"],
    "food": ["an uong", "am thuc", "food", "do an", "nha hang", "fnb"],
    "lifestyle": ["lifestyle", "doi song", "life style", "song xanh", "daily life"],
    "travel": ["du lich", "travel", "trip", "review dia diem", "xuat ngoai"],
    "fitness": ["fitness", "the hinh", "gym", "tap luyen", "workout", "health"],
    "tech": ["cong nghe", "technology", "tech", "gadget", "review cong nghe"],
    "entertainment": ["giai tri", "entertainment", "music", "phim", "gameshow", "streamer"],
}

PLATFORM_ALIASES = {
    "tiktok": ["tiktok", "tik tok"],
    "instagram": ["instagram", "insta", "ig"],
    "facebook": ["facebook", "fb"],
    "youtube": ["youtube", "yt"],
}

CATEGORY_KEYWORDS = CATEGORY_ALIASES
PLATFORM_KEYWORDS = PLATFORM_ALIASES
CANONICAL_CATEGORIES = tuple(CATEGORY_KEYWORDS.keys())
CANONICAL_PLATFORMS = tuple(PLATFORM_KEYWORDS.keys())


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = "".join(char for char in normalized if not unicodedata.combining(char))
    return ascii_text.replace("đ", "d").replace("Đ", "D").lower()


def normalize_category(text: str) -> str | None:
    normalized_text = normalize_text(text)
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in normalized_text for keyword in keywords):
            return category
    return None


def normalize_platforms(text: str) -> list[str]:
    normalized_text = normalize_text(text)
    platforms: list[str] = []
    for platform, keywords in PLATFORM_KEYWORDS.items():
        if any(keyword in normalized_text for keyword in keywords):
            platforms.append(platform)
    return platforms
