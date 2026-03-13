"""Per-user priority scoring for feed items.

Items authored by configured "priority authors" (e.g. friends, trusted
journalists) or tagged with "priority tags" (e.g. local community topics)
receive a score boost so that they float to the top of the feed when items
are sorted by score.

Configuration (via environment variables / .env):
  PRIORITY_AUTHORS  – comma-separated list of author names/handles to boost
  PRIORITY_TAGS     – comma-separated list of tags to boost
  PRIORITY_BOOST    – integer score added per matching criterion (default 100)
"""

from __future__ import annotations

import logging
from typing import Sequence

from mcp_server.feeds.base import FeedItem

logger = logging.getLogger(__name__)


def apply_priority_scores(
    items: Sequence[FeedItem],
    priority_authors: Sequence[str],
    priority_tags: Sequence[str],
    boost: int = 100,
) -> list[FeedItem]:
    """Boost the score of items that match priority authors or tags.

    Each matching criterion (author match, tag match) adds *boost* points to
    the item's score.  Multiple criteria can apply to the same item, stacking
    the boost.

    Args:
        items:            Feed items to process (modified in-place).
        priority_authors: Author names/handles that should be boosted.
                          Comparison is case-insensitive.
        priority_tags:    Tags that should be boosted.
                          Comparison is case-insensitive.
        boost:            Score points added per matching criterion.

    Returns:
        The same list (items are mutated in-place and the list is returned for
        convenience).
    """
    author_set = {a.lower().lstrip("@") for a in priority_authors if a.strip()}
    tag_set = {t.lower() for t in priority_tags if t.strip()}

    if not author_set and not tag_set:
        return list(items)

    result = list(items)
    for item in result:
        item_author = item.author.lower().lstrip("@")
        if author_set and item_author and item_author in author_set:
            item.score += boost
            logger.debug(
                "Priority boost (+%d) for author '%s': %s", boost, item.author, item.title
            )

        if tag_set:
            item_tags = {t.lower() for t in item.tags}
            if item_tags & tag_set:
                item.score += boost
                logger.debug(
                    "Priority boost (+%d) for tags %s: %s",
                    boost,
                    item_tags & tag_set,
                    item.title,
                )

    return result
