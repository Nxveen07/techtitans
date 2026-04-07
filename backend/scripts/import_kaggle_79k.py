import argparse
import csv
import sys
from pathlib import Path

# Make backend root importable when running from scripts/
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from db.models import DatasetSample
from db.session import SessionLocal


TEXT_CANDIDATES = ["content", "text", "article", "statement", "claim", "body"]
LABEL_CANDIDATES = ["label", "target", "class", "is_fake", "fake"]
TITLE_CANDIDATES = ["title", "headline"]


def normalize_label(raw: str) -> str | None:
    if raw is None:
        return None
    value = str(raw).strip().lower()
    if value == "":
        return None

    # Numeric/binary labels
    if value in {"1", "true", "real", "reliable", "verified"}:
        return "verified"
    if value in {"0", "false", "fake", "misinformation", "unreliable", "suspicious"}:
        return "suspicious"
    if value in {"2", "unknown", "uncertain", "unverified", "mixed"}:
        return "unverified"

    # Loose text mapping
    if "fake" in value or "misinfo" in value or "rumor" in value:
        return "suspicious"
    if "real" in value or "true" in value or "fact" in value:
        return "verified"
    if "unverified" in value or "uncertain" in value or "unknown" in value:
        return "unverified"
    return None


def pick_column(fieldnames: list[str], candidates: list[str]) -> str | None:
    lower_map = {name.lower(): name for name in fieldnames}
    for candidate in candidates:
        if candidate in lower_map:
            return lower_map[candidate]
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Import Kaggle fake-news CSV into dataset_samples.")
    parser.add_argument("--csv", required=True, help="Path to Kaggle CSV file")
    parser.add_argument("--limit", type=int, default=0, help="Optional max rows to import (0 = all)")
    parser.add_argument("--offset", type=int, default=0, help="Skip first N rows from CSV before importing")
    parser.add_argument("--source-type", default="kaggle_79k", help="source_type value to store")
    parser.add_argument("--split", default="unsplit", help="Initial split value (default: unsplit)")
    parser.add_argument(
        "--force-label",
        choices=["verified", "suspicious", "unverified"],
        default=None,
        help="Force all imported rows to a single label (useful for files split by class).",
    )
    args = parser.parse_args()
    csv.field_size_limit(10 * 1024 * 1024)

    csv_path = Path(args.csv)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    imported = 0
    skipped = 0

    db = SessionLocal()
    try:
        with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                raise RuntimeError("CSV has no headers.")

            text_col = pick_column(reader.fieldnames, TEXT_CANDIDATES)
            label_col = pick_column(reader.fieldnames, LABEL_CANDIDATES)
            title_col = pick_column(reader.fieldnames, TITLE_CANDIDATES)

            if text_col is None:
                raise RuntimeError(
                    f"Could not find text column. Available columns: {reader.fieldnames}"
                )
            if label_col is None and args.force_label is None:
                raise RuntimeError(
                    f"Could not find label column. Available columns: {reader.fieldnames}. "
                    "Use --force-label for class-specific files."
                )

            for idx, row in enumerate(reader):
                if idx < args.offset:
                    continue
                raw_text = (row.get(text_col) or "").strip()
                raw_title = (row.get(title_col) or "").strip() if title_col else ""
                mapped = args.force_label
                if mapped is None:
                    raw_label = row.get(label_col)
                    mapped = normalize_label(raw_label)

                if not mapped:
                    skipped += 1
                    continue

                if raw_title and raw_title.lower() not in raw_text.lower():
                    content = f"{raw_title}. {raw_text}".strip()
                else:
                    content = raw_text

                if len(content) < 5:
                    skipped += 1
                    continue

                db.add(
                    DatasetSample(
                        content=content[:4000],
                        label=mapped,
                        source_type=args.source_type,
                        split=args.split,
                    )
                )
                imported += 1

                if imported % 1000 == 0:
                    db.commit()
                    print(f"Imported {imported} rows...")

                if args.limit > 0 and imported >= args.limit:
                    break

            db.commit()
    finally:
        db.close()

    print(f"Import complete. imported={imported}, skipped={skipped}")


if __name__ == "__main__":
    main()
