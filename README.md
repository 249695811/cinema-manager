# 🎬 Cinema Manager - Hermes Skill

A [Hermes Agent](https://github.com/nousresearch/hermes-agent) skill for automated movie/TV resource search, Quark cloud drive save, and media library management.

## Features

- 🔍 **Multi-site search** — plugin system, add any resource site
- 📊 **Quality scoring** — auto-ranks by resolution, source, HDR, audio, codec, subtitles
- ☁️ **Quark save** — one-click save to your Quark cloud drive
- 📁 **Library management** — auto-organize files for Infuse/Plex/Jellyfin

## Installation

```bash
git clone https://github.com/249695811/cinema-manager.git ~/.hermes/skills/cinema-manager
pip install httpx
cp ~/.hermes/skills/cinema-manager/config.example.json ~/.hermes/skills/cinema-manager/config.json
```

## Configuration

Edit `config.json`:

```json
{
  "quark": {
    "username": "your_phone_or_email",
    "password": "your_password"
  },
  "plugins": {
    "wp365": { "enabled": true }
  },
  "save_folder": "影视资源"
}
```

**Quark auth** — pick one:
- `username` + `password` — auto-login, recommended
- `cookie` — manual, expires periodically

## Usage

### CLI

```bash
# Search
python3 scripts/cinema.py search "流浪地球"

# Auto search + save + organize
python3 scripts/cinema.py auto "星际穿越"

# Save a specific link
python3 scripts/cinema.py save "https://pan.quark.cn/s/xxx"

# Organize a saved file into library
python3 scripts/cinema.py organize <file_id> "电影名" --type movie
python3 scripts/cinema.py organize <file_id> "剧名" --type tv --season 1 --episode 3

# List plugins
python3 scripts/cinema.py plugins
```

### Via Hermes Agent

Just tell your agent:
- "搜一下流浪地球2"
- "我要看星际穿越"
- "帮我整理一下夸克网盘里的影视资源"

## Adding Resource Sites

This is a **plugin system**. To add your own resource site:

```bash
cp scripts/plugins/example.py scripts/plugins/your_site.py
```

Implement two methods:

```python
from plugins import ResourcePlugin, ResourceResult

class Plugin(ResourcePlugin):
    name = "your_site"
    display_name = "Your Site Name"
    requires_auth = False  # True if login needed
    url = "https://your-site.com"

    def search(self, query: str, page: int = 1) -> list[ResourceResult]:
        """Search for resources. Return list of ResourceResult."""
        # Call your site's search API
        # Return ResourceResult(title=..., source="quark", url=..., site=self.name)
        ...

    def extract_link(self, resource: ResourceResult) -> str | None:
        """Extract actual Quark share URL from search result."""
        # If search() returns direct links, return resource.url
        # Otherwise, call your site's extraction API
        ...
```

Then enable in `config.json`:
```json
{ "plugins": { "your_site": { "enabled": true } } }
```

See [`scripts/plugins/example.py`](scripts/plugins/example.py) for a full template.

## Library Management

After saving files to Quark, the library manager organizes them for media players:

```
影视资源/
├── 星际穿越 (2014)/
│   └── 星际穿越 (2014).mkv
├── 流浪地球2 (2023)/
│   └── 流浪地球2 (2023).mkv
└── 权力的游戏/
    ├── Season 01/
    │   ├── 权力的游戏 - S01E01.mkv
    │   └── 权力的游戏 - S01E02.mkv
    └── Season 02/
        └── ...
```

This naming convention works with:
- ✅ Infuse
- ✅ Plex
- ✅ Jellyfin
- ✅ Emby

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
