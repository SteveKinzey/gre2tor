from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import os
import re
import urllib.error
import urllib.request

from .version import APP_VERSION, GITHUB_LATEST_RELEASE_API, GITHUB_RELEASES_URL

_CACHE_TTL = timedelta(hours=6)
_update_cache: dict | None = None
_update_cache_at: datetime | None = None


@dataclass(frozen=True)
class UpdateInfo:
    current_version: str
    latest_version: str | None
    update_available: bool
    release_url: str
    checked: bool
    error: str | None = None

    def as_dict(self) -> dict:
        return {
            "current_version": self.current_version,
            "latest_version": self.latest_version,
            "update_available": self.update_available,
            "release_url": self.release_url,
            "checked": self.checked,
            "error": self.error,
        }


def _version_tuple(value: str | None) -> tuple[int, ...]:
    if not value:
        return (0,)
    cleaned = value.strip().lower().removeprefix("v")
    parts = re.findall(r"\d+", cleaned)
    return tuple(int(part) for part in parts[:4]) if parts else (0,)


def _is_newer(latest: str | None, current: str) -> bool:
    return _version_tuple(latest) > _version_tuple(current)


def check_for_updates(*, force: bool = False, timeout: float = 2.5) -> dict:
    global _update_cache, _update_cache_at

    if os.environ.get("GRE2TOR_DISABLE_UPDATE_CHECK") == "1":
        return UpdateInfo(
            current_version=APP_VERSION,
            latest_version=None,
            update_available=False,
            release_url=GITHUB_RELEASES_URL,
            checked=False,
        ).as_dict()

    now = datetime.now(timezone.utc)
    if not force and _update_cache and _update_cache_at and now - _update_cache_at < _CACHE_TTL:
        return _update_cache

    request = urllib.request.Request(
        GITHUB_LATEST_RELEASE_API,
        headers={"Accept": "application/vnd.github+json", "User-Agent": f"GRE2Tor/{APP_VERSION}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        latest = payload.get("tag_name") or payload.get("name")
        release_url = payload.get("html_url") or GITHUB_RELEASES_URL
        info = UpdateInfo(
            current_version=APP_VERSION,
            latest_version=latest,
            update_available=_is_newer(latest, APP_VERSION),
            release_url=release_url,
            checked=True,
        ).as_dict()
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        info = UpdateInfo(
            current_version=APP_VERSION,
            latest_version=None,
            update_available=False,
            release_url=GITHUB_RELEASES_URL,
            checked=False,
            error=str(exc),
        ).as_dict()

    _update_cache = info
    _update_cache_at = now
    return info
