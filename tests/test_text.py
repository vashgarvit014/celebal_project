from patchcontext.text import clean_text, join_sections


def test_clean_text_normalizes_whitespace() -> None:
    assert clean_text("hello\n\n   world") == "hello world"


def test_join_sections_skips_empty_values() -> None:
    assert join_sections(("Title", "Example"), ("Body", "")) == "Title: Example"

