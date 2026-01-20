from __future__ import annotations

from dataclasses import dataclass
from typing import List

from backend.app.core.signals import UrlSignals


@dataclass
class RiskAssessment:
    risk_score: int
    risk_level: str
    reasons: List[str]


def _clamp(n: int, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, n))


def assess_risk(signals: UrlSignals) -> RiskAssessment:
    score = 0
    reasons: List[str] = []

    # 1) Redirects
    if signals.redirect_count >= 3:
        score += 25
        reasons.append(f"Multiple redirects observed ({signals.redirect_count})")
    elif signals.redirect_count == 2:
        score += 15
        reasons.append("Two redirects observed")
    elif signals.redirect_count == 1:
        score += 5
        reasons.append("One redirect observed")

    # 2) URL shorteners
    if signals.used_shortener:
        score += 25
        reasons.append("URL shortener used (destination hidden)")

    # 3) Host changed (initial vs final)
    if signals.hostname_changed:
        score += 15
        reasons.append("Destination hostname differs from initial hostname")

    # 4) Content category hints
    if signals.content_category == "download":
        score += 20
        reasons.append("Response looks like a download (non-HTML content type)")
    elif signals.content_category == "unknown":
        score += 5
        reasons.append("Unknown or missing content type")

    # 5) HTTP status family hints
    if signals.status_family == "4xx":
        score += 10
        reasons.append(f"Client error status returned ({signals.http_status})")
    elif signals.status_family == "5xx":
        score += 10
        reasons.append(f"Server error status returned ({signals.http_status})")

    # 6) Missing security headers (weak signal)
    missing_headers = []
    for key in (
        "strict-transport-security",
        "content-security-policy",
        "x-frame-options",
    ):
        if not signals.security_headers_present.get(key, False):
            missing_headers.append(key)

    if len(missing_headers) >= 3:
        score += 5
        reasons.append("Common security headers not observed (weak signal)")

    score = _clamp(score)

    if score >= 60:
        level = "high"
    elif score >= 25:
        level = "medium"
    else:
        level = "low"

    if not reasons:
        reasons.append("No obvious high-risk signals detected")

    return RiskAssessment(
        risk_score=score,
        risk_level=level,
        reasons=reasons,
    )