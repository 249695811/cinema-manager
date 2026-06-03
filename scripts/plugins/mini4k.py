"""
mini4k.net plugin - Premium 4K movie resource site.
Requires user account (paid membership).
"""

import re
import json
import httpx
from typing import Optional

from . import ResourcePlugin, ResourceResult


class Plugin(ResourcePlugin):
    name = "mini4k"
    display_name = "MINI4K迷客电影"
    requires_auth = True
    url = "https://www.mini4k.net"

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.client = httpx.Client(follow_redirects=True, timeout=20)
        self._logged_in = False

    def login(self) -> bool:
        username = self.config.get("username", "")
        password = self.config.get("password", "")
        if not username or not password:
            return False

        try:
            r = self.client.post(
                f"{self.url}/user/login?_format=json",
                json={"name": username, "pass": password},
                headers={"Content-Type": "application/json"},
            )
            if r.status_code == 200 and "uid" in r.text:
                self._logged_in = True
                return True
        except Exception as e:
            print(f"[mini4k] Login error: {e}")
        return False

    def search(self, query: str, page: int = 1) -> list[ResourceResult]:
        if not self._logged_in and not self.login():
            return []

        try:
            r = self.client.get(
                f"{self.url}/search_api_autocomplete/solr9_search",
                params={"q": query},
            )
            if r.status_code != 200:
                return []
        except Exception as e:
            print(f"[mini4k] Search error: {e}")
            return []

        results = []
        for item in r.json():
            url = item.get("url", "")
            value = item.get("value", "")
            lines = [l.strip() for l in value.split("\n") if l.strip()]
            ch_name = lines[0] if lines else ""
            en_name = lines[1] if len(lines) > 1 else ""
            year = ""
            for l in lines:
                if re.match(r"\d{4}", l):
                    year = l.strip().split()[0]
                    break

            content_type = "movie" if "/movies/" in url else "show" if "/shows/" in url else "other"
            content_id = re.search(r"/(\d+)", url)

            results.append(ResourceResult(
                title=f"{ch_name} ({en_name}) {year}".strip(),
                source="quark",  # mini4k has quark links on torrent pages
                url=url,
                site=self.name,
                extra={
                    "content_id": content_id.group(1) if content_id else "",
                    "content_type": content_type,
                    "ch_name": ch_name,
                    "en_name": en_name,
                    "year": year,
                },
            ))

        return results

    def extract_link(self, resource: ResourceResult) -> Optional[str]:
        """Get quark link from the torrent detail pages."""
        if not self._logged_in and not self.login():
            return None

        content_id = resource.extra.get("content_id", "")
        content_type = resource.extra.get("content_type", "movies")
        if not content_id:
            return None

        # Get movie/show page to find torrent links
        try:
            r = self.client.get(f"{self.url}/{content_type}/{content_id}")
            if r.status_code != 200:
                return None
        except Exception:
            return None

        torrent_ids = re.findall(r'href="/torrents/(\d+)"', r.text)

        # Check each torrent for quark link
        for tid in torrent_ids:
            try:
                r = self.client.get(f"{self.url}/torrents/{tid}")
                if r.status_code != 200:
                    continue
                quark_match = re.search(
                    r'href="(https://pan\.quark\.cn/s/[^"]+)"', r.text
                )
                if quark_match:
                    return quark_match.group(1)
            except Exception:
                continue

        return None

    def get_torrents(self, content_id: str, content_type: str = "movies") -> list[dict]:
        """Get detailed torrent list for a movie/show."""
        if not self._logged_in and not self.login():
            return []

        try:
            r = self.client.get(f"{self.url}/{content_type}/{content_id}")
            if r.status_code != 200:
                return []
        except Exception:
            return []

        torrents = []
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", r.text, re.S)
        for row in rows:
            cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)
            if len(cells) >= 3:
                name_match = re.search(
                    r'href="/torrents/(\d+)"[^>]*>([^<]+)', cells[0]
                )
                if name_match:
                    size_match = re.search(
                        r"(\d+\.?\d*\s*(?:GB|MB|TB))",
                        cells[2] if len(cells) > 2 else "",
                    )
                    torrents.append({
                        "torrent_id": name_match.group(1),
                        "name": name_match.group(2).strip(),
                        "size": size_match.group(1) if size_match else "",
                    })

        return torrents
