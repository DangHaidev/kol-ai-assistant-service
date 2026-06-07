import json


def strip_code_fences(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def extract_json_candidate(raw: str) -> str | None:
    text = strip_code_fences(raw)
    stack: list[str] = []
    start_index: int | None = None
    pairs = {"{": "}", "[": "]"}
    closing = {value: key for key, value in pairs.items()}

    for index, char in enumerate(text):
        if char in pairs:
            if start_index is None:
                start_index = index
            stack.append(char)
            continue

        if char in closing and stack:
            if stack[-1] != closing[char]:
                continue
            stack.pop()
            if not stack and start_index is not None:
                return text[start_index : index + 1]
    return None


def safe_json_loads(raw: str) -> dict | list | None:
    candidates = [raw, strip_code_fences(raw)]
    extracted = extract_json_candidate(raw)
    if extracted:
        candidates.append(extracted)

    for candidate in candidates:
        if not candidate:
            continue
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    return None
