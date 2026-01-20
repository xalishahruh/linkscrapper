from __future__ import annotations

import backend.app.core.fetcher as FetchResult


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

def _host(url: str) -> Optional[str]:
    try:
        return urlparse(url).hostname
    except Exception:
        return None

def _status_family(code: int) -> str:
    if 200 <= code <= 299:
        return "2xx"
    if 300 <= code <= 399:
        return "3xx"
    if 400 <= code <= 499:
        return "4xx"
    if 500 <= code <= 599:
        return "5xx"
    return "other"

def _content_category(content_type: Optional[str]) -> str:

    if not content_type:
        return "Unknown content type"

    ct = content_type.lower()

    if "text/html" in ct:
        return "html"

    if "application/pdf" in ct:
        return "pdf"

    if "application/json" in ct:
        return "json"

    if ct.startswith("text/"):
        return "text"

    if "application/octet-stream" in ct:
        return "download"
    if "application/zip" in ct or "application/x-zip" in ct:
        return "download"
    if "application/pdf" in ct:
        return "download"

    return "other"


def _uses_shortener(chain: List[str]) -> bool:
    for u in chain:
        h = _host(u)
        if h and h.lower() in KNOWN_SHORTENERS:
            return True
        return False

def extract_signals(fetch: FetchResult) -> UrlSignals:
    """
    Convert FetchResult (what happened) into UrlSignals (measurable features).
    """

    chain = fetch.redirect_chain or []
    initial_url = chain[0] if chain else None

    initial_host = _host(initial_url) if initial_url else None
    final_host = _host(fetch.final_url) if fetch.final_url else None

    return UrlSignals(
        redirect_count=len(chain) - 1 if len(chain) > 0 else 0,
        redirect_chain=chain,
        initial_host=initial_host,
        final_host=final_host,
        hostname_changed=(initial_host is not None and final_host is not None and initial_host != final_host),
        used_shortener=_uses_shortener(chain),

        http_status=fetch.status_code,
        status_family=_status_family(fetch.status_code),
        content_type=fetch.content_type,
        content_category=_content_category(fetch.content_type),
        server=fetch.server,

        security_headers_present={
            "strict-transport-security": "strict-transport-security" in (fetch.headers or {}),
            "content-security-policy": "content-security-policy" in (fetch.headers or {}),
            "x-frame-options": "x-frame-options" in (fetch.headers or {}),
            "x-content-type-options": "x-content-type-options" in (fetch.headers or {}),
            "referrer-policy": "referrer-policy" in (fetch.headers or {}),
            "permissions-policy": "permissions-policy" in (fetch.headers or {}),
        },
    )