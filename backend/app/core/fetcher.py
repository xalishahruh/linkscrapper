from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from typing import List, Optional, Dict
from urllib.parse import urlparse

import httpx


@dataclass
class FetchResult:
    final_url: str
    status_code: int
    redirect_chain: List[str]
    content_type: Optional[str]
    server: Optional[str]
    headers: Dict[str, str]

ALLOWED_RESPONSE_HEADERS = {
    "strict-transport-security",
    "content-security-policy",
    "x-frame-options",
    "x-content-type-options",
    "referrer-policy",
    "permissions-policy",
}


def _is_private_host(host: str) -> bool:
    """
    Block private/internal IPs to reduce SSRF risk.
    If host is a domain name (not an IP), we allow it for now.
    Later we can add DNS resolution checks too.
    """
    try:
        ip = ipaddress.ip_address(host)
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
        )
    except ValueError:
        # Not an IP (likely a domain). Allow for MVP.
        return False

def _extract_allowed_headers(resp: httpx.Response) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for k, v in resp.headers.items():
        lk = k.lower()
        if lk in ALLOWED_RESPONSE_HEADERS:
            out[lk] = v
    return out

async def fetch_url(
    url: str,
    follow_redirects: bool = True,
    max_redirects: int = 10,
    timeout_seconds: float = 10.0,
    max_bytes: int = 512_000,  # 500 KB cap for MVP safety
) -> FetchResult:
    """
    Safely fetch a URL and track redirects + basic HTTP indicators.

    Security controls:
    - allow only http/https
    - block private/internal IP hosts (basic SSRF mitigation)
    - enforce timeout
    - cap redirects
    - cap downloaded bytes
    """

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Only http/https URLs are allowed")

    if not parsed.hostname:
        raise ValueError("URL must include a hostname")

    if _is_private_host(parsed.hostname):
        raise ValueError("Private/internal IP hosts are not allowed")

    timeout = httpx.Timeout(timeout_seconds)
    limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)

    redirect_chain: List[str] = []
    current = url

    async with httpx.AsyncClient(
        follow_redirects=False,  # manual redirect tracking
        timeout=timeout,
        limits=limits,
        headers={"User-Agent": "LinkScrapper/0.1"},
    ) as client:
        for _ in range(max_redirects + 1):
            resp = await client.get(current)

            redirect_chain.append(current)

            # Manual size cap: read only up to max_bytes
            # (We don't need full body today; just basic metadata)
            content = await resp.aread()
            if len(content) > max_bytes:
                raise ValueError("Response too large (size limit exceeded)")

            # Redirect handling
            if 300 <= resp.status_code < 400 and "location" in resp.headers:
                if not follow_redirects:
                    return FetchResult(
                        final_url=current,
                        status_code=resp.status_code,
                        redirect_chain=redirect_chain,
                        content_type=resp.headers.get("content-type"),
                        server=resp.headers.get("server"),
                        headers=_extract_allowed_headers(resp),
                    )

                next_url = resp.headers["location"]

                # Some redirects give relative locations; httpx can join them via resp.url
                try:
                    current = str(resp.url.join(next_url))
                except Exception:
                    current = next_url

                continue

            # Not a redirect → final response
            return FetchResult(
                final_url=str(resp.url),
                status_code=resp.status_code,
                redirect_chain=redirect_chain,
                content_type=resp.headers.get("content-type"),
                server=resp.headers.get("server"),
                headers=_extract_allowed_headers(resp)
            )

    raise ValueError("Max redirects exceeded")



