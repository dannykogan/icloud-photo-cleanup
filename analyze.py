#!/usr/bin/env python3
"""
analyze.py — Scan your iCloud Photos library and report what can be cleaned up.

Usage:
    python3 analyze.py

Outputs a summary + writes uuids_to_delete.txt for use with cleanup.swift.
"""

import sqlite3
import os
from datetime import datetime, timezone, timedelta

LIBRARY_PATH = os.path.expanduser("~/Pictures/Photos Library.photoslibrary")
DB_PATH = os.path.join(LIBRARY_PATH, "database/Photos.sqlite")

# ── Config ────────────────────────────────────────────────────────────────────
# Aesthetic score threshold (0.0–1.0). Lower = more aggressive cleanup.
# 0.2  → ~1,900 photos  (conservative: obviously bad shots only)
# 0.32 → ~4,800 photos  (recommended: bad + mediocre)
# 0.4  → ~8,600 photos  (aggressive: anything below average)
QUALITY_THRESHOLD = 0.32

# Set to True to also include favorited low-quality photos
INCLUDE_FAVORITES = True
# ─────────────────────────────────────────────────────────────────────────────

def ts(val):
    if val is None:
        return "Unknown"
    try:
        epoch = datetime(2001, 1, 1, tzinfo=timezone.utc)
        return (epoch + timedelta(seconds=float(val))).strftime("%Y-%m-%d")
    except Exception:
        return "Unknown"


def main():
    if not os.path.exists(DB_PATH):
        print(f"❌ Photos library not found at: {LIBRARY_PATH}")
        print("   Make sure iCloud Photos is set up on this Mac.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Total
    c.execute("SELECT COUNT(*) FROM ZASSET WHERE ZTRASHEDSTATE = 0;")
    total = c.fetchone()[0]

    c.execute("SELECT ZKIND, COUNT(*) FROM ZASSET WHERE ZTRASHEDSTATE = 0 GROUP BY ZKIND;")
    by_kind = {r[0]: r[1] for r in c.fetchall()}

    # Screenshots
    c.execute("SELECT COUNT(*) FROM ZASSET WHERE ZISDETECTEDSCREENSHOT = 1 AND ZTRASHEDSTATE = 0;")
    screenshot_count = c.fetchone()[0]

    # Duplicates
    c.execute("SELECT COUNT(*) FROM ZASSET WHERE ZDUPLICATEASSETVISIBILITYSTATE = 2 AND ZTRASHEDSTATE = 0;")
    dup_count = c.fetchone()[0]

    # Low quality
    fav_filter = "" if INCLUDE_FAVORITES else "AND ZFAVORITE = 0"
    c.execute(f"""
        SELECT COUNT(*) FROM ZASSET
        WHERE ZOVERALLAESTHETICSCORE < {QUALITY_THRESHOLD}
        AND ZTRASHEDSTATE = 0 AND ZKIND = 0
        AND ZISDETECTEDSCREENSHOT = 0
        AND ZDUPLICATEASSETVISIBILITYSTATE != 2
        {fav_filter}
    """)
    lowq_count = c.fetchone()[0]

    # Screenshots by year
    c.execute("""
        SELECT CAST(strftime('%Y', datetime(ZDATECREATED + 978307200, 'unixepoch')) AS INTEGER),
               COUNT(*)
        FROM ZASSET WHERE ZISDETECTEDSCREENSHOT = 1 AND ZTRASHEDSTATE = 0
        GROUP BY 1 ORDER BY 1
    """)
    ss_by_year = c.fetchall()

    # Collect UUIDs
    c.execute("SELECT ZUUID FROM ZASSET WHERE ZDUPLICATEASSETVISIBILITYSTATE = 2 AND ZTRASHEDSTATE = 0;")
    dup_uuids = [r[0] for r in c.fetchall()]

    c.execute("SELECT ZUUID FROM ZASSET WHERE ZISDETECTEDSCREENSHOT = 1 AND ZTRASHEDSTATE = 0;")
    ss_uuids = [r[0] for r in c.fetchall()]

    c.execute(f"""
        SELECT ZUUID FROM ZASSET
        WHERE ZOVERALLAESTHETICSCORE < {QUALITY_THRESHOLD}
        AND ZTRASHEDSTATE = 0 AND ZKIND = 0
        AND ZISDETECTEDSCREENSHOT = 0
        AND ZDUPLICATEASSETVISIBILITYSTATE != 2
        {fav_filter}
    """)
    lq_uuids = [r[0] for r in c.fetchall()]

    conn.close()

    all_uuids = list(set(dup_uuids + ss_uuids + lq_uuids))

    # Print report
    print("=" * 55)
    print("  iCloud Photo Library — Cleanup Analysis")
    print("=" * 55)
    print(f"  Total items:      {total:>8,}")
    print(f"  Photos:           {by_kind.get(0, 0):>8,}")
    print(f"  Videos:           {by_kind.get(1, 0):>8,}")
    print()
    print(f"  Screenshots:      {screenshot_count:>8,}")
    print(f"  Duplicates:       {dup_count:>8,}")
    print(f"  Low quality:      {lowq_count:>8,}  (score < {QUALITY_THRESHOLD})")
    print(f"  ─────────────────────────────")
    print(f"  Total to remove:  {len(all_uuids):>8,}")
    print("=" * 55)

    print("\nScreenshots by year:")
    for year, count in ss_by_year:
        bar = "█" * (count // 50)
        print(f"  {year}: {bar} {count:,}")

    # Write UUID file
    out_path = os.path.expanduser("~/Pictures/uuids_to_delete.txt")
    with open(out_path, "w") as f:
        f.write("\n".join(all_uuids))
    print(f"\n✅ UUID list written to: {out_path}")
    print(f"   Run cleanup.swift next to move these to Recently Deleted.")


if __name__ == "__main__":
    main()
