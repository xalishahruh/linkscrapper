from __future__ import annotations

from typing import Dict
from backend.app.core.signals import UrlSignals

def signals_to_features(s:UrlSignals) -> Dict[str, float]:

    features: Dict[str, float] = {}
    #main behaviours
    features["redirect_count"] = float(s.redirect_count)
    features["hostname_changed"] = 1.00 if s.hostname_changed else 0.0
    features["used_shortener"] = 1.00 if s.used_shortener else 0.0

    #http based
    features["status_2xx"] = 1.0 if s.status_family == "2xx" else 0.0
    features["status_3xx"] = 1.0 if s.status_family == "3xx" else 0.0
    features["status_4xx"] = 1.0 if s.status_family == "4xx" else 0.0
    features["status_5xx"] = 1.0 if s.status_family == "5xx" else 0.0
    features["status_other"] = 1.0 if s.status_family == "other" else 0.0


    #content based
    features["content_html"] = 1.0 if s.content_category == "html" else 0.0
    features["content_json"] = 1.0 if s.content_category == "json" else 0.0
    features["content_text"] = 1.0 if s.content_category == "text" else 0.0
    features["content_download"] = 1.0 if s.content_category == "download" else 0.0
    features["content_unknown"] = 1.0 if s.content_category == "unknown" else 0.0

    #security headers based
    hdr = s.security_headers_present or {}
    features["hdr_hsts"] = 1.0 if hdr.get("strict-transport-security", False) else 0.0
    features["hdr_csp"] = 1.0 if hdr.get("content-security-policy", False) else 0.0
    features["hdr_xfo"] = 1.0 if hdr.get("x-frame-options", False) else 0.0
    features["hdr_xcto"] = 1.0 if hdr.get("x-content-type-options", False) else 0.0
    features["hdr_referrer_policy"] = 1.0 if hdr.get("referrer-policy", False) else 0.0
    features["hdr_permissions_policy"] = 1.0 if hdr.get("permissions-policy", False) else 0.0

    return features