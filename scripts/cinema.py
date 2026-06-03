#!/usr/bin/env python3
"""
Cinema Manager - Search resource sites and save to Quark cloud drive.

Usage:
    cinema.py search <query>           Search all enabled plugins
    cinema.py save <quark_url>         Save a quark share link
    cinema.py auto <query>             Search + auto-save best version
    cinema.py organize <fid> <title>   Organize saved file into library
    cinema.py plugins                  List available plugins
"""

import json
import os
import sys
import importlib
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from plugins import ResourcePlugin, ResourceResult
from quark import QuarkClient
from library import LibraryManager

CONFIG_PATHS = [
    SCRIPT_DIR.parent / "config.json",
    Path.home() / ".cinema-manager" / "config.json",
]


def load_config() -> dict:
    for p in CONFIG_PATHS:
        if p.exists():
            with open(p) as f:
                return json.load(f)
    return {}


def load_plugins(config: dict) -> list:
    plugins = []
    plugin_configs = config.get("plugins", {})
    plugin_dir = SCRIPT_DIR / "plugins"

    for f in sorted(plugin_dir.glob("*.py")):
        if f.name.startswith("_") or f.name == "base.py":
            continue
        module_name = f.stem
        plugin_conf = plugin_configs.get(module_name, {})
        if not plugin_conf.get("enabled", True):
            continue
        try:
            mod = importlib.import_module(f"plugins.{module_name}")
            if hasattr(mod, "Plugin"):
                plugins.append(mod.Plugin(config=plugin_conf))
        except Exception as e:
            print(f"⚠️  Failed to load plugin {module_name}: {e}", file=sys.stderr)

    return plugins


def get_quark_client(config: dict) -> QuarkClient:
    quark_conf = config.get("quark", {})
    client = QuarkClient(
        username=quark_conf.get("username", ""),
        password=quark_conf.get("password", ""),
        cookie=quark_conf.get("cookie", ""),
    )
    if not client.cookie:
        client.login()
    return client


# ── Quality Scoring ──

QUALITY_SCORES = {"2160p": 100, "4k": 100, "uhd": 100, "1080p": 50, "1080i": 45, "720p": 20, "480p": 5}
SOURCE_SCORES = {"bluray": 90, "remux": 85, "bdrip": 80, "web-dl": 70, "webdl": 70, "webrip": 65, "hdtv": 40, "cam": 5}
HDR_SCORES = {"dolby.vision": 30, "dv": 30, "hdr10+": 25, "hdr10": 20, "hdr": 15}
AUDIO_SCORES = {"atmos": 15, "truehd": 12, "dts-hd": 10, "dts": 8, "eac3": 7, "ddp": 7, "ac3": 3, "aac": 2}
CODEC_SCORES = {"h265": 10, "hevc": 10, "x265": 10, "h264": 5, "x264": 5}
SUB_KW = ["字幕", "subtitle", "chs", "cht", "中英", "中字", "双语"]


def score_resource(res: ResourceResult) -> int:
    t = res.title.lower()
    s = 0
    for table in [QUALITY_SCORES, SOURCE_SCORES, HDR_SCORES, AUDIO_SCORES, CODEC_SCORES]:
        for k, v in table.items():
            if k in t:
                s += v
                break
    if any(kw in t for kw in SUB_KW):
        s += 5
    if res.source == "quark":
        s += 15
    return s


# ── Commands ──

def cmd_search(query: str, config: dict):
    plugins = load_plugins(config)
    if not plugins:
        print("❌ No plugins enabled. Edit config.json.")
        return []

    all_results = []
    for plugin in plugins:
        print(f"🔍 Searching {plugin.display_name}...", file=sys.stderr)
        try:
            results = plugin.search(query)
            for r in results:
                r.site = plugin.name
                r.extra["score"] = score_resource(r)
            all_results.extend(results)
        except Exception as e:
            print(f"⚠️  {plugin.name} error: {e}", file=sys.stderr)

    all_results.sort(key=lambda r: r.extra.get("score", 0), reverse=True)

    print(json.dumps([
        {"title": r.title, "source": r.source, "site": r.site,
         "score": r.extra.get("score", 0), "url": r.url[:80]}
        for r in all_results[:20]
    ], indent=2, ensure_ascii=False))
    return all_results


def cmd_save(share_url: str, config: dict, folder: str = ""):
    client = get_quark_client(config)
    print(f"☁️  Saving to Quark: {share_url}", file=sys.stderr)
    result = client.save_share(share_url, folder_name=folder or config.get("save_folder", ""))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


