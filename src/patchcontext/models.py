from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class HistoryDocument:
    id: str
    source_type: str
    title: str
    text: str
    url: str
    repo: str
    created_at: str | None = None
    updated_at: str | None = None
    author: str | None = None
    commit_sha: str | None = None
    pr_number: int | None = None
    issue_number: int | None = None
    comment_id: int | None = None

    @property
    def citation_label(self) -> str:
        if self.commit_sha:
            return self.commit_sha[:12]
        if self.pr_number:
            return f"PR #{self.pr_number}"
        if self.issue_number:
            return f"Issue #{self.issue_number}"
        return self.id

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HistoryDocument":
        return cls(**data)


def write_jsonl(path: Path, docs: Iterable[HistoryDocument]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as fh:
        for doc in docs:
            fh.write(doc.to_json() + "\n")
            count += 1
    return count


def read_jsonl(path: Path) -> list[HistoryDocument]:
    with path.open("r", encoding="utf-8") as fh:
        return [HistoryDocument.from_dict(json.loads(line)) for line in fh if line.strip()]

