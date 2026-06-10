"""
Quark cloud drive client.
Handles login, cookie management, and file saving.

Uses the quarkpan library if available, falls back to raw HTTP.
"""

import json
import os
import time
from typing import Optional

import httpx

QUARK_API = "https://drive-pc.quark.cn/1/clouddrive"
QUARK_SHARE_API = "https://drive.quark.cn/1/clouddrive"

COOKIE_CACHE = os.path.expanduser("~/.cinema-manager/quark_cookies.json")


class QuarkClient:
    """Quark cloud drive client with cookie-based authentication."""

    def __init__(self, cookie: str = ""):
        self._cookie = cookie
        self.client = httpx.Client(
            follow_redirects=True,
            timeout=30,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://pan.quark.cn/",
            },
        )

    @property
    def cookie(self) -> str:
        if self._cookie:
            return self._cookie
        # Try loading cached cookie
        self._load_cookie_cache()
        return self._cookie

    def _load_cookie_cache(self):
        if os.path.exists(COOKIE_CACHE):
            try:
                with open(COOKIE_CACHE) as f:
                    data = json.load(f)
                if data.get("expires_at", 0) > time.time():
                    self._cookie = data.get("cookie", "")
            except Exception:
                pass

    def _save_cookie_cache(self):
        os.makedirs(os.path.dirname(COOKIE_CACHE), exist_ok=True)
        with open(COOKIE_CACHE, "w") as f:
            json.dump({
                "cookie": self._cookie,
                "expires_at": time.time() + 86400 * 7,  # 7 days
            }, f)

    def login(self) -> bool:
        """Check if cookie is available."""
        return bool(self.cookie)

    def save_share(self, share_url: str, folder_name: str = "") -> dict:
        """Save a quark share link to drive."""
        if not self.cookie:
            return {"error": "Not logged in"}

        return self._save_raw(share_url)

    def _save_raw(self, share_url: str) -> dict:
        """Raw HTTP save implementation."""
        import re
        pwd_match = re.search(r"pan\.quark\.cn/s/([a-zA-Z0-9]+)", share_url)
        if not pwd_match:
            return {"error": "Invalid share URL"}

        pwd_id = pwd_match.group(1)
        headers = {
            "Cookie": self.cookie,
            "Content-Type": "application/json",
        }

        # Get share token
        r = self.client.post(
            f"{QUARK_SHARE_API}/share/sharepage/token",
            json={"pwd_id": pwd_id, "passcode": ""},
            headers=headers,
        )
        if r.status_code != 200 or r.json().get("code") != 0:
            return {"error": "Failed to get share token"}

        stoken = r.json()["data"]["stoken"]

        # List files in share
        r = self.client.get(
            f"{QUARK_SHARE_API}/share/sharepage/detail",
            params={
                "pwd_id": pwd_id, "stoken": stoken,
                "pdir_fid": "0", "_page": "1", "_size": "50",
                "pr": "ucpro", "fr": "pc",
            },
            headers=headers,
        )
        if r.status_code != 200:
            return {"error": "Failed to list share files"}

        files = r.json().get("data", {}).get("list", [])
        if not files:
            return {"error": "Share is empty"}

        # Save files
        r = self.client.post(
            f"{QUARK_SHARE_API}/share/sharepage/save",
            json={
                "fid_list": [f["fid"] for f in files],
                "fid_token_list": [f.get("share_fid_token", "") for f in files],
                "to_pdir_fid": "0",
                "pwd_id": pwd_id,
                "stoken": stoken,
                "pdir_fid": "0",
                "pdir_save_all": True,
                "exclude_fids": [],
                "scene": "link",
            },
            headers=headers,
        )

        return r.json() if r.status_code == 200 else {"error": f"Save failed: {r.status_code}"}
