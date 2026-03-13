"""MCP tool definitions for the Social Media Helper.

Tools exposed to LLM agents:
  - get_feed          – fetch the processed news feed
  - get_digest        – get the LLM-generated daily digest
  - get_categories    – list available categories
  - get_items_by_category – filter items by category
"""

from __future__ import annotations

import json
import logging
from typing import Any

import mcp.server.stdio
import mcp.types as types
from mcp.server import Server

from mcp_server.api.routes import _get_processed_feed, generate_daily_digest
from mcp_server.config import settings

logger = logging.getLogger(__name__)

mcp_server = Server("social-media-helper")


# ---------------------------------------------------------------------------
# Tool list
# ---------------------------------------------------------------------------

@mcp_server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_feed",
            description=(
                "Fetch the latest aggregated news feed from HackerNews, onet.pl, and other "
                "configured sources. Items are deduplicated and categorised. Returns up to "
                "`limit` items starting at `offset`."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of items to return (1-100, default 20)",
                        "default": 20,
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Pagination offset (default 0)",
                        "default": 0,
                    },
                    "category": {
                        "type": "string",
                        "description": "Optional category filter (tech, news, business, science, sport, entertainment, general)",
                    },
                },
            },
        ),
        types.Tool(
            name="get_digest",
            description=(
                "Get a markdown-formatted daily digest of the most important stories, "
                "grouped by category. Clickbait items are flagged."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="get_categories",
            description="List all categories present in the current news feed.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="get_items_by_category",
            description="Return feed items filtered to a specific category.",
            inputSchema={
                "type": "object",
                "required": ["category"],
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Category name (e.g. tech, news, business)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum items to return (default 20)",
                        "default": 20,
                    },
                },
            },
        ),
    ]


# ---------------------------------------------------------------------------
# Tool call handler
# ---------------------------------------------------------------------------

@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    try:
        result = await _dispatch(name, arguments)
        return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
    except Exception as exc:
        logger.exception("MCP tool error")
        return [types.TextContent(type="text", text=json.dumps({"error": str(exc)}))]


async def _dispatch(name: str, args: dict[str, Any]) -> Any:
    items = await _get_processed_feed()

    if name == "get_feed":
        limit = int(args.get("limit", 20))
        offset = int(args.get("offset", 0))
        category = args.get("category")
        if category:
            items = [i for i in items if i.category == category]
        return {
            "total": len(items),
            "items": [i.to_dict() for i in items[offset : offset + limit]],
        }

    if name == "get_digest":
        digest = await generate_daily_digest(
            items,
            openai_api_key=settings.openai_api_key,
            openai_model=settings.openai_model,
            openai_base_url=settings.openai_base_url,
        )
        return {"digest": digest}

    if name == "get_categories":
        return {"categories": sorted({i.category for i in items})}

    if name == "get_items_by_category":
        category = args.get("category", "general")
        limit = int(args.get("limit", 20))
        filtered = [i for i in items if i.category == category]
        return {
            "category": category,
            "total": len(filtered),
            "items": [i.to_dict() for i in filtered[:limit]],
        }

    raise ValueError(f"Unknown tool: {name}")


async def run_stdio_server() -> None:
    """Run the MCP server over stdio (for use with Claude Desktop etc.)."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await mcp_server.run(
            read_stream,
            write_stream,
            mcp_server.create_initialization_options(),
        )
