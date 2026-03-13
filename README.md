# Social Media Helper

> **Stop doom-scrolling. Get one curated stream.**

Aggregates news from HackerNews, onet.pl and other RSS sources, deduplicates related stories, flags clickbait and fake-news patterns, and produces a concise daily digest — powered by an LLM.

See [PLAN.md](PLAN.md) for the full architecture, decision log and roadmap.

---

## Architecture

```
┌─────────────────────────────────────────────┐
│              Backend (Python)                │
│                                              │
│  ┌──────────────┐   ┌──────────────────────┐│
│  │  Feed fetchers│   │  Processing pipeline  ││
│  │  · HackerNews │   │  · Deduplication      ││
│  │  · onet.pl    │──▶│  · Categorisation     ││
│  │  · RSS feeds  │   │  · LLM summarisation  ││
│  └──────────────┘   └──────────┬───────────┘│
│                                 │             │
│          ┌──────────────────────┴──────────┐  │
│          │   FastAPI REST API  /api/feed    │  │
│          │   MCP server tools  (stdio)      │  │
│          └─────────────────────────────────┘  │
└─────────────────────────────────────────────┘
                        │
          ┌─────────────┴──────────────┐
          │                            │
   Android app (Kotlin)        LLM Agent (Claude/
   RecyclerView feed            ChatGPT via MCP)
```

---

## Quick Start

### 1. Backend

```bash
cd backend
cp .env.example .env   # add your OPENAI_API_KEY
pip install -r requirements.txt

# REST API server (for Android app)
python -m mcp_server.main

# MCP stdio server (for Claude Desktop / other LLM agents)
python -m mcp_server.main --mcp
```

Or with Docker:

```bash
cd backend
docker-compose up
```

API available at `http://localhost:8000`.  
Swagger docs at `http://localhost:8000/docs`.

### 2. Android App

Open `android/` in Android Studio. The app expects the backend at
`http://10.0.2.2:8000` (Android emulator localhost). For physical devices
update `BACKEND_URL` in `app/build.gradle.kts`.

```bash
cd android
./gradlew assembleDebug
```

### 3. MCP with Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "social-media-helper": {
      "command": "python",
      "args": ["-m", "mcp_server.main", "--mcp"],
      "cwd": "/path/to/social-media-helper/backend"
    }
  }
}
```

Available tools: `get_feed`, `get_digest`, `get_categories`, `get_items_by_category`.

---

## Configuration

All settings are read from environment variables or a `backend/.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | *(empty)* | OpenAI key; falls back to extractive summaries if not set |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model for summarisation |
| `HACKERNEWS_TOP_N` | `30` | Number of HN top stories to fetch |
| `CACHE_TTL_SECONDS` | `900` | How long to cache processed feed |
| `DEDUP_SIMILARITY_THRESHOLD` | `0.85` | Cosine similarity threshold for deduplication |
| `PORT` | `8000` | REST API port |

---

## Development

### Run backend tests

```bash
cd backend
pytest tests/ -v
```

### Lint

```bash
cd backend
ruff check mcp_server/ tests/
```

### Build with Bazel (Python backend)

```bash
bazel test //backend:backend_tests
```

---

## CI / CD

- **CI** (`.github/workflows/ci.yml`) – runs on every push/PR: lints Python, runs pytest, builds Android debug APK.
- **Release** (`.github/workflows/release.yml`) – triggered manually via `workflow_dispatch`; builds a signed release APK and attaches it as a GitHub Release artifact.

Both workflows target a **self-hosted** runner (label `self-hosted`).
