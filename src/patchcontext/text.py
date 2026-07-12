from __future__ import annotations

import re


_WHITESPACE = re.compile(r"\s+")


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return _WHITESPACE.sub(" ", value).strip()


def join_sections(*sections: tuple[str, str | None]) -> str:
    rendered: list[str] = []
    for label, value in sections:
        cleaned = clean_text(value)
        if cleaned:
            rendered.append(f"{label}: {cleaned}")
    return "\n\n".join(rendered)

