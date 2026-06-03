# 🎬 Cinema Manager - Hermes Skill

A [Hermes Agent](https://github.com/nousresearch/hermes-agent) skill for automated movie/TV resource search and Quark cloud drive save.

## What It Does

1. **Search** resource sites for movies/TV shows
2. **Identify** the best quality version (4K BluRay > 1080p WEB-DL > ...)
3. **Save** to your Quark cloud drive automatically

Just tell your agent: *"I want to watch Interstellar"* and it handles the rest.

## Installation

### As a Hermes Skill

```bash
# Clone to your skills directory
git clone https://github.com/249695811/cinema-manager.git ~/.hermes/skills/cinema-manager

# Install Python dependency
pip install httpx
```

### Configuration

```bash
cp config.example.json config.json
# Edit config.json with your Quark credentials
```

**config.json**:
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
  "default_quality": "4k",
  "save_folder": "影视资源"
}
```

## Usage

### CLI

```bash
# Search across all enabled sites
python3 scripts/cinema.py search "速度与激情"

# Search + auto-save best quark version
python3 scripts/cinema.py auto "幽旅巫咒"

# Save a specific quark share link
python3 scripts/cinema.py save "https://pan.quark.cn/s/xxx"

# List configured plugins
python3 scripts/cinema.py plugins
```

### Via Hermes Agent

Just chat naturally:
- "帮我看一下幽旅巫咒"
- "我要看速度与激情10"
- "搜一下流浪地球2，转存到夸克"

The agent will search, rank results, ask for confirmation, and save.

## Resource Site Plugins

| Plugin | Site | Free? | Auth Required |
|--------|------|-------|---------------|
| `wp365` | [pan.365wp.top](https://pan.365wp.top) | ✅ Free | No |
| `mini4k` | [mini4k.net](https://www.mini4k.net) | 💰 Paid | Yes |

### Adding Custom Plugins

Create `scripts/plugins/your_site.py`:

```python
from .base import ResourcePlugin, ResourceResult

class MyPlugin(ResourcePlugin):
    name = "my_site"
    display_name = "My Resource Site"
    requires_auth = False

    def search(self, query: str) -> list[ResourceResult]:
        # Implement search logic
        pass

    def extract_link(self, resource: ResourceResult) -> str:
        # Return quark share URL
        pass
```

## Quality Scoring

Resources are scored by:

| Factor | Best | Worst |
|--------|------|-------|
| Resolution | 2160p/4K (+100) | 480p (+5) |
| Source | BluRay/REMUX (+90) | CAM (+5) |
| HDR | Dolby Vision (+30) | None (0) |
| Audio | Atmos/TrueHD (+15) | AAC (+2) |
| Codec | H.265/HEVC (+10) | H.264 (+5) |
| Subtitles | Included (+5) | None (0) |

## Quark Drive

Supports two auth methods:
- **Username + Password** (recommended): Auto-login, auto-refresh cookies
- **Cookie** (advanced): Manual, expires periodically

## License

MIT
