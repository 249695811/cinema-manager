"""
Base plugin interface for resource sites.
All resource site plugins must inherit from ResourcePlugin.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ResourceResult:
    """A single resource search result."""
    title: str
    source: str                    # "quark", "baidu", "magnet"
    url: str                       # share URL or encrypted URL
    quality: str = ""              # "4K", "1080p", etc.
    size: str = ""                 # "25.0GB"
    site: str = ""                 # plugin name
    extra: dict = field(default_factory=dict)  # plugin-specific data

    @property
    def is_quark(self) -> bool:
        return self.source == "quark"

    @property
    def is_cloud(self) -> bool:
        return self.source in ("quark", "baidu", "xunlei")


class ResourcePlugin(ABC):
    """Base class for resource site plugins."""

    name: str = ""                 # unique identifier
    display_name: str = ""         # human-readable name
    requires_auth: bool = False    # whether login is needed
    url: str = ""                  # site URL

    def __init__(self, config: dict = None):
        self.config = config or {}

    @abstractmethod
    def search(self, query: str, page: int = 1) -> list[ResourceResult]:
        """Search for resources. Returns list of ResourceResult."""
        ...

    @abstractmethod
    def extract_link(self, resource: ResourceResult) -> Optional[str]:
        """Extract the actual share URL from a resource.
        Returns quark pan share URL or None."""
        ...

    def login(self) -> bool:
        """Login if required. Returns True on success."""
        return True

    def __repr__(self):
        auth = "🔑" if self.requires_auth else "🆓"
        return f"{auth} {self.display_name} ({self.name})"
