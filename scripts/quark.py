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
    """Quark cloud drive client with auto-login support."""

    def __init__(self, username: str = "", password: str = "", cookie: str = ""):
        self.username = username
        self.password = password
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
        """Login with username/password to get fresh cookies."""
        if not self.username or not self.password:
            return bool(self.cookie)

        # quarkpan library handles login
        try:
            sys.path.insert(0, self._quarkpan_path())
            from quark_client import create_client
            client = create_client(auto_login=True)
            if client.is_logged_in():
                # Extract cookies from the client
                self._cookie = "; ".join(
                    f"{k}={v}" for k, v in client.api_client._client.cookies.items()
                )
                self._save_cookie_cache()
                return True
        except Exception:
            pass

        return bool(self.cookie)

    def _quarkpan_path(self) -> str:
        """Find quarkpan installation path."""
        candidates = [
            os.path.expanduser("~/.hermes-web-ui/desktop-runtime/linux-x64/python/lib/python3.12/site-packages"),
            "/usr/lib/python3/dist-packages",
        ]
        for p in candidates:
            if os.path.exists(os.path.join(p, "quark_client")):
                return p
        return ""

    def save_share(self, share_url: str, folder_name: str = "") -> dict:
        """Save a quark share link to drive."""
        if not self.cookie:
            return {"error": "Not logged in"}

        # Try quarkpan library first
        try:
            import sys
            sys.path.insert(0, self._quarkpan_path())
            from quark_client import create_client
            client = create_client(cookies=self.cookie, auto_login=False)
            kwargs = {}
            if folder_name:
                kwargs["target_folder_name"] = folder_name
            return client.save_shared_files(share_url, **kwargs)
        except ImportError:
            pass
        except Exception as e:
            return {"error": str(e)}

        # Fallback: raw HTTP
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
