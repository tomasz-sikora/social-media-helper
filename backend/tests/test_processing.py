"""Tests for processing pipeline (dedup, categorise, summarise)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from mcp_server.feeds.base import FeedItem
from mcp_server.processing.categorizer import categorise, categorise_items
from mcp_server.processing.deduplicator import deduplicate
from mcp_server.processing.summarizer import _detect_clickbait, _extractive_summary


def _make_item(title: str, summary: str = "", score: int = 0, category: str = "general") -> FeedItem:
    return FeedItem(
        title=title,
        url=f"https://example.com/{title.replace(' ', '-')}",
        source="test",
        published_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        summary=summary,
        score=score,
        category=category,
    )


# ---------------------------------------------------------------------------
# Categoriser tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("title,expected_category", [
    ("Python 3.13 released with new features", "tech"),
    ("Warsaw stock exchange hits new high", "business"),
    ("Champions League final match preview", "sport"),
    ("NASA discovers water on Mars", "science"),
    ("Polish government announces new budget", "news"),
    ("Oscar nominations revealed", "entertainment"),
    ("Random article about nothing", "general"),
])
def test_categorise_item(title, expected_category):
    item = _make_item(title)
    assert categorise(item) == expected_category


def test_categorise_items_in_place():
    items = [
        _make_item("OpenAI launches new GPT model"),
        _make_item("Football World Cup highlights"),
    ]
    result = categorise_items(items)
    assert result[0].category == "tech"
    assert result[1].category == "sport"


def test_categorise_honours_preset_category():
    item = _make_item("OpenAI GPT news", category="business")
    assert categorise(item) == "business"


# ---------------------------------------------------------------------------
# Deduplicator tests
# ---------------------------------------------------------------------------

def test_deduplicate_removes_near_duplicates():
    items = [
        _make_item("OpenAI releases GPT-5 model today", score=100),
        _make_item("OpenAI releases GPT-5 model", score=50),  # near-duplicate
        _make_item("Python 3.12 released with speed improvements", score=80),
    ]
    result = deduplicate(items, threshold=0.7)
    assert len(result) == 2
    titles = {i.title for i in result}
    # The highest-scoring duplicate should be kept
    assert "OpenAI releases GPT-5 model today" in titles
    assert "Python 3.12 released with speed improvements" in titles


def test_deduplicate_keeps_unique_items():
    items = [
        _make_item("Python 3.12 released"),
        _make_item("JavaScript framework benchmark 2024"),
        _make_item("Poland wins football match"),
    ]
    result = deduplicate(items, threshold=0.85)
    assert len(result) == 3


def test_deduplicate_empty():
    assert deduplicate([], threshold=0.85) == []


def test_deduplicate_assigns_cluster_labels():
    items = [
        _make_item("Breaking news about AI today", score=10),
        _make_item("Breaking news about AI", score=5),
    ]
    deduplicate(items, threshold=0.7)
    clusters = {i.dedup_cluster for i in items}
    assert len(clusters) == 1  # both in same cluster


# ---------------------------------------------------------------------------
# Summariser tests
# ---------------------------------------------------------------------------

def test_extractive_summary_returns_first_two_sentences():
    item = _make_item(
        "Test",
        summary="First sentence. Second sentence. Third sentence.",
    )
    summary = _extractive_summary(item)
    assert "First sentence" in summary
    assert "Second sentence" in summary
    assert "Third" not in summary


def test_extractive_summary_falls_back_to_title():
    item = _make_item("My Title", summary="")
    assert _extractive_summary(item) == "My Title"


@pytest.mark.parametrize("title,clickbait", [
    ("You won't believe what happened next", True),
    ("Python 3.12 release notes", False),
    ("Shocking discovery stuns scientists", True),
    ("Warsaw stock market update", False),
])
def test_detect_clickbait(title, clickbait):
    item = _make_item(title)
    score = _detect_clickbait(item)
    if clickbait:
        assert score > 0
    else:
        assert score == 0.0


@pytest.mark.asyncio
async def test_summarise_items_no_api_key():
    """Without an API key, items should get extractive summaries."""
    from mcp_server.processing.summarizer import summarise_items

    items = [
        _make_item("Python released", summary="Python 3.12 is out. It is faster. New syntax."),
        _make_item("OpenAI news", summary="GPT-5 announced. Available next month."),
    ]
    result = await summarise_items(items, openai_api_key="")
    assert all(i.llm_summary for i in result)
    assert result[0].llm_summary == "Python 3.12 is out. It is faster."


@pytest.mark.asyncio
async def test_generate_daily_digest_no_api_key():
    from mcp_server.processing.summarizer import generate_daily_digest

    items = [_make_item("Test story", summary="This is a test.")]
    items[0].llm_summary = "Test story summary."
    digest = await generate_daily_digest(items, openai_api_key="")
    assert "Today's Digest" in digest
    assert "Test story summary." in digest
