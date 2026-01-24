from __future__ import annotations

import csv
import json
import os
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]  # project root
    inp = root / "data" / "raw" / "malwareurls.csv"
    out_dir = root / "data" / "processed"
    out = out_dir / "urlhaus_pos.jsonl"

    if not inp.exists():
        raise FileNotFoundError(f"Input file not found: {inp}")

    os.makedirs(out_dir, exist_ok=True)

    n_in = 0
    n_written = 0

    with inp.open("r", encoding="utf-8", newline="") as f_in, out.open("w", encoding="utf-8") as f_out:
        # Skip comment lines starting with '#'
        for line in f_in:
            if not line.startswith("#"):
                header = line
                break
        else:
            raise ValueError("No CSV header found in file")

        reader = csv.DictReader([header] + list(f_in))

        if not reader.fieldnames or "url" not in reader.fieldnames:
            raise ValueError(f"Expected a CSV with a 'url' column. Found columns: {reader.fieldnames}")

        for row in reader:
            n_in += 1
            url = (row.get("url") or "").strip()
            if not url:
                continue

            # Label convention: 1 = malicious (positive)
            item = {
                "url": url,
                "label": 1,
                # keep some metadata (optional but helpful later)
                "threat": (row.get("threat") or "").strip(),
                "tags": (row.get("tags") or "").strip(),
                "source": "urlhaus",
            }

            f_out.write(json.dumps(item, ensure_ascii=False) + "\n")
            n_written += 1

    print(f"✅ Read {n_in} rows, wrote {n_written} positives to {out}")


if __name__ == "__main__":
    main()
