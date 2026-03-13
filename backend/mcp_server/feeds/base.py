"""Base data model and abstract feed reader."""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class FeedItem:
    """A single item fetched from any feed source."""

    title: str
    url: str
    source: str
    published_at: datetime
    summary: str = ""
    author: str = ""
    tags: list[str] = field(default_factory=list)
    score: int = 0  # engagement score where available (e.g. HN points)
    category: str = "general"
    # filled during processing
    dedup_cluster: Optional[str] = None
    llm_summary: str = ""
    clickbait_score: float = 0.0  # 0 = not clickbait, 1 = definitely clickbait

    @property
    def id(self) -> str:
        """Stable identifier derived from the canonical URL."""
        return hashlib.sha256(self.url.encode()).hexdigest()[:16]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "published_at": self.published_at.isoformat(),
            "summary": self.summary,
            "author": self.author,
            "tags": self.tags,
            "score": self.score,
            "category": self.category,
            "dedup_cluster": self.dedup_cluster,
            "llm_summary": self.llm_summary,
            "clickbait_score": self.clickbait_score,
        }


class BaseFeedReader(ABC):
    """Abstract base class for all feed readers."""

    @abstractmethod
    async def fetch(self) -> list[FeedItem]:
        """Fetch and return a list of FeedItems."""
        ...

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Human-readable source identifier."""
        ...
