from __future__ import annotations

import time
from collections.abc import Iterator
from typing import Any

import requests
from tenacity import retry, stop_after_attempt, wait_exponential


class GitHubClient:
    def __init__(self, token: str | None = None) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "PatchContext",
            }
        )
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    @retry(wait=wait_exponential(multiplier=1, min=1, max=20), stop=stop_after_attempt(5))
    def get(self, url: str, **params: Any) -> requests.Response:
        response = self.session.get(url, params=params or None, timeout=30)
        if response.status_code == 403 and response.headers.get("X-RateLimit-Remaining") == "0":
            reset = int(response.headers.get("X-RateLimit-Reset", "0"))
            sleep_for = max(0, reset - int(time.time())) + 2
            time.sleep(min(sleep_for, 120))
            response = self.session.get(url, params=params or None, timeout=30)
        response.raise_for_status()
        return response

    def paginate(
        self,
        url: str,
        *,
        max_pages: int | None = None,
        **params: Any,
    ) -> Iterator[dict[str, Any]]:
        page = 1
        while True:
            response = self.get(url, per_page=100, page=page, **params)
            items = response.json()
            if not items:
                return
            yield from items
            if max_pages and page >= max_pages:
                return
            if 'rel="next"' not in response.headers.get("Link", ""):
                return
            page += 1

