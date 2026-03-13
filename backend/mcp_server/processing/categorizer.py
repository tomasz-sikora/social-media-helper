"""Keyword-based categorisation of feed items.

Categories: tech, news, business, sport, science, entertainment, general.
"""

from __future__ import annotations

import re
from typing import Sequence

from mcp_server.feeds.base import FeedItem

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "tech": [
        "software", "hardware", "ai", "llm", "machine learning", "programming",
        "python", "javascript", "linux", "open source", "github", "developer",
        "startup", "cloud", "kubernetes", "docker", "api", "cybersecurity",
        "hack", "exploit", "vulnerability", "algorithm", "neural", "gpt",
        "technolog",  # covers Polish "technologia/technologie"
    ],
    "business": [
        "market", "stock", "invest", "economy", "financial", "bank", "revenue",
        "profit", "merger", "acquisition", "ipo", "venture", "fund",
        "biznes", "gospodark", "rynek",
    ],
    "science": [
        "research", "study", "science", "physics", "biology", "chemistry",
        "space", "nasa", "astronomy", "climate", "covid", "vaccine", "health",
        "medical", "nauka",
    ],
    "sport": [
        "football", "soccer", "basketball", "tennis", "olympic", "champion",
        "league", "match", "player", "sport", "fifa", "nba", "nfl",
        "piłka", "mecz", "sport",
    ],
    "entertainment": [
        "movie", "music", "film", "actor", "director", "album", "concert",
        "celebrity", "award", "oscar", "grammy", "netflix", "streaming",
        "kultura",
    ],
    "news": [
        "politics", "government", "election", "president", "minister", "war",
        "conflict", "protest", "law", "court", "police", "crime",
        "polska", "poland", "europe", "polityk", "wybor",
    ],
}


def _text_for_item(item: FeedItem) -> str:
    return " ".join([item.title, item.summary, " ".join(item.tags)]).lower()


def categorise(item: FeedItem) -> str:
    """Return the best matching category for the item."""
    # If already set to something specific, honour it unless it's 'general'
    if item.category and item.category != "general":
        return item.category

    text = _text_for_item(item)
    scores: dict[str, int] = {cat: 0 for cat in CATEGORY_KEYWORDS}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if re.search(r"\b" + re.escape(kw), text):
                scores[cat] += 1

    best_cat = max(scores, key=lambda c: scores[c])
    if scores[best_cat] == 0:
        return "general"
    return best_cat


def categorise_items(items: Sequence[FeedItem]) -> list[FeedItem]:
    """Categorise all items in-place and return them."""
    for item in items:
        item.category = categorise(item)
    return list(items)