def cmd_auto(query: str, config: dict):
    plugins = load_plugins(config)
    if not plugins:
        print("❌ No plugins enabled.")
        return

    # Search
    all_results = []
    for plugin in plugins:
        print(f"🔍 Searching {plugin.display_name}...", file=sys.stderr)
        try:
            results = plugin.search(query)
            for r in results:
                r.site = plugin.name
                r.extra["score"] = score_resource(r)
            all_results.extend(results)
        except Exception as e:
            print(f"⚠️  {plugin.name} error: {e}", file=sys.stderr)

    if not all_results:
        print("❌ No results found.")
        return

    all_results.sort(key=lambda r: r.extra.get("score", 0), reverse=True)
    quark_results = [r for r in all_results if r.source == "quark"]

    if not quark_results:
        print("❌ No Quark resources found.")
        for r in all_results[:5]:
            print(f"  [{r.source}] {r.title}")
        return

    best = quark_results[0]
    print(f"\n🏆 Best: {best.title}", file=sys.stderr)
    print(f"   Score: {best.extra.get('score', 0)}", file=sys.stderr)

    plugin = next((p for p in plugins if p.name == best.site), None)
    if not plugin:
        print("❌ Plugin not found")
        return

    print(f"🔗 Extracting link...", file=sys.stderr)
    share_url = plugin.extract_link(best)
    if not share_url:
        print("❌ Failed to extract link")
        return

    print(f"   URL: {share_url}", file=sys.stderr)

    # Save
    client = get_quark_client(config)
    folder = config.get("save_folder", "影视资源")
    print(f"☁️  Saving to Quark/{folder}...", file=sys.stderr)
    result = client.save_share(share_url, folder_name=folder)

    status = result.get("status", 0)
    if status == 200:
        # Organize into library
        task_data = result.get("task_result", {}).get("data", {})
        save_as = task_data.get("save_as", {})
        saved_fids = save_as.get("save_as_top_fids", [])

        if saved_fids:
            from library import extract_movie_info
            info = extract_movie_info(best.title)
            lib = LibraryManager(client, library_root=folder,
                                 omdb_key=config.get("omdb_api_key", ""),
                                 genre_cache_file=os.path.join(os.path.dirname(__file__), "genre_cache.json"))

            # Build mini4k URL for genre scraping if applicable
            mini4k_url = ""
            if best.site == "mini4k" and best.url.startswith("/"):
                mini4k_url = f"https://www.mini4k.net{best.url}"

            for fid in saved_fids:
                org_result = lib.organize_movie(fid, best.title, info.get("year", ""), mini4k_url)
                if org_result.get("status") == "ok":
                    print(f"📁 Organized: {org_result['path']}", file=sys.stderr)
                else:
                    print(f"⚠️  Organize failed: {org_result.get('error')}", file=sys.stderr)

        print(f"✅ Done!", file=sys.stderr)
    else:
        print(f"❌ Failed: {result.get('message', 'unknown')}", file=sys.stderr)

    print(json.dumps({"movie": best.title, "share_url": share_url, "result": result},
                     indent=2, ensure_ascii=False))


def cmd_organize(fid: str, title: str, config: dict, content_type: str = "movie",
                 season: int = 1, episode: int = 0):
    client = get_quark_client(config)
    lib = LibraryManager(client, library_root=config.get("save_folder", "影视资源"),
                         omdb_key=config.get("omdb_api_key", ""),
                         genre_cache_file=os.path.join(os.path.dirname(__file__), "genre_cache.json"))

    if content_type == "tv":
        result = lib.organize_tv_show(fid, title, season=season, episode=episode)
    else:
        result = lib.organize_movie(fid, title)

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


def cmd_plugins(config: dict):
    plugins = load_plugins(config)
    if not plugins:
        print("No plugins found.")
        print("\nTo add a resource site, create a plugin file:")
        print("  cp scripts/plugins/example.py scripts/plugins/your_site.py")
        print("  # Edit your_site.py, implement search() and extract_link()")
        print('  # Add to config.json: "your_site": {"enabled": true}')
        return

    print("Available plugins:")
    for p in plugins:
        auth = "🔑" if p.requires_auth else "🆓"
        print(f"  {auth} {p.display_name} ({p.name}) - {p.url}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    config = load_config()
    cmd = sys.argv[1]

    if cmd == "search":
        query = " ".join(sys.argv[2:])
        if not query:
            print("Usage: cinema.py search <query>"); sys.exit(1)
        cmd_search(query, config)

    elif cmd == "save":
        if len(sys.argv) < 3:
            print("Usage: cinema.py save <quark_share_url>"); sys.exit(1)
        cmd_save(sys.argv[2], config)

    elif cmd == "auto":
        query = " ".join(sys.argv[2:])
        if not query:
            print("Usage: cinema.py auto <query>"); sys.exit(1)
        cmd_auto(query, config)

    elif cmd == "organize":
        if len(sys.argv) < 4:
            print("Usage: cinema.py organize <file_id> <title> [--type movie|tv] [--season N] [--episode N]")
            sys.exit(1)
        fid = sys.argv[2]
        title = sys.argv[3]
        content_type = "movie"
        season, episode = 1, 0
        i = 4
        while i < len(sys.argv):
            if sys.argv[i] == "--type" and i + 1 < len(sys.argv):
                content_type = sys.argv[i + 1]; i += 2
            elif sys.argv[i] == "--season" and i + 1 < len(sys.argv):
                season = int(sys.argv[i + 1]); i += 2
            elif sys.argv[i] == "--episode" and i + 1 < len(sys.argv):
                episode = int(sys.argv[i + 1]); i += 2
            else:
                i += 1
        cmd_organize(fid, title, config, content_type, season, episode)

    elif cmd == "plugins":
        cmd_plugins(config)

    else:
        print(f"Unknown command: {cmd}\n{__doc__}")
        sys.exit(1)


if __name__ == "__main__":
    main()
