from pathlib import Path

from patchcontext.models import HistoryDocument, read_jsonl, write_jsonl


def test_jsonl_roundtrip(tmp_path: Path) -> None:
    doc = HistoryDocument(
        id="pr:1",
        source_type="pull_request",
        title="Test PR",
        text="A design discussion.",
        url="https://github.com/fastapi/fastapi/pull/1",
        repo="fastapi/fastapi",
        pr_number=1,
    )
    path = tmp_path / "history.jsonl"
    assert write_jsonl(path, [doc]) == 1
    assert read_jsonl(path) == [doc]


def test_citation_labels() -> None:
    assert (
        HistoryDocument(
            id="commit:abcdef123456",
            source_type="commit",
            title="Commit",
            text="Body",
            url="https://github.com/fastapi/fastapi/commit/abcdef123456",
            repo="fastapi/fastapi",
            commit_sha="abcdef123456",
        ).citation_label
        == "abcdef123456"
    )

