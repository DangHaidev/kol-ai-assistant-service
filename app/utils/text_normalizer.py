import unicodedata


CATEGORY_KEYWORDS = {
    "fashion": ["thoi trang", "fashion"],
    "beauty": ["my pham", "lam dep", "beauty"],
    "food": ["an uong", "am thuc", "food"],
    "travel": ["du lich", "travel"],
    "technology": ["cong nghe", "technology", "tech"],
}

PLATFORM_KEYWORDS = {
    "tiktok": ["tiktok"],
    "instagram": ["instagram", "insta"],
    "facebook": ["facebook", "fb"],
    "youtube": ["youtube", "yt"],
}


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
