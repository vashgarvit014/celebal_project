from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    repo: str = os.getenv("PATCHCONTEXT_REPO", "fastapi/fastapi")
    raw_dir: Path = Path(os.getenv("PATCHCONTEXT_RAW_DIR", "data/raw"))
    processed_dir: Path = Path(os.getenv("PATCHCONTEXT_PROCESSED_DIR", "data/processed"))
    index_dir: Path = Path(os.getenv("PATCHCONTEXT_INDEX_DIR", "indexes/fastapi"))
    embedding_model: str = os.getenv("PATCHCONTEXT_EMBEDDING_MODEL", "text-embedding-ada-002")
    chat_model: str = os.getenv("PATCHCONTEXT_CHAT_MODEL", "gpt-4o-mini")
    github_token: str | None = os.getenv("GITHUB_TOKEN")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    enable_nli: bool = os.getenv("PATCHCONTEXT_ENABLE_NLI", "0") == "1"
    nli_model: str = os.getenv("PATCHCONTEXT_NLI_MODEL", "facebook/bart-large-mnli")


def get_settings() -> Settings:
    return Settings()


def ensure_dirs(settings: Settings) -> None:
    for path in (settings.raw_dir, settings.processed_dir, settings.index_dir):
        path.mkdir(parents=True, exist_ok=True)

