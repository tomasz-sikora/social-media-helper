"""Entry point for the Social Media Helper backend.

Modes:
  python -m mcp_server.main           → starts the FastAPI REST server
  python -m mcp_server.main --mcp     → starts the MCP stdio server
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

import uvicorn
from fastapi import FastAPI

from mcp_server.api.routes import router
from mcp_server.config import settings

logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s %(levelname)s %(name)s – %(message)s",
)

app = FastAPI(
    title="Social Media Helper API",
    description=(
        "Aggregates, deduplicates and summarises news from HackerNews, "
        "onet.pl and other RSS sources."
    ),
    version="0.1.0",
)
app.include_router(router)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Social Media Helper backend")
    parser.add_argument(
        "--mcp",
        action="store_true",
        help="Run as an MCP stdio server instead of a REST HTTP server",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    if args.mcp:
        from mcp_server.mcp.tools import run_stdio_server

        asyncio.run(run_stdio_server())
    else:
        uvicorn.run(
            "mcp_server.main:app",
            host=settings.host,
            port=settings.port,
            log_level=settings.log_level,
            reload=False,
        )


if __name__ == "__main__":
    main(sys.argv[1:])
