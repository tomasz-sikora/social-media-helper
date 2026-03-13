"""Social platform feed readers.

Supports:
  - Twitter/X via Nitter RSS (preferred) or RSSHub
  - Facebook public pages via RSSHub
  - LinkedIn public companies/profiles via RSSHub

All readers are thin wrappers around :class:`~mcp_server.feeds.rss_reader.RssFeedReader`
that build the correct feed URL from a configurable base URL and an account
identifier (username, page slug, etc.).

Configuration (via environment variables / .env):
  NITTER_BASE_URL      – base URL of a Nitter instance, e.g. https://nitter.net
  RSSHUB_BASE_URL      – base URL of an RSSHub instance, e.g. https://rsshub.app
  TWITTER_ACCOUNTS     – comma-separated Twitter/X usernames
  FACEBOOK_PAGES       – comma-separated Facebook page names
  LINKEDIN_COMPANIES   – comma-separated LinkedIn company slugs

Why RSS bridges instead of a custom crawler?
  Official APIs for Twitter, Facebook, and LinkedIn are heavily gated (expensive
  or approval-required). Nitter and RSSHub provide lightweight RSS interfaces
  for *public* content without requiring authentication.  For private/non-public
  content a headless-browser or Android-emulator crawler would be needed – that
  is a separate Stage-3+ concern tracked in PLAN.md.
"""

from __future__ import annotations

import logging
from typing import Sequence

from mcp_server.feeds.base import BaseFeedReader, FeedItem
from mcp_server.feeds.rss_reader import RssFeedReader

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Twitter / X
# ---------------------------------------------------------------------------


class TwitterNitterReader(BaseFeedReader):
    """Fetch a Twitter/X user timeline via Nitter RSS or RSSHub.

    Resolution order:
    1. Nitter RSS  – ``{nitter_base_url}/{username}/rss``
    2. RSSHub      – ``{rsshub_base_url}/twitter/user/{username}``

    At least one of *nitter_base_url* or *rsshub_base_url* must be provided;
    otherwise no items are returned and a warning is emitted.
    """

    def __init__(
        self,
        username: str,
        nitter_base_url: str = "",
        rsshub_base_url: str = "",
    ) -> None:
        self._username = username.lstrip("@")
        self._nitter_base_url = nitter_base_url.rstrip("/")
        self._rsshub_base_url = rsshub_base_url.rstrip("/")
        self._delegate: RssFeedReader | None = self._build_delegate()

    def _build_delegate(self) -> RssFeedReader | None:
        if self._nitter_base_url:
            url = f"{self._nitter_base_url}/{self._username}/rss"
            return RssFeedReader(url, extra_tags=["twitter", "social"])
        if self._rsshub_base_url:
            url = f"{self._rsshub_base_url}/twitter/user/{self._username}"
            return RssFeedReader(url, extra_tags=["twitter", "social"])
        return None

    @property
    def source_name(self) -> str:
        return f"twitter/@{self._username}"

    async def fetch(self) -> list[FeedItem]:
        if self._delegate is None:
            logger.warning(
                "TwitterNitterReader: no nitter_base_url or rsshub_base_url configured "
                "for @%s – skipping",
                self._username,
            )
            return []
        items = await self._delegate.fetch()
        for item in items:
            item.source = self.source_name
            if "twitter" not in item.tags:
                item.tags.append("twitter")
        return items


# ---------------------------------------------------------------------------
# Facebook
# ---------------------------------------------------------------------------


class FacebookRSSHubReader(BaseFeedReader):
    """Fetch a Facebook public page feed via RSSHub.

    Feed URL pattern: ``{rsshub_base_url}/facebook/page/{page_name}``
    """

    def __init__(self, page_name: str, rsshub_base_url: str) -> None:
        self._page_name = page_name
        self._rsshub_base_url = rsshub_base_url.rstrip("/")
        self._delegate: RssFeedReader | None = self._build_delegate()

    def _build_delegate(self) -> RssFeedReader | None:
        if not self._rsshub_base_url:
            return None
        url = f"{self._rsshub_base_url}/facebook/page/{self._page_name}"
        return RssFeedReader(url, extra_tags=["facebook", "social"])

    @property
    def source_name(self) -> str:
        return f"facebook/{self._page_name}"

    async def fetch(self) -> list[FeedItem]:
        if self._delegate is None:
            logger.warning(
                "FacebookRSSHubReader: no rsshub_base_url configured for page '%s' – skipping",
                self._page_name,
            )
            return []
        items = await self._delegate.fetch()
        for item in items:
            item.source = self.source_name
            if "facebook" not in item.tags:
                item.tags.append("facebook")
        return items


# ---------------------------------------------------------------------------
# LinkedIn
# ---------------------------------------------------------------------------


class LinkedInRSSHubReader(BaseFeedReader):
    """Fetch a LinkedIn public company/profile feed via RSSHub.

    Feed URL pattern: ``{rsshub_base_url}/linkedin/company/{company_slug}``
    """

    def __init__(self, company_slug: str, rsshub_base_url: str) -> None:
        self._company_slug = company_slug
        self._rsshub_base_url = rsshub_base_url.rstrip("/")
        self._delegate: RssFeedReader | None = self._build_delegate()

    def _build_delegate(self) -> RssFeedReader | None:
        if not self._rsshub_base_url:
            return None
        url = f"{self._rsshub_base_url}/linkedin/company/{self._company_slug}"
        return RssFeedReader(url, extra_tags=["linkedin", "social"])

    @property
    def source_name(self) -> str:
        return f"linkedin/{self._company_slug}"

    async def fetch(self) -> list[FeedItem]:
        if self._delegate is None:
            logger.warning(
                "LinkedInRSSHubReader: no rsshub_base_url configured for '%s' – skipping",
                self._company_slug,
            )
            return []
        items = await self._delegate.fetch()
        for item in items:
            item.source = self.source_name
            if "linkedin" not in item.tags:
                item.tags.append("linkedin")
        return items


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------


def get_social_readers(
    twitter_accounts: Sequence[str],
    facebook_pages: Sequence[str],
    linkedin_companies: Sequence[str],
    nitter_base_url: str = "",
    rsshub_base_url: str = "",
) -> list[BaseFeedReader]:
    """Return a list of configured social platform feed readers.

    Only readers for which at least one account/page is configured *and* the
    required base URL is set will be included.
    """
    readers: list[BaseFeedReader] = []

    for username in twitter_accounts:
        username = username.strip()
        if username:
            readers.append(
                TwitterNitterReader(
                    username,
                    nitter_base_url=nitter_base_url,
                    rsshub_base_url=rsshub_base_url,
                )
            )

    for page in facebook_pages:
        page = page.strip()
        if page and rsshub_base_url:
            readers.append(FacebookRSSHubReader(page, rsshub_base_url=rsshub_base_url))

    for company in linkedin_companies:
        company = company.strip()
        if company and rsshub_base_url:
            readers.append(LinkedInRSSHubReader(company, rsshub_base_url=rsshub_base_url))

    return readers
