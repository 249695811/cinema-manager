"""
Example resource site plugin template.
Copy this file and implement the methods to add your own resource site.

Usage:
    1. Copy this file to scripts/plugins/your_site.py
    2. Implement search() and extract_link()
    3. Add "your_site": {"enabled": true} to config.json plugins
"""

import json
import urllib.request
import urllib.parse
from typing import Optional

from . import ResourcePlugin, ResourceResult


class Plugin(ResourcePlugin):
    # ── Required: identify your plugin ──
    name = "example"                        # unique id (filename without .py)
    display_name = "Example Resource Site"  # shown to user
    requires_auth = False                   # True if login needed
    url = "https://example.com"             # site URL

    def search(self, query: str, page: int = 1) -> list[ResourceResult]:
        """
        Search the resource site for movies/TV shows.

        Args:
            query: search keyword (movie name, etc.)
            page: pagination (1-indexed)

        Returns:
            List of ResourceResult with at least title, source, url filled.
            source should be "quark", "baidu", or "magnet".
            url is the share link or an opaque token for extract_link().
        """
        results = []

        # Example: call a search API
        # params = urllib.parse.urlencode({"keyword": query, "page": str(page)})
        # req = urllib.request.Request(f"{self.url}/api/search?{params}")
        # with urllib.request.urlopen(req, timeout=15) as resp:
        #     data = json.loads(resp.read())
        # for item in data["results"]:
        #     results.append(ResourceResult(
        #         title=item["title"],
        #         source="quark",       # or "baidu" / "magnet"
        #         url=item["share_url"], # or encrypted token
        #         site=self.name,
        #     ))

        return results

    def extract_link(self, resource: ResourceResult) -> Optional[str]:
        """
        Extract the actual Quark share URL from a search result.

        If search() already returns direct share URLs, just return resource.url.
        If search() returns encrypted tokens, decrypt them here.

        Returns:
            Quark share URL (https://pan.quark.cn/s/xxx) or None.
        """
        # If url is already a direct share link:
        if resource.url.startswith("https://pan.quark.cn/"):
            return resource.url

        # Otherwise, call an extraction API:
        # req = urllib.request.Request(
        #     f"{self.url}/api/extract",
        #     data=json.dumps({"token": resource.url}).encode(),
        #     headers={"Content-Type": "application/json"},
        # )
        # with urllib.request.urlopen(req, timeout=15) as resp:
        #     data = json.loads(resp.read())
        # return data.get("share_url")

        return None
