"""
Library Manager - Organize saved files in Quark drive for media players.

Logic:
- Well-named files (scene format: has 2160p/1080p/WEB-DL/BluRay/x265 etc) → keep original name, only create folder
- Messy files (Chinese titles, emojis, random tags) → extract info, rename to standard format

Folder structure (Infuse/Plex compatible):
- Movies: Movie Name (Year)/original_or_renamed.ext
- TV: Show Name/Season XX/original_or_renamed.ext
"""

import re
import sys
import json
from typing import Optional

from quark import QuarkClient


# ── Scene name detection ──

SCENE_TAGS = [
    r'\d{3,4}[pPiI]',           # 2160p, 1080p, 720p
    r'(?:2160|1080|720|480)',    # resolution numbers
    r'WEB[-.]?DL', r'WEBRip', r'BluRay', r'REMUX', r'BDRip', r'BDRemux',
    r'UHD', r'HDR(?:10)?(?:\+)?', r'DV', r'Dolby\.?Vision',
    r'[xXhH]\.?26[45]', r'HEVC', r'AVC', r'AV1',
    r'(?:DDP?|EAC3|TrueHD|DTS(?:-HD)?|Atmos)\b',
    r'\d+\.\d+',                # 5.1, 7.1 etc
    r'\[.*?\]',                 # [QxR], [RARBG] etc
]


def is_scene_name(filename: str) -> bool:
    """Check if filename follows scene naming convention."""
    # Must have at least 2 scene-standard tags
    matches = 0
    for pattern in SCENE_TAGS:
        if re.search(pattern, filename, re.I):
            matches += 1
    return matches >= 2


def clean_display_name(name: str) -> str:
    """Clean messy names for folder display."""
    # Remove emojis and decorative unicode
    name = re.sub(r'[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE00-\uFE0F]', '', name)
    # Remove bracket tags
    name = re.sub(r'\[.*?\]', '', name)
    name = re.sub(r'【.*?】', '', name)
    name = re.sub(r'[《》]', '', name)
    # Remove prefixes like "名称：", "电影：", "资源标题：", "#电影名称:", "电影"
    name = re.sub(r'^[#\s]*(电影资源标题|电影名称|名称|资源标题|标题)[：:]\s*', '', name)
    # Remove standalone prefix words (no colon needed)
    name = re.sub(r'^(电影|片名)\s*', '', name)
    # Remove description suffixes after punctuation
    name = re.split(r'[·。：：]+', name)[0]
    # Remove trailing site names
    name = re.sub(r'(夸克网盘|百度网盘|迅雷云盘|网盘链接|链接)\s*$', '', name)
    # Remove trailing year in parentheses (avoid double-year in folder names)
    name = re.sub(r'\s*[\(（]\d{4}[\)）]\s*$', '', name)
    # Clean whitespace
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def extract_movie_info(title: str) -> dict:
    """Extract movie name and year from title."""
    info = {"title": title, "year": "", "cn_name": "", "en_name": ""}

    # Extract year
    year_match = re.search(r'[\(（](\d{4})[\)）]|\b((?:19|20)\d{2})\b', title)
    if year_match:
        info["year"] = year_match.group(1) or year_match.group(2)

    # Extract Chinese name (before year or English block)
    cn_match = re.search(r'^([\u4e00-\u9fff][\u4e00-\u9fff\s·：·—\-]+?)(?=[\s\(（A-Z#]|$)', title)
    if cn_match:
        cn = cn_match.group(1).strip()
        if len(cn) >= 2:
            info["cn_name"] = cn

    # Extract English name
    en_match = re.search(r'([A-Z][a-zA-Z\s:&\-]+?)(?:\s+\d{4}|\s*[\(（]|$)', title)
    if en_match:
        en = en_match.group(1).strip()
        if len(en) >= 2:
            info["en_name"] = en

    return info


def format_folder_name(info: dict) -> str:
    """Format: Movie Name (Year)"""
    name = info.get("cn_name") or info.get("en_name") or info.get("title", "Unknown")
    name = clean_display_name(name)
    year = info.get("year", "")
    if year:
        return f"{name} ({year})"
    return name


def format_filename(info: dict, ext: str = "mkv") -> str:
    """Format: Movie Name (Year).ext"""
    return f"{format_folder_name(info)}.{ext}"


# ── Library Manager ──

