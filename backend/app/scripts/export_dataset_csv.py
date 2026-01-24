from __future__ import annotations

import argparse
import csv
import json
import os
import sqlite3
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


def iter_done_payloads(db_path: str) -> Iterable[Dict[str, Any]]:
    con = sqlite3.connect(db_path)
    try:
        cur = con.cursor()
        cur.execute(
            """
            SELECT id, input_url, result_json
            FROM analyses
            WHERE status = 'done' AND result_json IS NOT NULL
            """
        )
        for analysis_id, input_url, result_json in cur.fetchall():
            try:
                payload = json.loads(result_json)
                payload.setdefault("analysis_id", analysis_id)
                payload.setdefault("url", input_url)
                yield payload
            except json.JSONDecodeError:
                continue
    finally:
        con.close()


def collect_feature_keys(payloads: List[Dict[str, Any]]) -> List[str]:
    keys: Set[str] = set()
    for p in payloads:
        feats = p.get("features")
        if isinstance(feats, dict):
            keys.update(feats.keys())
    return sorted(keys)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export LinkScrapper dataset from SQLite to flattened CSV.")
    parser.add_argument("--db", default="linkscrapper.db", help="Path to SQLite DB file (default: linkscrapper.db)")
    parser.add_argument("--out", default=os.path.join("data", "dataset.csv"), help="Output CSV path")
    parser.add_argument("--label", default=None, help="Optional label to attach to every row (0/1).")
    args = parser.parse_args()

    label_val: Optional[int] = None if args.label is None else int(args.label)

    payloads = list(iter_done_payloads(args.db))
    if not payloads:
        print("No completed analyses found to export.")
        return

    feature_keys = collect_feature_keys(payloads)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    # CSV columns: id, url, optional label, then each feature column
    fieldnames = ["analysis_id", "url"]
    if label_val is not None:
        fieldnames.append("label")
    fieldnames.extend(feature_keys)

    n_written = 0
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for p in payloads:
            feats = p.get("features")
            if not isinstance(feats, dict) or not feats:
                continue

            row: Dict[str, Any] = {
                "analysis_id": p.get("analysis_id"),
                "url": p.get("url"),
            }
            if label_val is not None:
                row["label"] = label_val

            # fill features (missing -> 0)
            for k in feature_keys:
                v = feats.get(k, 0)
                row[k] = v

            writer.writerow(row)
            n_written += 1

    print(f"✅ Exported {n_written} rows to {args.out}")


if __name__ == "__main__":
    main()
