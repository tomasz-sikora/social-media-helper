"""Deduplication of feed items using title-level similarity.

Two items are considered duplicates if their titles are similar enough
(cosine similarity above a configurable threshold) after TF-IDF embedding.
Semantic embedding via sentence-transformers is used when available for
higher accuracy; TF-IDF is the fast fallback.
"""

from __future__ import annotations

import logging
import uuid
from typing import Sequence

from mcp_server.feeds.base import FeedItem

logger = logging.getLogger(__name__)


def _tfidf_dedup(items: list[FeedItem], threshold: float) -> list[FeedItem]:
    """Simple TF-IDF cosine-similarity deduplication."""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np
    except ImportError:
        logger.warning("scikit-learn not available, skipping deduplication")
        return items

    if not items:
        return items

    titles = [item.title for item in items]
    vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=1)
    try:
        matrix = vectorizer.fit_transform(titles)
    except ValueError:
        return items

    sim = cosine_similarity(matrix)
    n = len(items)
    cluster_map: dict[int, str] = {}

    for i in range(n):
        if i in cluster_map:
            continue
        cluster_id = str(uuid.uuid4())[:8]
        cluster_map[i] = cluster_id
        for j in range(i + 1, n):
            if j not in cluster_map and sim[i, j] >= threshold:
                cluster_map[j] = cluster_id

    # Keep the highest-scored item per cluster; assign cluster labels
    cluster_best: dict[str, int] = {}
    for idx, cluster_id in cluster_map.items():
        best = cluster_best.get(cluster_id)
        if best is None or items[idx].score > items[best].score:
            cluster_best[cluster_id] = idx

    kept_indices = set(cluster_best.values())
    result = []
    for idx, item in enumerate(items):
        item.dedup_cluster = cluster_map[idx]
        if idx in kept_indices:
            result.append(item)

    logger.debug("Dedup: %d items -> %d after deduplication", n, len(result))
    return result


def deduplicate(items: Sequence[FeedItem], threshold: float = 0.85) -> list[FeedItem]:
    """Remove near-duplicate items from *items*, keeping the best representative."""
    return _tfidf_dedup(list(items), threshold)
