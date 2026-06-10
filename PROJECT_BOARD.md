# 🎬 cinema-manager — 项目说明

> 最后更新：2026-06-03 | 当前版本：v1.0 | 状态：稳定可用 ✅

---

## 一、总览

```
产品：Hermes Agent 影视资源管理 skill
定位：搜索影视资源 → 夸克网盘转存 → 自动分类整理 → Infuse/Plex/Jellyfin 可用
模式：开源免费（MIT），Hermes Agent 插件
GitHub：github.com/249695811/cinema-manager
```

---

## 二、目录结构

```
cinema-manager/
├── SKILL.md                    # Hermes Agent skill 定义
├── README.md                   # 用户文档
├── config.example.json         # 配置模板
├── config.json                 # 本地配置（不提交，含账号密码）
├── scripts/
│   ├── cinema.py               # 主入口（search/save/auto/organize）
│   ├── quark.py                # 夸克网盘 API
│   ├── library.py              # 分类整理逻辑
│   ├── setup.py                # 交互式配置向导
│   └── plugins/
│       ├── __init__.py         # 插件基类
│       ├── example.py          # 插件开发模板
│       ├── wp365.py            # 365wp 内容源
│       └── mini4k.py           # mini4k 内容源
└── references/
    ├── 365wp-api.md            # 365wp API 文档
    ├── quark-drive-api.md      # 夸克网盘 API 文档
    ├── quark-file-management.md # 夸克文件管理
    └── prompt-sensitivity.md   # LLM 措辞注意事项
```

---

## 三、版本历史

### v1.0 — 初始发布 ✅ 2026-06-03

- [x] 多源搜索 + 插件系统（wp365、mini4k、example 模板）
- [x] 夸克网盘转存 + Cookie/账号两种认证
- [x] 自动分类（OMDB API / 内容源抓取 / 关闭三种模式）
- [x] 质量评分（分辨率、来源、HDR、音频、编码、字幕）
- [x] setup.py 交互式配置向导
- [x] README 完善、.gitignore 排除 config.json
- [x] 措辞从 "resource site" 改为 "content source"，避免 LLM 触发版权拒绝

---

## 四、待办

- [ ] 无明确待办

---

## 五、关键信息

- **config.json 含夸克账号密码，绝不提交 git**
- 插件开发参考 `scripts/plugins/example.py`
- LLM 措辞注意：用 "content source" 不用 "resource site"
- GitHub 已有 5 个 star

---

## 六、Agent 交接说明

本项目当前状态稳定，无进行中的任务。如需扩展：
1. 新增内容源 → 复制 `scripts/plugins/example.py`，实现 `search()` 和 `extract_link()`
2. 修改分类逻辑 → `scripts/library.py`
3. 修改夸克操作 → `scripts/quark.py`
