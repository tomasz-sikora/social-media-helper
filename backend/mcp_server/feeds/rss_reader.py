"""Generic RSS / Atom feed reader using feedparser."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

import feedparser
import httpx

from mcp_server.feeds.base import BaseFeedReader, FeedItem

logger = logging.getLogger(__name__)


def _parse_date(entry: feedparser.FeedParserDict) -> datetime:
    """Best-effort date parsing from a feedparser entry."""
    for attr in ("published_parsed", "updated_parsed", "created_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    for attr in ("published", "updated"):
        raw = getattr(entry, attr, None)
        if raw:
            try:
                return parsedate_to_datetime(raw)
            except Exception:
                pass
    return datetime.now(tz=timezone.utc)


def _source_from_url(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.hostname or url
    # Strip www. prefix
    return host.removeprefix("www.")


class RssFeedReader(BaseFeedReader):
    """Reads any RSS or Atom feed and returns FeedItems."""

    def __init__(self, feed_url: str, extra_tags: list[str] | None = None) -> None:
        self._feed_url = feed_url
        self._extra_tags = extra_tags or []
        self._source = _source_from_url(feed_url)

    @property
    def source_name(self) -> str:
        return self._source

    async def fetch(self) -> list[FeedItem]:
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                resp = await client.get(self._feed_url)
                resp.raise_for_status()
                raw = resp.content
        except Exception as exc:
            logger.warning("Failed to fetch RSS %s: %s", self._feed_url, exc)
            return []

        feed = feedparser.parse(raw)
        items: list[FeedItem] = []
        for entry in feed.entries:
            title = getattr(entry, "title", "").strip()
            url = getattr(entry, "link", "").strip()
            if not title or not url:
                continue
            summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
            author = getattr(entry, "author", "")
            tags = self._extra_tags + [t.get("term", "") for t in getattr(entry, "tags", [])]
            tags = [t for t in tags if t]
            items.append(
                FeedItem(
                    title=title,
                    url=url,
                    source=self._source,
                    published_at=_parse_date(entry),
                    summary=summary,
                    author=author,
                    tags=tags,
                    category=self._infer_category(tags, self._source),
                )
            )
        return items

    @staticmethod
    def _infer_category(tags: list[str], source: str) -> str:
        tech_keywords = {"tech", "technology", "programming", "software", "hacker"}
        news_keywords = {"news", "poland", "polska", "world", "świat"}
        joined = " ".join(tags + [source]).lower()
        if any(k in joined for k in tech_keywords):
            return "tech"
        if any(k in joined for k in news_keywords):
            return "news"
        return "general"
