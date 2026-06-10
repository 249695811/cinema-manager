# 🎬 Cinema Manager - Hermes Skill

A [Hermes Agent](https://github.com/nousresearch/hermes-agent) skill for personal media library management — discover content, save to Quark cloud drive, and auto-organize with genre classification.

## Features

- 🔍 **Multi-source search** — plugin system, add any content source
- 📊 **Quality scoring** — auto-ranks by resolution, source, HDR, audio, codec, subtitles
- ☁️ **Quark save** — one-click save to your Quark cloud drive
- 🎭 **Genre auto-classification** — OMDB API or content source scraping, with local cache
- 📁 **Library management** — auto-organize files for Infuse/Plex/Jellyfin

## Quick Start

```bash
git clone https://github.com/249695811/cinema-manager.git ~/.hermes/skills/cinema-manager
pip install httpx
python3 ~/.hermes/skills/cinema-manager/scripts/setup.py
```

Setup wizard walks you through:
1. **夸克网盘登录** — 账号密码（推荐）或 Cookie
2. **内容源选择** — 自动检测已安装插件，逐个启用/禁用
3. **自动分类** — OMDB API（推荐）/ 内容源抓取 / 关闭
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
python3 scripts/setup.py                             # Re-run setup wizard
```

## Configuration

Edit `config.json` (created by setup wizard):

```json
{
  "quark": {
    "cookie": "your_cookie_from_browser"
  },
  "plugins": {
    "wp365": { "enabled": true }
  },
  "save_folder": "夸克影视",
  "omdb_api_key": ""
}
```

### Quark Auth

Login to [pan.quark.cn](https://pan.quark.cn), open browser DevTools (F12) → Network tab → copy the `Cookie` header value from any request. Paste it into `config.json` as `quark.cookie`.

Cookies expire after ~7 days. When expired, grab a fresh one from the browser.

### Genre Classification

| Mode | Config | Accuracy | Cost |
|------|--------|----------|------|
| OMDB API | `"omdb_api_key": "your_key"` | High | Free, 1000 req/day |
| Content scrape | `"omdb_api_key": ""` | Medium | Free |
| Disabled | (movies go to flat structure) | N/A | Free |

Get a free OMDB key at [omdbapi.com/apikey.aspx](http://www.omdbapi.com/apikey.aspx) — just enter your email.

Genre results cached in `scripts/genre_cache.json`.

## Adding Content Sources

Drop a `.py` plugin file into `scripts/plugins/`:

```bash
cp scripts/plugins/example.py scripts/plugins/your_site.py
```

Implement two methods:

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

Then enable in `config.json` or re-run `setup.py`. See `scripts/plugins/example.py` for a full template.

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
```

Infuse/Plex compatible naming:
- Movie: `Movie Name (Year).ext`
- TV: `Show Name/Season XX/Show Name - SXXEXX.ext`

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
