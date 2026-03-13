"""LLM-powered summarisation, clickbait detection and fact-check hints.

When OPENAI_API_KEY is not configured, the module falls back to a simple
extractive summary (first sentence of the item's existing summary text).
"""

from __future__ import annotations

import logging
import re
from typing import Sequence

from mcp_server.feeds.base import FeedItem

logger = logging.getLogger(__name__)

_CLICKBAIT_PATTERNS = re.compile(
    r"(you won'?t believe|shocking|jaw.?drop|unbeliev|mind.?blow|"
    r"this (one |simple )?(trick|hack)|number \d+ will|doctors hate|"
    r"click here|find out (now|why)|secret|amazing|incredible|"
    r"what happened next|go viral)",
    re.IGNORECASE,
)


def _extractive_summary(item: FeedItem) -> str:
    """Return first 1–2 sentences from the item's existing summary."""
    text = item.summary or item.title
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return " ".join(sentences[:2]) or item.title


def _detect_clickbait(item: FeedItem) -> float:
    """Heuristic clickbait score in [0, 1]."""
    text = item.title + " " + item.summary
    matches = len(_CLICKBAIT_PATTERNS.findall(text))
    return min(1.0, matches * 0.3)


async def _llm_summarise_batch(items: list[FeedItem], client, model: str) -> None:
    """Use OpenAI chat completion to summarise a batch of items."""
    if not items:
        return

    bullet_list = "\n".join(
        f"- [{i+1}] {item.title}: {item.summary[:300]}" for i, item in enumerate(items)
    )
    prompt = (
        "You are a journalist assistant. For each of the numbered articles below:\n"
        "1. Write a 1-sentence neutral summary.\n"
        "2. Give a clickbait score from 0 (not clickbait) to 10 (pure clickbait).\n"
        "3. Note any obvious factual red-flags (or 'none').\n\n"
        "Format each answer as: [N] SUMMARY | clickbait:SCORE | flags:FLAGS\n\n"
        f"{bullet_list}"
    )
    try:
        resp = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.2,
        )
        text = resp.choices[0].message.content or ""
    except Exception as exc:
        logger.warning("LLM summarise error: %s", exc)
        return

    for line in text.splitlines():
        m = re.match(r"\[(\d+)\]\s*(.*?)\s*\|\s*clickbait:(\d+)\s*\|\s*flags:(.*)", line)
        if not m:
            continue
        idx = int(m.group(1)) - 1
        if 0 <= idx < len(items):
            items[idx].llm_summary = m.group(2).strip()
            try:
                items[idx].clickbait_score = int(m.group(3)) / 10.0
            except ValueError:
                pass


async def summarise_items(
    items: Sequence[FeedItem],
    openai_api_key: str = "",
    openai_model: str = "gpt-4o-mini",
    openai_base_url: str = "https://api.openai.com/v1",
    batch_size: int = 20,
) -> list[FeedItem]:
    """Populate llm_summary and clickbait_score on each item.

    Falls back to extractive summary when no API key is configured.
    """
    result = list(items)

    # Always compute heuristic clickbait score
    for item in result:
        if item.clickbait_score == 0.0:
            item.clickbait_score = _detect_clickbait(item)

    if not openai_api_key:
        for item in result:
            if not item.llm_summary:
                item.llm_summary = _extractive_summary(item)
        return result

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=openai_api_key, base_url=openai_base_url)
    except ImportError:
        logger.warning("openai package not installed; using extractive summaries")
        for item in result:
            item.llm_summary = _extractive_summary(item)
        return result

    # Process in batches to stay within token limits
    for start in range(0, len(result), batch_size):
        batch = result[start : start + batch_size]
        await _llm_summarise_batch(batch, client, openai_model)
        # Fill extractive fallback for items that didn't get an LLM summary
        for item in batch:
            if not item.llm_summary:
                item.llm_summary = _extractive_summary(item)

    return result


async def generate_daily_digest(
    items: Sequence[FeedItem],
    openai_api_key: str = "",
    openai_model: str = "gpt-4o-mini",
    openai_base_url: str = "https://api.openai.com/v1",
) -> str:
    """Generate a markdown digest of the day's top stories."""
    if not items:
        return "No stories found."

    # Build a bullet list of already-summarised items
    bullets = "\n".join(
        f"- **{item.category.upper()}** – {item.llm_summary or item.title} ({item.source})"
        for item in items
    )

    if not openai_api_key:
        return f"## Today's Digest\n\n{bullets}"

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=openai_api_key, base_url=openai_base_url)
        resp = await client.chat.completions.create(
            model=openai_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a daily news editor. Write a concise markdown digest "
                        "grouping the stories by category. Remove duplicates. "
                        "Flag any clickbait or unverified claims."
                    ),
                },
                {"role": "user", "content": bullets},
            ],
            max_tokens=2000,
            temperature=0.3,
        )
        return resp.choices[0].message.content or bullets
    except Exception as exc:
        logger.warning("Digest generation error: %s", exc)
        return f"## Today's Digest\n\n{bullets}"
