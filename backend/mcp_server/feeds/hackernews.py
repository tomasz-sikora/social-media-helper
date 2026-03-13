"""HackerNews feed reader using the official Firebase API."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

import httpx

from mcp_server.feeds.base import BaseFeedReader, FeedItem

logger = logging.getLogger(__name__)

HN_API_BASE = "https://hacker-news.firebaseio.com/v0"


class HackerNewsFeedReader(BaseFeedReader):
    """Fetches top stories from HackerNews using the public REST API."""

    def __init__(self, top_n: int = 30) -> None:
        self._top_n = top_n

    @property
    def source_name(self) -> str:
        return "hackernews"

    async def fetch(self) -> list[FeedItem]:
        async with httpx.AsyncClient(timeout=15) as client:
            top_ids = await self._fetch_top_ids(client)
            items = await asyncio.gather(
                *[self._fetch_item(client, item_id) for item_id in top_ids[: self._top_n]],
                return_exceptions=True,
            )
        result: list[FeedItem] = []
        for item in items:
            if isinstance(item, Exception):
                logger.warning("HN item fetch error: %s", item)
                continue
            if item is not None:
                result.append(item)
        return result

    async def _fetch_top_ids(self, client: httpx.AsyncClient) -> list[int]:
        resp = await client.get(f"{HN_API_BASE}/topstories.json")
        resp.raise_for_status()
        return resp.json()

    async def _fetch_item(self, client: httpx.AsyncClient, item_id: int) -> FeedItem | None:
        resp = await client.get(f"{HN_API_BASE}/item/{item_id}.json")
        resp.raise_for_status()
        data = resp.json()
        if not data or data.get("type") != "story" or not data.get("title"):
            return None
        url = data.get("url") or f"https://news.ycombinator.com/item?id={item_id}"
        published_at = datetime.fromtimestamp(data.get("time", 0), tz=timezone.utc)
        return FeedItem(
            title=data["title"],
            url=url,
            source=self.source_name,
            published_at=published_at,
            summary=data.get("text", ""),
            author=data.get("by", ""),
            score=data.get("score", 0),
            tags=["tech", "hacker-news"],
            category="tech",
        )
