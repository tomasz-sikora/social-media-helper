"""Tests for social platform feed readers and priority scorer."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from mcp_server.feeds.base import FeedItem
from mcp_server.feeds.social import (
    FacebookRSSHubReader,
    LinkedInRSSHubReader,
    TwitterNitterReader,
    get_social_readers,
)
from mcp_server.processing.scorer import apply_priority_scores


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_item(
    title: str = "Test",
    author: str = "",
    tags: list[str] | None = None,
    score: int = 0,
) -> FeedItem:
    return FeedItem(
        title=title,
        url=f"https://example.com/{title.replace(' ', '-')}",
        source="test",
        published_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        author=author,
        tags=tags or [],
        score=score,
    )


SAMPLE_RSS = b"""<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>@testuser on Nitter</title>
    <item>
      <title>Tweet about Python</title>
      <link>https://nitter.net/testuser/status/1</link>
      <description>Python is great!</description>
      <pubDate>Mon, 01 Jan 2024 12:00:00 +0000</pubDate>
      <author>testuser</author>
    </item>
  </channel>
</rss>
"""


def _mock_rss_client(content: bytes = SAMPLE_RSS):
    """Return a context-manager mock that yields a client returning *content*."""

    class MockResponse:
        status_code = 200
        content = content

        def raise_for_status(self):
            pass

    class MockClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url):
            return MockResponse()

    return MockClient()


# ---------------------------------------------------------------------------
# TwitterNitterReader
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_twitter_nitter_reader_uses_nitter_url():
    """When nitter_base_url is set it should be preferred."""
    captured_urls: list[str] = []

    class MockClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url):
            captured_urls.append(url)

            class Resp:
                status_code = 200
                content = SAMPLE_RSS

                def raise_for_status(self):
                    pass

            return Resp()

    with patch("mcp_server.feeds.rss_reader.httpx.AsyncClient", return_value=MockClient()):
        reader = TwitterNitterReader(
            "testuser",
            nitter_base_url="https://nitter.net",
            rsshub_base_url="https://rsshub.app",
        )
        items = await reader.fetch()

    assert captured_urls == ["https://nitter.net/testuser/rss"]
    assert len(items) == 1
    assert items[0].source == "twitter/@testuser"
    assert "twitter" in items[0].tags


@pytest.mark.asyncio
async def test_twitter_nitter_reader_falls_back_to_rsshub():
    """When nitter_base_url is empty, RSSHub URL should be used."""
    captured_urls: list[str] = []

    class MockClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url):
            captured_urls.append(url)

            class Resp:
                status_code = 200
                content = SAMPLE_RSS

                def raise_for_status(self):
                    pass

            return Resp()

    with patch("mcp_server.feeds.rss_reader.httpx.AsyncClient", return_value=MockClient()):
        reader = TwitterNitterReader(
            "testuser",
            nitter_base_url="",
            rsshub_base_url="https://rsshub.app",
        )
        items = await reader.fetch()

    assert captured_urls == ["https://rsshub.app/twitter/user/testuser"]
    assert items[0].source == "twitter/@testuser"


@pytest.mark.asyncio
async def test_twitter_nitter_reader_no_urls_returns_empty():
    """When neither nitter nor rsshub URL is set, return empty list."""
    reader = TwitterNitterReader("testuser")
    items = await reader.fetch()
    assert items == []


@pytest.mark.asyncio
async def test_twitter_nitter_reader_strips_at_prefix():
    reader = TwitterNitterReader(
        "@myhandle",
        nitter_base_url="https://nitter.net",
    )
    assert reader.source_name == "twitter/@myhandle"

    captured_urls: list[str] = []

    class MockClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url):
            captured_urls.append(url)

            class Resp:
                status_code = 200
                content = SAMPLE_RSS

                def raise_for_status(self):
                    pass

            return Resp()

    with patch("mcp_server.feeds.rss_reader.httpx.AsyncClient", return_value=MockClient()):
        await reader.fetch()

    assert captured_urls == ["https://nitter.net/myhandle/rss"]


# ---------------------------------------------------------------------------
# FacebookRSSHubReader
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_facebook_rsshub_reader_builds_correct_url():
    captured_urls: list[str] = []

    class MockClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url):
            captured_urls.append(url)

            class Resp:
                status_code = 200
                content = SAMPLE_RSS

                def raise_for_status(self):
                    pass

            return Resp()

    with patch("mcp_server.feeds.rss_reader.httpx.AsyncClient", return_value=MockClient()):
        reader = FacebookRSSHubReader("bbcnews", rsshub_base_url="https://rsshub.app")
        items = await reader.fetch()

    assert captured_urls == ["https://rsshub.app/facebook/page/bbcnews"]
    assert items[0].source == "facebook/bbcnews"
    assert "facebook" in items[0].tags


@pytest.mark.asyncio
async def test_facebook_rsshub_reader_no_base_url_returns_empty():
    reader = FacebookRSSHubReader("bbcnews", rsshub_base_url="")
    items = await reader.fetch()
    assert items == []


# ---------------------------------------------------------------------------
# LinkedInRSSHubReader
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_linkedin_rsshub_reader_builds_correct_url():
    captured_urls: list[str] = []

    class MockClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url):
            captured_urls.append(url)

            class Resp:
                status_code = 200
                content = SAMPLE_RSS

                def raise_for_status(self):
                    pass

            return Resp()

    with patch("mcp_server.feeds.rss_reader.httpx.AsyncClient", return_value=MockClient()):
        reader = LinkedInRSSHubReader("openai", rsshub_base_url="https://rsshub.app")
        items = await reader.fetch()

    assert captured_urls == ["https://rsshub.app/linkedin/company/openai"]
    assert items[0].source == "linkedin/openai"
    assert "linkedin" in items[0].tags


@pytest.mark.asyncio
async def test_linkedin_rsshub_reader_no_base_url_returns_empty():
    reader = LinkedInRSSHubReader("openai", rsshub_base_url="")
    items = await reader.fetch()
    assert items == []


# ---------------------------------------------------------------------------
# get_social_readers factory
# ---------------------------------------------------------------------------


def test_get_social_readers_returns_correct_count():
    readers = get_social_readers(
        twitter_accounts=["userA", "userB"],
        facebook_pages=["bbcnews"],
        linkedin_companies=["openai"],
        nitter_base_url="https://nitter.net",
        rsshub_base_url="https://rsshub.app",
    )
    assert len(readers) == 4  # 2 Twitter + 1 Facebook + 1 LinkedIn


def test_get_social_readers_skips_facebook_without_rsshub():
    readers = get_social_readers(
        twitter_accounts=[],
        facebook_pages=["bbcnews"],
        linkedin_companies=[],
        nitter_base_url="",
        rsshub_base_url="",  # no rsshub
    )
    assert len(readers) == 0


def test_get_social_readers_skips_empty_accounts():
    readers = get_social_readers(
        twitter_accounts=["", "  "],
        facebook_pages=[""],
        linkedin_companies=[""],
        nitter_base_url="https://nitter.net",
        rsshub_base_url="https://rsshub.app",
    )
    assert len(readers) == 0


# ---------------------------------------------------------------------------
# apply_priority_scores
# ---------------------------------------------------------------------------


def test_priority_score_boosts_author():
    items = [
        _make_item("Article by Friend", author="john_doe", score=10),
        _make_item("Random article", author="stranger", score=10),
    ]
    result = apply_priority_scores(items, priority_authors=["john_doe"], priority_tags=[], boost=100)
    scores = {i.title: i.score for i in result}
    assert scores["Article by Friend"] == 110
    assert scores["Random article"] == 10


def test_priority_score_boosts_tag():
    items = [
        _make_item("Local event", tags=["kraków", "community"], score=5),
        _make_item("Global news", tags=["world"], score=5),
    ]
    result = apply_priority_scores(items, priority_authors=[], priority_tags=["kraków"], boost=50)
    scores = {i.title: i.score for i in result}
    assert scores["Local event"] == 55
    assert scores["Global news"] == 5


def test_priority_score_stacks_multiple_criteria():
    """An item matching both author and tag should get double boost."""
    items = [
        _make_item("Double match", author="alice", tags=["community"], score=0),
    ]
    result = apply_priority_scores(
        items, priority_authors=["alice"], priority_tags=["community"], boost=100
    )
    assert result[0].score == 200


def test_priority_score_case_insensitive():
    items = [
        _make_item("Article", author="John_Doe", score=0),
    ]
    result = apply_priority_scores(items, priority_authors=["john_doe"], priority_tags=[], boost=100)
    assert result[0].score == 100


def test_priority_score_at_prefix_stripped():
    items = [
        _make_item("Tweet", author="@alice", score=0),
    ]
    result = apply_priority_scores(items, priority_authors=["@alice"], priority_tags=[], boost=100)
    assert result[0].score == 100


def test_priority_score_no_criteria_is_noop():
    items = [_make_item("Article", author="author", tags=["tag"], score=42)]
    result = apply_priority_scores(items, priority_authors=[], priority_tags=[], boost=100)
    assert result[0].score == 42


def test_priority_score_empty_items():
    result = apply_priority_scores([], priority_authors=["alice"], priority_tags=["tag"])
    assert result == []
