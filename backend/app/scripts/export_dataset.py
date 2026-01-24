from __future__ import annotations

import argparse
import json
import os
import sqlite3
from typing import Any, Dict, Iterable, Optional

from pyexpat import features


def iter_done_result(db_path: str) -> Iterable[Dict[str, Any]]:
    con = sqlite3.connect(db_path)
    try:
        cur = con.cursor()
        cur.execute(  """
            SELECT id, input_url, result_json
            FROM analyses
            WHERE status = 'done' AND result_json IS NOT NULL
            """)
        for analysis_id, input_url, result_json in cur.fetchall():
            try:
                payload = json.loads(result_json)
                payload.setdefault("url", input_url)
                payload.setdefault("analysis_id", analysis_id)
                yield payload
            except json.JSONDecodeError:
                continue
    finally:
        con.close()


def payload_to_dataset_row(payload: Dict[str, Any], label: Optional[int] = None):
    features = payload.get("features")
    if not isinstance(features, dict) or not features:
        return None

    row:Dict[str, Any] = {
        "analysis_id": payload.get("analysis_id"),
        "url": payload.get("url"),
        "features": features,
    }
    if label is not None:
        row["label"] = int(label)


    return row


def main() -> None:
    parser = argparse.ArgumentParser(description="Export LinkScrapper dataset from SQLite to JSONL.")
    parser.add_argument("--db", default="linkscrapper.db", help="Path to SQLite DB file (default: linkscrapper.db)")
    parser.add_argument("--out", default=os.path.join("data", "dataset.jsonl"), help="Output JSONL path")
    parser.add_argument(
        "--label",
        default=None,
        help="Optional label to attach to every row (e.g., 0 for benign). Leave empty for unlabeled export.",
    )
    args = parser.parse_args()

    label_val: Optional[int]
    if args.label is None:
        label_val = None
    else:
        label_val = int(args.label)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    n_written = 0
    with open(args.out, "w", encoding="utf-8") as f:
        for payload in iter_done_result(args.db):
            row = payload_to_dataset_row(payload, label=label_val)
            if row is None:
                continue
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            n_written += 1

    print(f"Exported {n_written} rows to {args.out}")


if __name__ == "__main__":
    main()