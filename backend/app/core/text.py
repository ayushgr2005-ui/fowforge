import re


def normalize_citations(text: str) -> str:
    return re.sub(r"【S(\d+)】", r"[S\1]", text or "")
