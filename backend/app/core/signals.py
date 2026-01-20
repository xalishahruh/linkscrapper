import backend.app.core.fetcher as fetcher

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Dict
from urllib.parse import urlparse

KNOWN_SHORTENERS = {
    "bit.ly",
    "t.co",
    "tinyurl.com",
    "goo.gl",
    "ow.ly",
    "buff.ly",
    "is.gd",
    "cutt.ly",
    "rebrand.ly",
}

@dataclass
class UrlSignals:
    redirect_count: int
    redirect_chain: List[str]
    initial_host: Optional[str]
    final_host: Optional[str]
    hostname_changed: bool
    used_shortener:bool

    http_status: int
    status_family:str
    content_type: Optional[str]
    content_category: str
    server: Optional[str]

    security_headers_present: Dict[str, bool]