# prepare_urlhaus_ml_csv.py
from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse

import pandas as pd


INPUT_PATH = Path("/mnt/data/malwareurls.csv")  # your uploaded file
OUTPUT_PATH = Path("data/urlhaus_ml.csv")


def _read_urlhaus_csv(path: Path) -> pd.DataFrame:
    """
    Reads URLhaus 'CSV dump' files that contain comment lines and a commented header.
    Returns a DataFrame with columns like: id, dateadded, url, url_status, ...
    """
    if not path.exists():
        raise FileNotFoundError(f"Input not found: {path}")

    header: Optional[List[str]] = None
    rows: List[List[str]] = []

    with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Skip comment blocks
            if line.startswith("################################################################"):
                continue

            # Header line is commented like: "# id,dateadded,url,..."
            if line.startswith("#") and "url" in line.lower() and "," in line:
                # remove leading "#", then split by comma
                header_line = line.lstrip("#").strip()
                header = [h.strip().strip('"') for h in header_line.split(",")]
                continue

            # Other comment lines
            if line.startswith("#"):
                continue

            # Data lines are standard CSV (often quoted)
            # Use csv.reader on a single line
            parsed = next(csv.reader([line]))
            rows.append(parsed)

    if header is None:
        # Fallback: known URLhaus order (in case header missing)
        header = [
            "id",
            "dateadded",
            "url",
            "url_status",
            "last_online",
            "threat",
            "tags",
            "urlhaus_link",
            "reporter",
        ]

    df = pd.DataFrame(rows, columns=header[: len(rows[0])])  # guard if fewer cols
    return df


_ip_re = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")


def _safe_hostname(parsed) -> str:
    return parsed.hostname or ""


def _url_features(url: str) -> Dict[str, float]:
    """
    URL-only numeric features (safe, no fetching).
    """
    u = url.strip()
    p = urlparse(u)

    hostname = _safe_hostname(p)
    is_ip = 1.0 if _ip_re.match(hostname) else 0.0

    path = p.path or ""
    query = p.query or ""

    # counts
    digits = sum(ch.isdigit() for ch in u)
    letters = sum(ch.isalpha() for ch in u)
    specials = len(u) - digits - letters

    # basic structure
    dot_count = u.count(".")
    slash_count = u.count("/")
    hyphen_count = u.count("-")
    at_count = u.count("@")
    qmark_count = u.count("?")
    eq_count = u.count("=")
    amp_count = u.count("&")

    # host/subdomain-ish
    host_parts = [x for x in hostname.split(".") if x]
    subdomain_count = float(max(0, len(host_parts) - 2)) if len(host_parts) >= 2 else 0.0
    tld_len = float(len(host_parts[-1])) if host_parts else 0.0

    return {
        "url_len": float(len(u)),
        "num_digits": float(digits),
        "num_letters": float(letters),
        "num_specials": float(max(0, specials)),
        "dot_count": float(dot_count),
        "slash_count": float(slash_count),
        "hyphen_count": float(hyphen_count),
        "at_count": float(at_count),
        "qmark_count": float(qmark_count),
        "eq_count": float(eq_count),
        "amp_count": float(amp_count),
        "uses_https": 1.0 if p.scheme.lower() == "https" else 0.0,
        "host_len": float(len(hostname)),
        "is_ip_host": is_ip,
        "subdomain_count": subdomain_count,
        "tld_len": tld_len,
        "path_len": float(len(path)),
        "query_len": float(len(query)),
    }


def main() -> None:
    df = _read_urlhaus_csv(INPUT_PATH)

    if "url" not in df.columns:
        raise ValueError(f"'url' column not found. Columns: {list(df.columns)}")

    # Build ML dataset (label=1 for URLhaus / malicious)
    feat_rows = []
    for u in df["url"].astype(str):
        feats = _url_features(u)
        feats["label"] = 1  # positive class
        feats["url"] = u
        feat_rows.append(feats)

    out_df = pd.DataFrame(feat_rows)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")

    print(f"✅ Parsed {len(df)} URLhaus rows")
    print(f"✅ Wrote ML-ready CSV: {OUTPUT_PATH}")
    print(f"Columns: {list(out_df.columns)}")


if __name__ == "__main__":
    main()
