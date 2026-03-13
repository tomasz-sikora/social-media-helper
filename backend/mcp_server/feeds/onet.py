"""Onet.pl news feed reader (Polish news portal).

Onet exposes a standard RSS feed, so this is a thin wrapper around
RssFeedReader with onet-specific defaults and category mapping.
"""

from __future__ import annotations

from mcp_server.feeds.rss_reader import RssFeedReader

ONET_RSS_FEEDS: dict[str, str] = {
    "onet.pl/wiadomosci": "https://wiadomosci.onet.pl/rss.xml",
    "onet.pl/sport": "https://sport.onet.pl/rss.xml",
    "onet.pl/tech": "https://technologie.onet.pl/rss.xml",
    "onet.pl/biznes": "https://biznes.onet.pl/rss.xml",
}


def get_onet_readers(sections: list[str] | None = None) -> list[RssFeedReader]:
    """Return RssFeedReader instances for the requested Onet sections.

    If *sections* is None, all sections are returned.
    """
    selected = sections or list(ONET_RSS_FEEDS.keys())
    readers = []
    for key in selected:
        url = ONET_RSS_FEEDS.get(key)
        if url:
            readers.append(RssFeedReader(url, extra_tags=["poland", "onet"]))
    return readers
