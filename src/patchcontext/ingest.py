from __future__ import annotations

import argparse
from collections.abc import Iterable

from patchcontext.config import ensure_dirs, get_settings
from patchcontext.github_client import GitHubClient
from patchcontext.models import HistoryDocument, write_jsonl
from patchcontext.text import join_sections


API_ROOT = "https://api.github.com"


def ingest_commits(
    client: GitHubClient,
    repo: str,
    *,
    max_pages: int | None,
    max_items: int | None,
    include_file_details: bool = False,
) -> Iterable[HistoryDocument]:
    url = f"{API_ROOT}/repos/{repo}/commits"
    for index, item in enumerate(client.paginate(url, max_pages=max_pages), start=1):
        if max_items and index > max_items:
            return
        sha = item["sha"]
        commit = item.get("commit", {})
        author = (commit.get("author") or {}).get("name")
        message = commit.get("message", "")
        file_summary = ""
        if include_file_details:
            files_response = client.get(f"{API_ROOT}/repos/{repo}/commits/{sha}")
            files_payload = files_response.json()
            files = files_payload.get("files", [])
            file_summary = "\n".join(
                f"- {f.get('filename')} ({f.get('status')}, +{f.get('additions')}/-{f.get('deletions')})"
                for f in files[:30]
            )
        text = join_sections(("Commit message", message), ("Changed files", file_summary))
        yield HistoryDocument(
            id=f"commit:{sha}",
            source_type="commit",
            title=message.splitlines()[0][:180] if message else sha[:12],
            text=text,
            url=item["html_url"],
            repo=repo,
            created_at=(commit.get("author") or {}).get("date"),
            author=author,
            commit_sha=sha,
        )


def ingest_issues_and_prs(
    client: GitHubClient,
    repo: str,
    *,
    max_pages: int | None,
    max_items: int | None,
) -> Iterable[HistoryDocument]:
    url = f"{API_ROOT}/repos/{repo}/issues"
    for index, item in enumerate(
        client.paginate(url, state="all", sort="updated", direction="desc", max_pages=max_pages),
        start=1,
    ):
        if max_items and index > max_items:
            return
        number = int(item["number"])
        is_pr = "pull_request" in item
        source_type = "pull_request" if is_pr else "issue"
        comments = list(
            client.paginate(
                f"{API_ROOT}/repos/{repo}/issues/{number}/comments",
                max_pages=None,
            )
        )
        comment_text = "\n\n".join(
            f"Comment by {(comment.get('user') or {}).get('login')} at {comment.get('created_at')}: "
            f"{comment.get('body') or ''}"
            for comment in comments
        )
        sections = [
            ("Title", item.get("title")),
            ("Body", item.get("body")),
            ("Comments", comment_text),
        ]
        if is_pr:
            pr_payload = client.get(f"{API_ROOT}/repos/{repo}/pulls/{number}").json()
            sections.extend(
                [
                    ("Merge commit SHA", pr_payload.get("merge_commit_sha")),
                    ("Review decision", pr_payload.get("mergeable_state")),
                    ("Base branch", (pr_payload.get("base") or {}).get("ref")),
                    ("Head branch", (pr_payload.get("head") or {}).get("ref")),
                ]
            )
        yield HistoryDocument(
            id=f"{source_type}:{number}",
            source_type=source_type,
            title=item.get("title") or f"{source_type} {number}",
            text=join_sections(*sections),
            url=item["html_url"],
            repo=repo,
            created_at=item.get("created_at"),
            updated_at=item.get("updated_at"),
            author=(item.get("user") or {}).get("login"),
            pr_number=number if is_pr else None,
            issue_number=None if is_pr else number,
        )


def run_ingest(
    repo: str,
    max_pages: int | None = 10,
    max_items: int | None = None,
    include_file_details: bool = False,
) -> int:
    settings = get_settings()
    ensure_dirs(settings)
    client = GitHubClient(settings.github_token)
    docs = [
        *ingest_commits(
            client,
            repo,
            max_pages=max_pages,
            max_items=max_items,
            include_file_details=include_file_details,
        ),
        *ingest_issues_and_prs(client, repo, max_pages=max_pages, max_items=max_items),
    ]
    return write_jsonl(settings.processed_dir / "history.jsonl", docs)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest GitHub history for PatchContext.")
    parser.add_argument("--repo", default=get_settings().repo)
    parser.add_argument("--max-pages", type=int, default=10)
    parser.add_argument("--max-items", type=int, default=None)
    parser.add_argument("--include-file-details", action="store_true")
    args = parser.parse_args()
    count = run_ingest(args.repo, args.max_pages, args.max_items, args.include_file_details)
    print(f"Wrote {count} documents to {get_settings().processed_dir / 'history.jsonl'}")


if __name__ == "__main__":
    main()