class LibraryManager:
    """Manage organized media library in Quark drive."""

    def __init__(self, quark: QuarkClient, library_root: str = "影视资源"):
        self.quark = quark
        self.library_root = library_root
        self._root_id = None

    def _api(self, method: str, *args, **kwargs):
        """Call quark client method via the underlying API client."""
        # Access quark_client library methods
        sys.path.insert(0, self._quarkpan_path())
        from quark_client import create_client
        client = create_client(cookies=self.quark.cookie, auto_login=False)
        return getattr(client, method)(*args, **kwargs)

    def _quarkpan_path(self) -> str:
        import os
        candidates = [
            os.path.expanduser("~/.hermes-web-ui/desktop-runtime/linux-x64/python/lib/python3.12/site-packages"),
        ]
        for p in candidates:
            if os.path.exists(os.path.join(p, "quark_client")):
                return p
        return ""

    def get_or_create_folder(self, name: str, parent_id: str = "0") -> Optional[str]:
        """Get folder ID by name, create if not exists."""
        try:
            result = self._api("list_files", parent_id)
            files = result.get("data", {}).get("list", [])
            for f in files:
                if f.get("file_name") == name and f.get("dir"):
                    return f["fid"]
        except Exception:
            pass

        try:
            result = self._api("create_folder", name, parent_id)
            return result.get("data", {}).get("fid")
        except Exception as e:
            print(f"⚠️  Failed to create folder '{name}': {e}", file=sys.stderr)
            return None

    def ensure_library_root(self) -> Optional[str]:
        if self._root_id:
            return self._root_id
        self._root_id = self.get_or_create_folder(self.library_root)
        return self._root_id

    def organize_movie(self, source_fid: str, title: str, year: str = "") -> dict:
        """
        Organize a saved movie file into the library.

        - If filename is scene-standard → keep it, just move into folder
        - If filename is messy → rename to Movie Name (Year).ext
        """
        root_id = self.ensure_library_root()
        if not root_id:
            return {"error": "Failed to access library root"}

        # Get original file info
        try:
            file_info = self._api("get_file_info", source_fid)
            file_data = file_info.get("data", {})
            original_name = file_data.get("file_name", "")
            is_dir = file_data.get("dir", False)
        except Exception:
            original_name = ""
            is_dir = False

        # Parse movie info from title (used for folder name regardless)
        info = extract_movie_info(title)
        if year:
            info["year"] = year

        # Create movie folder
        folder_name = format_folder_name(info)
        folder_id = self.get_or_create_folder(folder_name, root_id)
        if not folder_id:
            return {"error": f"Failed to create folder: {folder_name}"}

        # Decide: keep original name or rename
        if not is_dir and original_name:
            if is_scene_name(original_name):
                # Scene-standard name → keep as-is
                print(f"📋 Keeping original name: {original_name}", file=sys.stderr)
            else:
                # Messy name → rename
                ext = original_name.rsplit(".", 1)[-1] if "." in original_name else "mkv"
                new_name = format_filename(info, ext)
                try:
                    self._api("rename_file", source_fid, new_name)
                    print(f"✏️  Renamed: {original_name} → {new_name}", file=sys.stderr)
                except Exception as e:
                    print(f"⚠️  Rename failed: {e}", file=sys.stderr)

        # Move to library folder
        try:
            self._api("move_files", [source_fid], folder_id)
            return {
                "status": "ok",
                "path": f"{self.library_root}/{folder_name}",
                "folder_id": folder_id,
                "kept_original": is_scene_name(original_name) if original_name else False,
            }
        except Exception as e:
            return {"error": f"Move failed: {e}"}

    def organize_tv_show(self, source_fid: str, show_name: str,
                         season: int = 1, episode: int = 0,
                         episode_title: str = "") -> dict:
        """
        Organize a saved TV show file.

        - Scene-standard name → keep, just move into Season folder
        - Messy name → rename to Show Name - SXXEXX.ext
        """
        root_id = self.ensure_library_root()
        if not root_id:
            return {"error": "Failed to access library root"}

        # Get original file info
        try:
            file_info = self._api("get_file_info", source_fid)
            file_data = file_info.get("data", {})
            original_name = file_data.get("file_name", "")
        except Exception:
            original_name = ""

        # Create show/season folders
        show_folder_id = self.get_or_create_folder(clean_display_name(show_name), root_id)
        if not show_folder_id:
            return {"error": f"Failed to create folder: {show_name}"}

        season_name = f"Season {season:02d}"
        season_folder_id = self.get_or_create_folder(season_name, show_folder_id)
        if not season_folder_id:
            return {"error": f"Failed to create folder: {season_name}"}

        # Rename if not scene-standard
        if original_name:
            if is_scene_name(original_name):
                print(f"📋 Keeping original name: {original_name}", file=sys.stderr)
            else:
                ext = original_name.rsplit(".", 1)[-1] if "." in original_name else "mkv"
                new_name = f"{clean_display_name(show_name)} - S{season:02d}E{episode:02d}"
                if episode_title:
                    new_name += f" - {episode_title}"
                new_name += f".{ext}"
                try:
                    self._api("rename_file", source_fid, new_name)
                    print(f"✏️  Renamed: {original_name} → {new_name}", file=sys.stderr)
                except Exception as e:
                    print(f"⚠️  Rename failed: {e}", file=sys.stderr)

        # Move
        try:
            self._api("move_files", [source_fid], season_folder_id)
            return {
                "status": "ok",
                "path": f"{self.library_root}/{show_name}/{season_name}",
                "folder_id": season_folder_id,
                "kept_original": is_scene_name(original_name) if original_name else False,
            }
        except Exception as e:
            return {"error": f"Move failed: {e}"}
