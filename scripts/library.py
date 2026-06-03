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
import subprocess
from typing import Optional

from quark import QuarkClient


# ── Genre lookup via Tavily ──

GENRE_MAP = {
    "action": "动作", "adventure": "冒险", "animation": "动画",
    "comedy": "喜剧", "crime": "犯罪", "documentary": "纪录片",
    "drama": "剧情", "family": "家庭", "fantasy": "奇幻",
    "history": "历史", "horror": "恐怖", "music": "音乐",
    "mystery": "悬疑", "romance": "爱情", "romantic": "爱情",
    "science fiction": "科幻", "sci-fi": "科幻", "scifi": "科幻",
    "thriller": "惊悚", "war": "战争", "western": "西部",
    "动作": "动作", "冒险": "冒险", "动画": "动画",
    "喜剧": "喜剧", "犯罪": "犯罪", "纪录片": "纪录片",
    "剧情": "剧情", "家庭": "家庭", "奇幻": "奇幻",
    "历史": "历史", "恐怖": "恐怖", "音乐": "音乐",
    "悬疑": "悬疑", "爱情": "爱情", "科幻": "科幻",
    "惊悚": "惊悚", "战争": "战争", "西部": "西部",
}


def lookup_genre(title: str, year: str = "", omdb_key: str = "", cache_file: str = "",
                 mini4k_url: str = "") -> str:
    """Look up movie genre. OMDB → mini4k scrape → cache → '其他'."""
    cache = {}
    if cache_file:
        try:
            with open(cache_file) as f:
                cache = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    cache_key = f"{title} ({year})" if year else title
    if cache_key in cache:
        return cache[cache_key]

    genre = "其他"

    # Method 1: OMDB API (free, 1000 req/day)
    if omdb_key:
        try:
            import urllib.parse
            params = urllib.parse.urlencode({"t": title, "y": year, "apikey": omdb_key})
            result = subprocess.run(
                ["curl", "-s", "--connect-timeout", "5",
                 f"http://www.omdbapi.com/?{params}"],
                capture_output=True, text=True, timeout=10
            )
            data = json.loads(result.stdout)
            omdb_genre = data.get("Genre", "")
            if omdb_genre:
                genre = _map_omdb_genre(omdb_genre.split(",")[0].strip())
        except Exception:
            pass

    # Method 2: Scrape genre from mini4k page
    if genre == "其他" and mini4k_url:
        try:
            result = subprocess.run(
                ["curl", "-s", "--connect-timeout", "8", mini4k_url],
                capture_output=True, text=True, timeout=15
            )
            # Extract from <span class="genre">...<a>动作</a>...</span>
            genre_match = re.search(
                r'class="genre[^"]*"[^>]*>(.*?)</span>', result.stdout, re.S
            )
            if genre_match:
                genres_text = genre_match.group(1)
                genres = re.findall(r'>([^<]+)</a>', genres_text)
                if genres:
                    # Clean and take first genre
                    first_genre = genres[0].strip().rstrip(',').strip()
                    genre = GENRE_MAP.get(first_genre, first_genre)
        except Exception:
            pass

    # Cache result
    if cache_file and genre != "其他":
        cache[cache_key] = genre
        try:
            with open(cache_file, "w") as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    return genre


def _map_omdb_genre(english_genre: str) -> str:
    """Map OMDB English genre to Chinese."""
    mapping = {
        "Action": "动作", "Adventure": "冒险", "Animation": "动画",
        "Comedy": "喜剧", "Crime": "犯罪", "Documentary": "纪录片",
        "Drama": "剧情", "Family": "家庭", "Fantasy": "奇幻",
        "History": "历史", "Horror": "恐怖", "Music": "音乐",
        "Mystery": "悬疑", "Romance": "爱情", "Sci-Fi": "科幻",
        "Thriller": "惊悚", "War": "战争", "Western": "西部",
    }
    return mapping.get(english_genre, "其他")


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

    def __init__(self, quark: QuarkClient, library_root: str = "影视资源",
                 omdb_key: str = "", genre_cache_file: str = ""):
        self.quark = quark
        self.library_root = library_root
        self.omdb_key = omdb_key
        self.genre_cache_file = genre_cache_file
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

    def organize_movie(self, source_fid: str, title: str, year: str = "",
                       mini4k_url: str = "") -> dict:
        """
        Organize a saved movie file into the library.
        Structure: library_root/Genre/ Movie Name (Year)/files
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

        # Parse movie info from title
        info = extract_movie_info(title)
        if year:
            info["year"] = year

        folder_name = format_folder_name(info)

        # Look up genre → create genre subfolder
        genre = lookup_genre(info.get("cn_name") or info.get("en_name") or info.get("title", ""), info.get("year", ""), self.omdb_key, self.genre_cache_file, mini4k_url)
        print(f"🎭 Genre: {genre}", file=sys.stderr)
        genre_id = self.get_or_create_folder(genre, root_id)
        if not genre_id:
            print(f"⚠️  Failed to create genre folder, falling back to root", file=sys.stderr)
            genre_id = root_id

        if is_dir:
            # Source is already a folder → rename it directly, no wrapper
            if original_name != folder_name:
                try:
                    self._api("rename_file", source_fid, folder_name)
                    print(f"✏️  Renamed folder: {original_name} → {folder_name}", file=sys.stderr)
                except Exception as e:
                    print(f"⚠️  Rename failed: {e}", file=sys.stderr)
            # Move to genre folder
            try:
                self._api("move_files", [source_fid], genre_id)
                return {
                    "status": "ok",
                    "path": f"{self.library_root}/{genre}/{folder_name}",
                    "folder_id": source_fid,
                    "genre": genre,
                    "kept_original": False,
                }
            except Exception as e:
                return {"error": f"Move failed: {e}"}

        # Source is a file → create folder and move file into it
        folder_id = self.get_or_create_folder(folder_name, genre_id)
        if not folder_id:
            return {"error": f"Failed to create folder: {folder_name}"}

        # Decide: keep original name or rename
        if original_name:
            if is_scene_name(original_name):
                print(f"📋 Keeping original name: {original_name}", file=sys.stderr)
            else:
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
                "path": f"{self.library_root}/{genre}/{folder_name}",
                "folder_id": folder_id,
                "genre": genre,
                "kept_original": is_scene_name(original_name) if original_name else False,
            }
        except Exception as e:
            return {"error": f"Move failed: {e}"}

    def organize_tv_show(self, source_fid: str, show_name: str,
                         season: int = 1, episode: int = 0,
                         episode_title: str = "") -> dict:
        """
        Organize a saved TV show file.
        Structure: library_root/Genre/Show Name/Season XX/files
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

        # Look up genre
        genre = lookup_genre(show_name, omdb_key=self.omdb_key, cache_file=self.genre_cache_file)
        print(f"🎭 Genre: {genre}", file=sys.stderr)
        genre_id = self.get_or_create_folder(genre, root_id)
        if not genre_id:
            genre_id = root_id

        # Create show/season folders
        show_folder_id = self.get_or_create_folder(clean_display_name(show_name), genre_id)
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
                "path": f"{self.library_root}/{genre}/{show_name}/{season_name}",
                "folder_id": season_folder_id,
                "genre": genre,
                "kept_original": is_scene_name(original_name) if original_name else False,
            }
        except Exception as e:
            return {"error": f"Move failed: {e}"}
