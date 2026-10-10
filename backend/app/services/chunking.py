def chunk_text(text: str, size: int = 800, overlap: int = 120) -> list[str]:
    words = text.split()
    if not words:
        return []
    out = []
    start = 0
    while start < len(words):
        end = min(len(words), start + size)
        out.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = max(start + 1, end - overlap)
    return out
