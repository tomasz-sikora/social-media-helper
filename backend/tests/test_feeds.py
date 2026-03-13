"""Tests for feed fetchers."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from mcp_server.feeds.base import FeedItem
from mcp_server.feeds.hackernews import HackerNewsFeedReader
from mcp_server.feeds.rss_reader import RssFeedReader, _parse_date, _source_from_url


# ---------------------------------------------------------------------------
# FeedItem tests
# ---------------------------------------------------------------------------

def test_feed_item_id_is_stable():
    item = FeedItem(
        title="Test",
        url="https://example.com/article",
        source="test",
        published_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    assert item.id == item.id
    assert len(item.id) == 16


def test_feed_item_to_dict():
    item = FeedItem(
        title="Test",
        url="https://example.com/article",
        source="test",
        published_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    d = item.to_dict()
    assert d["title"] == "Test"
    assert d["url"] == "https://example.com/article"
    assert "id" in d


# ---------------------------------------------------------------------------
# source_from_url helper
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("url,expected", [
    ("https://www.example.com/feed.rss", "example.com"),
    ("https://news.ycombinator.com/", "news.ycombinator.com"),
    ("https://wiadomosci.onet.pl/rss.xml", "wiadomosci.onet.pl"),
])
def test_source_from_url(url, expected):
    assert _source_from_url(url) == expected


# ---------------------------------------------------------------------------
# HackerNewsFeedReader tests (mocked HTTP)
# ---------------------------------------------------------------------------

TOP_IDS = [1, 2, 3]
HN_ITEM_1 = {
    "id": 1,
    "type": "story",
    "title": "A HN story",
    "url": "https://hnstory.example.com",
    "by": "user1",
    "score": 100,
    "time": 1700000000,
}
HN_ITEM_2 = {
    "id": 2,
    "type": "comment",  # should be skipped
    "title": "",
}
HN_ITEM_3 = {
    "id": 3,
    "type": "story",
    "title": "Another story",
    "by": "user2",
    "score": 50,
    "time": 1700000100,
    # no url → should use HN link
}


@pytest.mark.asyncio
async def test_hackernews_fetch():
    responses = {
        "https://hacker-news.firebaseio.com/v0/topstories.json": TOP_IDS,
        "https://hacker-news.firebaseio.com/v0/item/1.json": HN_ITEM_1,
        "https://hacker-news.firebaseio.com/v0/item/2.json": HN_ITEM_2,
        "https://hacker-news.firebaseio.com/v0/item/3.json": HN_ITEM_3,
    }

    import httpx

    class MockResponse:
        def __init__(self, data):
            self._data = data
            self.status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return self._data

    class MockClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url):
            return MockResponse(responses[url])

    with patch("mcp_server.feeds.hackernews.httpx.AsyncClient", return_value=MockClient()):
        reader = HackerNewsFeedReader(top_n=3)
        items = await reader.fetch()

    assert len(items) == 2  # item 2 is a comment, skipped
    titles = [i.title for i in items]
    assert "A HN story" in titles
    assert "Another story" in titles

    hn_item = next(i for i in items if i.title == "Another story")
    assert "ycombinator" in hn_item.url


# ---------------------------------------------------------------------------
# RssFeedReader tests
# ---------------------------------------------------------------------------

SAMPLE_RSS = b"""<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <item>
      <title>Article One</title>
      <link>https://example.com/one</link>
      <description>Summary of article one.</description>
      <pubDate>Mon, 01 Jan 2024 12:00:00 +0000</pubDate>
      <author>Author A</author>
    </item>
    <item>
      <title>Article Two</title>
      <link>https://example.com/two</link>
      <description>Summary of article two.</description>
      <pubDate>Tue, 02 Jan 2024 12:00:00 +0000</pubDate>
    </item>
  </channel>
</rss>
"""


@pytest.mark.asyncio
async def test_rss_reader_fetch():
    import httpx

    class MockResponse:
        status_code = 200
        content = SAMPLE_RSS

        def raise_for_status(self):
            pass

    class MockClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url):
            return MockResponse()

    with patch("mcp_server.feeds.rss_reader.httpx.AsyncClient", return_value=MockClient()):
        reader = RssFeedReader("https://example.com/feed.rss", extra_tags=["test"])
        items = await reader.fetch()

    assert len(items) == 2
    assert items[0].title == "Article One"
    assert items[1].title == "Article Two"
    assert "test" in items[0].tags


@pytest.mark.asyncio
async def test_rss_reader_handles_http_error():
    import httpx

    class MockClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url):
            raise httpx.ConnectError("connection refused")

    with patch("mcp_server.feeds.rss_reader.httpx.AsyncClient", return_value=MockClient()):
        reader = RssFeedReader("https://unreachable.example.com/feed.rss")
        items = await reader.fetch()

    assert items == []
