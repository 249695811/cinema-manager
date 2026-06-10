# 🎬 影视管理 - Hermes 技能

[Hermes Agent](https://github.com/nousresearch/hermes-agent) 技能，用于个人媒体库管理 — 内容发现、夸克网盘保存、自动分类整理。

## 功能特性

- 🔍 **多源搜索** — 插件系统，可添加任意内容源
- 📊 **质量评分** — 按分辨率、片源、HDR、音频、编码、字幕自动排序
- ☁️ **夸克网盘保存** — 一键保存到夸克网盘
- 🎭 **自动分类** — OMDB API 或内容源抓取，本地缓存
- 📁 **媒体库管理** — 自动整理为 Infuse/Plex/Jellyfin 兼容格式

## 快速开始

```bash
git clone https://github.com/249695811/cinema-manager.git ~/.hermes/skills/cinema-manager
pip install httpx
python3 ~/.hermes/skills/cinema-manager/scripts/setup.py
```

设置向导会引导你完成：
1. **夸克网盘登录** — 账号密码（推荐）或 Cookie
2. **内容源选择** — 自动检测已安装插件，逐个启用/禁用
3. **自动分类** — OMDB API（推荐）/ 内容源抓取 / 关闭
4. **保存目录** — 夸克网盘中的文件夹名

## 使用方法

### 通过 Hermes Agent

直接告诉你的助手：
- "我要看星际穿越"
- "搜一下流浪地球2"
- "帮我整理一下夸克网盘里的影视资源"

### 命令行

```bash
python3 scripts/cinema.py search "流浪地球"        # 搜索
python3 scripts/cinema.py auto "星际穿越"           # 搜索 + 保存 + 整理
python3 scripts/cinema.py save "https://pan.quark.cn/s/xxx"  # 保存链接
python3 scripts/cinema.py organize <fid> "电影名" --type movie  # 整理
python3 scripts/cinema.py plugins                    # 查看插件
python3 scripts/setup.py                             # 重新运行设置向导
```

## 配置说明

编辑 `config.json`（由设置向导创建）：

```json
{
  "quark": {
    "cookie": "从浏览器获取的cookie"
  },
  "plugins": {
    "wp365": { "enabled": true }
  },
  "save_folder": "夸克影视",
  "omdb_api_key": ""
}
```

### 夸克认证

登录 [pan.quark.cn](https://pan.quark.cn)，打开浏览器开发者工具（F12）→ Network 标签 → 随便点一个请求 → 复制 `Cookie` 请求头的值，粘贴到 `config.json` 的 `quark.cookie` 字段。

Cookie 约 7 天过期，过期后重新从浏览器复制即可。

### 自动分类

| 模式 | 配置 | 准确度 | 费用 |
|------|------|--------|------|
| OMDB API | `"omdb_api_key": "你的key"` | 高 | 免费，1000次/天 |
| 内容源抓取 | `"omdb_api_key": ""` | 中 | 免费 |
| 关闭 | （电影存入扁平结构） | 无 | 免费 |

在 [omdbapi.com/apikey.aspx](http://www.omdbapi.com/apikey.aspx) 免费获取 OMDB API Key，只需输入邮箱。

分类结果缓存在 `scripts/genre_cache.json`。

## 添加内容源

将 `.py` 插件文件放入 `scripts/plugins/` 目录：

```bash
cp scripts/plugins/example.py scripts/plugins/your_site.py
```

实现两个方法：

```python
from plugins import ResourcePlugin, ResourceResult

class Plugin(ResourcePlugin):
    name = "your_site"
    display_name = "你的站点名"
    requires_auth = False
    url = "https://your-site.com"

    def search(self, query: str, page: int = 1) -> list[ResourceResult]:
        ...
    def extract_link(self, resource: ResourceResult) -> str | None:
        ...
```

然后在 `config.json` 中启用，或重新运行 `setup.py`。详见 `scripts/plugins/example.py` 完整模板。

## 媒体库结构

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

Infuse/Plex 兼容命名：
- 电影：`电影名 (年份).扩展名`
- 电视剧：`剧名/Season XX/剧名 - SXXEXX.扩展名`

## 质量评分

| 因素 | 最佳 | 最差 |
|------|------|------|
| 分辨率 | 2160p/4K (+100) | 480p (+5) |
| 片源 | BluRay/REMUX (+90) | CAM (+5) |
| HDR | Dolby Vision (+30) | 无 (0) |
| 音频 | Atmos/TrueHD (+15) | AAC (+2) |
| 编码 | H.265/HEVC (+10) | H.264 (+5) |
| 字幕 | 包含 (+5) | 无 (0) |
| 平台 | 夸克 (+15) | 百度 (0) |

## 许可证

MIT
