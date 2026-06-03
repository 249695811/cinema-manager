---
name: cinema-manager
description: Search and save movie/TV resources to Quark cloud drive. Searches resource sites, identifies best quality version, and auto-saves to your drive. Use when user wants to find or watch movies/TV shows, or mentions "cinema", "movie search", "quark save", "影院", "看电影".
---

# Cinema Manager

Automated movie/TV resource search + Quark cloud drive save workflow.

## Quick Start

```bash
# Search for a movie
python3 scripts/cinema.py search "电影名"

# Search and auto-save best version
python3 scripts/cinema.py auto "电影名"

# List available plugins
python3 scripts/cinema.py plugins
```

## Config

Copy `config.example.json` to `config.json` and fill in:
- Quark credentials (username + password, or cookie)
- Resource site plugins to enable

## Workflow

1. User says "I want to watch [movie]"
2. Agent runs `cinema.py search` across enabled plugins
3. Results are ranked by quality (resolution, source, HDR, audio, codec, subtitles)
4. Agent presents top picks to user
5. User confirms → agent runs `cinema.py save <url>`
6. File saved to user's Quark drive

## Plugin System

Each resource site is a plugin in `scripts/plugins/`. To add a new site:
1. Create `scripts/plugins/your_site.py`
2. Inherit from `ResourcePlugin` (see `base.py`)
3. Implement `search()` and `extract_link()`
4. Add to config.json

## Quality Scoring

| Factor | High | Low |
|--------|------|-----|
| Resolution | 2160p/4K (+100) | 720p (+20) |
| Source | BluRay (+90) | CAM (+5) |
| HDR | Dolby Vision (+30) | HDR (+15) |
| Audio | Atmos (+15) | AAC (+2) |
| Codec | H.265 (+10) | H.264 (+5) |
| Subtitles | Yes (+5) | - |
