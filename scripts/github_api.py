#!/usr/bin/env python3
"""Small standard-library GitHub REST client for Atlas planning tools."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


API_VERSION = "2022-11-28"


class GitHubApiError(RuntimeError):
    """Describe a failed GitHub API request without exposing credentials."""

    def __init__(self, status: int, method: str, path: str, message: str) -> None:
        super().__init__(f"GitHub API {method} {path} returned {status}: {message}")
        self.status = status
        self.method = method
        self.path = path


class GitHubClient:
    """Read GitHub repository state through the versioned REST API."""

    def __init__(self, token: str, *, api_url: str = "https://api.github.com") -> None:
        self.token = token.strip()
        self.api_url = api_url.rstrip("/")

    def _url(self, path: str) -> str:
        if path.startswith("https://"):
            return path
        return self.api_url + "/" + path.lstrip("/")

    def request(self, method: str, path: str) -> tuple[Any, dict[str, str]]:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "atlas-dependabot-rollout/1.0",
            "X-GitHub-Api-Version": API_VERSION,
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = urllib.request.Request(self._url(path), headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = response.read()
                payload = json.loads(body) if body else None
                return payload, dict(response.headers.items())
        except urllib.error.HTTPError as error:
            try:
                payload = json.loads(error.read())
                message = str(payload.get("message", "request failed"))
            except (json.JSONDecodeError, AttributeError):
                message = "request failed"
            raise GitHubApiError(error.code, method, path, message) from error
        except urllib.error.URLError as error:
            raise RuntimeError(f"GitHub API request failed for {path}: {error.reason}") from error

    def get(self, path: str) -> Any:
        payload, _ = self.request("GET", path)
        return payload

    def get_optional(self, path: str) -> Any | None:
        try:
            return self.get(path)
        except GitHubApiError as error:
            if error.status == 404:
                return None
            raise

    def paginate(self, path: str) -> list[Any]:
        separator = "&" if "?" in path else "?"
        page = 1
        items: list[Any] = []
        while True:
            payload = self.get(f"{path}{separator}per_page=100&page={page}")
            if not isinstance(payload, list):
                raise RuntimeError(f"Expected a list from GitHub API path {path}")
            items.extend(payload)
            if len(payload) < 100:
                return items
            page += 1


def quote_path(value: str) -> str:
    """Quote a repository path while retaining path separators."""
    return urllib.parse.quote(value, safe="/")


def quote_ref(value: str) -> str:
    """Quote a branch, tag, or commit for use as one URL component."""
    return urllib.parse.quote(value, safe="")
