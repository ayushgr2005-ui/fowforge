from app.core.text import normalize_citations


def test_normalize_unicode_citations():
    assert normalize_citations("Answer 【S1】") == "Answer [S1]"


def test_ascii_citations_unchanged():
    assert normalize_citations("Answer [S1]") == "Answer [S1]"
