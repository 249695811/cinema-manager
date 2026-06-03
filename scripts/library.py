"""
Library Manager - Organize saved files in Quark drive for media players.

Renames and organizes files following Infuse/Plex/Jellyfin conventions:
- Movies:  Movie Name (Year)/Movie Name (Year).ext
- TV Shows: Show Name/Season XX/Show Name - SXXEXX - Episode Title.ext
"""

import re
import sys
import json
from typing import Optional

from quark import QuarkClient


# ── Naming conventions ──

def clean_name(name: str) -> str:
    """Remove tags and clean up file names for media player compatibility."""
    # Remove common tags
    tags_to_remove = [
        r'\[.*?\]',           # [xxx]
        r'【.*?】',           # 【xxx】
        r'#\S+',              # #tag
        r'🗄',                # emoji
        r'📜',                # emoji
        r'介绍：.*$',          # description suffix
    ]
    for pattern in tags_to_remove:
        name = re.sub(pattern, '', name)

    # Clean separators
    name = re.sub(r'[·。]+', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def parse_movie_info(title: str) -> dict:
    """Extract movie info from a title string."""
    info = {"title": title, "year": "", "resolution": "", "source": ""}

    # Extract year
    year_match = re.search(r'[\(（](\d{4})[\)）]|\b(19\d{2}|20\d{2})\b', title)
    if year_match:
        info["year"] = year_match.group(1) or year_match.group(2)

    # Extract Chinese name (before year or English name)
    cn_match = re.search(r'^([\u4e00-\u9fff][\u4e00-\u9fff\s·：·]+)', title)
    if cn_match:
        info["cn_name"] = cn_match.group(1).strip()

    # Extract English name
    en_match = re.search(r'([A-Z][a-zA-Z\s:]+(?:\d+)?)', title)
    if en_match:
        info["en_name"] = en_match.group(1).strip()

    # Extract resolution
    res_match = re.search(r'(2160[pP]|4[kK]|1080[pP]|720[pP])', title, re.I)
    if res_match:
        info["resolution"] = res_match.group(1).upper()

    return info


def format_movie_folder(info: dict) -> str:
    """Format as Infuse-compatible folder name: Movie Name (Year)"""
    name = info.get("cn_name") or info.get("title", "Unknown")
    name = clean_name(name)
    year = info.get("year", "")
    if year:
        return f"{name} ({year})"
    return name


def format_movie_filename(info: dict, ext: str = ".mkv") -> str:
    """Format as Infuse-compatible filename: Movie Name (Year).ext"""
    folder = format_movie_folder(info)
    return f"{folder}{ext}"


# ── Library Manager ──

class LibraryManager:
    """Manage organized media library in Quark drive."""

    def __init__(self, quark: QuarkClient, library_root: str = "影视资源"):
        self.quark = quark
        self.library_root = library_root
        self._root_id = None

    def get_or_create_folder(self, name: str, parent_id: str = "0") -> Optional[str]:
        """Get folder ID by name, create if not exists."""
        # List existing folders
        try:
            result = self.quark.client.list_files(parent_id)
            files = result.get("data", {}).get("list", [])
            for f in files:
                if f.get("file_name") == name and f.get("dir"):
                    return f["fid"]
        except Exception:
            pass

        # Create folder
        try:
            result = self.quark.client.create_folder(name, parent_id)
            return result.get("data", {}).get("fid")
        except Exception as e:
            print(f"⚠️  Failed to create folder '{name}': {e}", file=sys.stderr)
            return None

    def ensure_library_root(self) -> Optional[str]:
        """Ensure the library root folder exists."""
        if self._root_id:
            return self._root_id
        self._root_id = self.get_or_create_folder(self.library_root)
        return self._root_id

    def organize_movie(self, source_fid: str, title: str, year: str = "") -> dict:
        """
        Organize a saved movie file into the library structure.

        Moves file from root/downloads into:
            影视资源/Movie Name (Year)/Movie Name (Year).ext

        Args:
            source_fid: File ID of the saved file in Quark
            title: Movie title
            year: Release year

        Returns:
            dict with status and new path info
        """
        root_id = self.ensure_library_root()
        if not root_id:
            return {"error": "Failed to access library root"}

        # Parse movie info
        info = parse_movie_info(title)
        if year:
            info["year"] = year

        # Create movie folder
        folder_name = format_movie_folder(info)
        folder_id = self.get_or_create_folder(folder_name, root_id)
        if not folder_id:
            return {"error": f"Failed to create folder: {folder_name}"}

        # Get original file info
        try:
            file_info = self.quark.client.get_file_info(source_fid)
            original_name = file_info.get("data", {}).get("file_name", "")
            is_dir = file_info.get("data", {}).get("dir", False)
        except Exception:
            original_name = ""
            is_dir = False

        # Rename if it's a file (not directory)
        if not is_dir and original_name:
            ext = original_name.rsplit(".", 1)[-1] if "." in original_name else "mkv"
            new_name = format_movie_filename(info, f".{ext}")
            try:
                self.quark.client.rename_file(source_fid, new_name)
            except Exception as e:
                print(f"⚠️  Rename failed: {e}", file=sys.stderr)

        # Move to library folder
        try:
            self.quark.client.move_files([source_fid], folder_id)
            return {
                "status": "ok",
                "path": f"{self.library_root}/{folder_name}",
                "folder_id": folder_id,
                "info": info,
            }
        except Exception as e:
            return {"error": f"Move failed: {e}"}

    def organize_tv_show(self, source_fid: str, show_name: str,
                         season: int = 1, episode: int = 0,
                         episode_title: str = "") -> dict:
        """
        Organize a saved TV show file into the library structure.

        Moves file into:
            影视资源/Show Name/Season XX/Show Name - SXXEXX.ext
        """
        root_id = self.ensure_library_root()
        if not root_id:
            return {"error": "Failed to access library root"}

        # Create show folder
        show_folder_id = self.get_or_create_folder(clean_name(show_name), root_id)
        if not show_folder_id:
            return {"error": f"Failed to create folder: {show_name}"}

        # Create season folder
        season_name = f"Season {season:02d}"
        season_folder_id = self.get_or_create_folder(season_name, show_folder_id)
        if not season_folder_id:
            return {"error": f"Failed to create folder: {season_name}"}

        # Get original file info
        try:
            file_info = self.quark.client.get_file_info(source_fid)
            original_name = file_info.get("data", {}).get("file_name", "")
            ext = original_name.rsplit(".", 1)[-1] if "." in original_name else "mkv"
        except Exception:
            ext = "mkv"

        # Rename
        new_name = f"{clean_name(show_name)} - S{season:02d}E{episode:02d}"
        if episode_title:
            new_name += f" - {episode_title}"
        new_name += f".{ext}"

        try:
            self.quark.client.rename_file(source_fid, new_name)
        except Exception as e:
            print(f"⚠️  Rename failed: {e}", file=sys.stderr)

        # Move
        try:
            self.quark.client.move_files([source_fid], season_folder_id)
            return {
                "status": "ok",
                "path": f"{self.library_root}/{show_name}/{season_name}/{new_name}",
                "folder_id": season_folder_id,
            }
        except Exception as e:
            return {"error": f"Move failed: {e}"}

    def list_recent(self, limit: int = 20) -> list:
        """List recently added files in the library."""
        root_id = self.ensure_library_root()
        if not root_id:
            return []

        try:
            result = self.quark.client.list_files(root_id)
            files = result.get("data", {}).get("list", [])
            return sorted(files, key=lambda f: f.get("l_created_at", 0), reverse=True)[:limit]
        except Exception:
            return []
