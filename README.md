# 🎬 Cinema Manager - Hermes Skill

A [Hermes Agent](https://github.com/nousresearch/hermes-agent) skill for automated movie/TV resource search, Quark cloud drive save, and media library management with auto genre classification.

## Features

- 🔍 **Multi-site search** — plugin system, add any resource site
- 📊 **Quality scoring** — auto-ranks by resolution, source, HDR, audio, codec, subtitles
- ☁️ **Quark save** — one-click save to your Quark cloud drive
- 🎭 **Genre auto-classification** — OMDB API or resource site scraping, with local cache
- 📁 **Library management** — auto-organize files for Infuse/Plex/Jellyfin

## Quick Start

```bash
git clone https://github.com/249695811/cinema-manager.git ~/.hermes/skills/cinema-manager
pip install httpx
python3 ~/.hermes/skills/cinema-manager/scripts/setup.py
```

The setup wizard will guide you through:

1. **夸克网盘登录** — 账号密码（推荐）或 Cookie
2. **资源站选择** — wp365（免费）或 mini4k（需会员）
3. **自动分类** — OMDB API（推荐）/ 资源站抓取 / 关闭
4. **保存目录** — 夸克网盘中的文件夹名

## Usage

### Via Hermes Agent

Just tell your agent:
- "我要看星际穿越"
- "搜一下流浪地球2"
- "帮我整理一下夸克网盘里的影视资源"

### CLI

```bash
python3 scripts/cinema.py search "流浪地球"        # Search
python3 scripts/cinema.py auto "星际穿越"           # Search + save + organize
python3 scripts/cinema.py save "https://pan.quark.cn/s/xxx"  # Save a link
python3 scripts/cinema.py organize <fid> "电影名" --type movie  # Organize
python3 scripts/cinema.py plugins                    # List plugins
```

## Configuration

Edit `config.json` (created by setup wizard):

```json
{
  "quark": {
    "username": "your_phone_or_email",
    "password": "your_password"
  },
  "plugins": {
    "wp365": { "enabled": true },
    "mini4k": { "enabled": false, "username": "", "password": "" }
  },
  "save_folder": "夸克影视",
  "omdb_api_key": ""
}
```

### Quark Auth

| Method | Pros | Cons |
|--------|------|------|
| `username` + `password` | Auto-refreshes | Need account |
| `cookie` | No account needed | Expires ~7 days |

### Resource Plugins

| Plugin | Auth | Notes |
|--------|------|-------|
| `wp365` | No | Free aggregation, quark + baidu links |
| `mini4k` | Paid | Premium 4K resources, best genre data |

### Genre Classification

Three modes:

| Mode | Config | Accuracy | Cost |
|------|--------|----------|------|
| OMDB API | `"omdb_api_key": "your_key"` | High | Free, 1000 req/day |
| Resource scrape | `"omdb_api_key": ""` + mini4k enabled | Medium | Free |
| Disabled | `"omdb_api_key": ""`, no mini4k | N/A | Free |

Get a free OMDB key at [omdbapi.com/apikey.aspx](http://www.omdbapi.com/apikey.aspx) — just enter your email.

Genre results cached in `scripts/genre_cache.json`.

## Library Structure

```
夸克影视/
├── 动作/
│   └── 金谍行动 (2026)/
│       └── In.the.Grey.2026.2160p.WEB-DL.mkv
├── 剧情/
│   └── 大濛 (2025)/
│       └── A.Foggy.Tale.2025.1080p.NF.WEB-DL.mkv
├── 科幻/
│   └── 流浪地球2 (2023)/
│       └── 流浪地球2 (2023).mkv
└── 其他/
    └── 未识别类型的电影 (2024)/

夸克影视/剧情/百年孤独/     ← TV shows
├── Season 01/
│   ├── 百年孤独 - S01E01.mkv
│   └── 百年孤独 - S01E02.mkv
```

Infuse/Plex compatible naming:
- Movie: `Movie Name (Year).ext`
- TV: `Show Name/Season XX/Show Name - SXXEXX.ext`

## Adding Resource Sites

```bash
cp scripts/plugins/example.py scripts/plugins/your_site.py
```

```python
from plugins import ResourcePlugin, ResourceResult

class Plugin(ResourcePlugin):
    name = "your_site"
    display_name = "Your Site Name"
    requires_auth = False
    url = "https://your-site.com"

    def search(self, query: str, page: int = 1) -> list[ResourceResult]:
        ...
    def extract_link(self, resource: ResourceResult) -> str | None:
        ...
```

Enable: `{ "plugins": { "your_site": { "enabled": true } } }`

## Quality Scoring

| Factor | Best | Worst |
|--------|------|-------|
| Resolution | 2160p/4K (+100) | 480p (+5) |
| Source | BluRay/REMUX (+90) | CAM (+5) |
| HDR | Dolby Vision (+30) | None (0) |
| Audio | Atmos/TrueHD (+15) | AAC (+2) |
| Codec | H.265/HEVC (+10) | H.264 (+5) |
| Subtitles | Included (+5) | None (0) |
| Platform | Quark (+15) | Baidu (0) |

## License

MIT
