# Social Media Helper – Project Plan

## Vision

A tool that eliminates doom-scrolling by aggregating, deduplicating, and summarising recent news from social media and news sources into a single curated feed. The user reads one clean stream instead of scrolling through ads and clickbait.

---

## Architecture Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | **MCP Server** (Python) as primary backend interface | Allows any LLM agent (Claude, ChatGPT via plugins) to consume the feed as tools, keeping the backend agnostic of the UI |
| 2 | **FastAPI REST API** in the same process | Enables the Android app to query the same backend without LLM involvement |
| 3 | **HackerNews official API** for HN feeds | Free, no auth required, JSON |
| 4 | **RSS/Atom** for onet.pl and other news | onet.pl exposes RSS; generic RSS reader covers many sources |
| 5 | **Social platforms (FB, X, LinkedIn)** via RSS bridges or Nitter | Official APIs are gated/paid; RSS bridges (nitter for X, rss.app, rsshub) provide RSS without auth for public feeds |
| 6 | **OpenAI API** for summarisation, fact-checking, clickbait detection | Configurable; supports any OpenAI-compatible endpoint |
| 7 | **Android native app** (Kotlin) | Runs on Android; no backend dependency for browsing cached summaries |
| 8 | **Bazel** as the mono-repo build/test tool | Single build graph across Python + Android; rules_python + rules_android |
| 9 | **Docker / docker-compose** for backend | Self-contained deployment; no host dependencies |
| 10 | **Self-hosted GitHub runner** for CI | Defined in workflow; runner label `self-hosted` |
| 11 | **Manual release workflow** builds APK | Triggered via `workflow_dispatch`; APK attached as release artifact |

---

## Monorepo Layout

```
social-media-helper/
├── .bazelversion          # pins Bazel version
├── .bazelrc               # common Bazel flags
├── MODULE.bazel           # Bazel module dependencies
├── WORKSPACE              # legacy workspace (kept for compatibility)
├── BUILD                  # root build file
├── PLAN.md                # this file
├── README.md
├── .github/
│   └── workflows/
│       ├── ci.yml         # lint + test on push/PR
│       └── release.yml    # manual APK release
├── backend/
│   ├── BUILD.bazel
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── requirements.txt
│   ├── mcp_server/
│   │   ├── main.py        # FastAPI app + MCP server entry
│   │   ├── config.py
│   │   ├── feeds/         # feed fetchers
│   │   ├── processing/    # dedup, categorise, summarise
│   │   ├── api/           # REST routes
│   │   └── mcp/           # MCP tool definitions
│   └── tests/
└── android/
    ├── BUILD.bazel
    ├── settings.gradle.kts
    ├── build.gradle.kts
    └── app/
        ├── build.gradle.kts
        └── src/
```

---

## Stages

### Stage 1 – Foundation (current) ✅
- Monorepo skeleton with Bazel
- Backend: feed fetchers for HackerNews + RSS (onet.pl, generic)
- Backend: deduplication, categorisation, OpenAI summarisation
- Backend: FastAPI REST API + MCP server
- Android app: Kotlin skeleton, feed list + detail screen
- CI workflow (lint + pytest)
- Manual release workflow (APK artifact)

### Stage 2 – Social Platform Integration ✅
- X (Twitter) via Nitter RSS (primary) or RSSHub (fallback) – `TwitterNitterReader`
- Facebook public pages via RSSHub – `FacebookRSSHubReader`
- LinkedIn public companies via RSSHub – `LinkedInRSSHubReader`
- Per-user priority scoring (friends / local community tags) – `apply_priority_scores`

> **Note – RSSHub vs custom crawler:**  RSSHub and Nitter cover *public* content
> without authentication and are the pragmatic choice for Stage 2.  For access to
> private/non-public posts (e.g. friends-only Facebook posts, private Twitter feeds)
> a headless-browser crawler or Android-emulator approach would be required.  That
> path carries significant maintenance burden (anti-bot measures, ToS risks) and is
> therefore deferred to a future stage when the value is clear.

### Stage 3 – Enhanced Intelligence
- Sentence-transformer based semantic deduplication (cluster-level)
- Fact-checking pipeline (cross-reference multiple sources)
- Clickbait score using fine-tuned classifier
- Personalisation: user interest vector stored locally

### Stage 4 – Offline / Privacy-First
- On-device summarisation option (llama.cpp via JNI on Android)
- Local vector store for deduplication without cloud
- Scheduled background sync with WorkManager

---

## Progress Log

| Date | Change |
|------|--------|
| 2026-03-13 | Repository created, initial plan committed |
| 2026-03-13 | Stage 1 implementation: backend (MCP+REST), Android app, Bazel, CI/CD |
| 2026-03-13 | Stage 2 implementation: Twitter/Nitter, Facebook/RSSHub, LinkedIn/RSSHub, priority scoring |
