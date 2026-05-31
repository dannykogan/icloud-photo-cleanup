# iCloud Photo Cleanup

Two-script tool to bulk-clean your iCloud Photos library on macOS — removes screenshots, exact duplicates, and low-quality/blurry shots using Apple's own metadata.

**No third-party tools required.** Uses Python's built-in `sqlite3` to read the Photos database, and the native `PHPhotoLibrary` framework to delete safely.

---

## What it removes

| Category | How it's detected |
|---|---|
| **Screenshots** | `ZISDETECTEDSCREENSHOT = 1` (Apple's own AI flag) |
| **Duplicates** | `ZDUPLICATEASSETVISIBILITYSTATE = 2` (Photos' built-in duplicate detection, keeps the better copy) |
| **Low quality** | `ZOVERALLAESTHETICSCORE < 0.32` (Apple's aesthetic scoring, 0–1 scale) |

Everything goes to **Recently Deleted** first — nothing is permanently gone until you empty that album. You have a 30-day recovery window.

---

## Usage

### Step 1 — Analyze

```bash
python3 analyze.py
```

Scans your Photos library database and prints a report like:

```
=======================================================
  iCloud Photo Library — Cleanup Analysis
=======================================================
  Total items:         38,958
  Photos:              30,946
  Videos:               8,012

  Screenshots:          4,469
  Duplicates:             180
  Low quality:          4,862  (score < 0.32)
  ─────────────────────────────
  Total to remove:      9,503
=======================================================
```

Also writes `~/Pictures/uuids_to_delete.txt` for the next step.

### Step 2 — Clean up

```bash
swift cleanup.swift
```

- Reads the UUID list from Step 1
- Fetches the photos using the native Photos framework
- Shows a system confirmation dialog (Photos asks you to confirm)
- Moves everything to Recently Deleted

### Step 3 — Review & confirm

Open **Photos → Albums → Recently Deleted**, look through, and hit **Delete All** when you're happy.

---

## Configuration

Edit the top of `analyze.py` to tune the aggressiveness:

```python
# Aesthetic score threshold (0.0–1.0)
QUALITY_THRESHOLD = 0.32   # 0.2 = conservative, 0.32 = recommended, 0.4 = aggressive

# Include favorited photos in the low-quality sweep?
INCLUDE_FAVORITES = True
```

---

## How it works

macOS Photos stores its full library metadata in a SQLite database at:
```
~/Pictures/Photos Library.photoslibrary/database/Photos.sqlite
```

The key tables/columns used:

- `ZASSET.ZISDETECTEDSCREENSHOT` — Apple's on-device ML screenshot detection
- `ZASSET.ZDUPLICATEASSETVISIBILITYSTATE` — 1 = keep, 2 = redundant copy
- `ZASSET.ZOVERALLAESTHETICSCORE` — Apple's aesthetic score (blur, exposure, composition)
- `ZASSET.ZUUID` — local identifier, matches `PHAsset.localIdentifier`

`analyze.py` reads these directly (read-only). `cleanup.swift` uses `PHPhotoLibrary.shared().performChanges` to delete — the same API the Photos app uses internally, so iCloud sync is handled correctly.

---

## Requirements

- macOS 13+ (Ventura or later)
- iCloud Photos enabled and synced
- Python 3 (pre-installed on macOS)
- Swift (pre-installed on macOS via Xcode Command Line Tools)
- Terminal must have permission to control Photos: **System Settings → Privacy & Security → Automation → Terminal → Photos ✓**

---

## Safety notes

- **Non-destructive first pass:** everything goes to Recently Deleted, not permanent deletion
- **Favorites are excluded by default** — set `INCLUDE_FAVORITES = True` in `analyze.py` to include them
- **Videos are excluded** from the quality sweep (only photos are scored)
- The SQLite database is opened read-only by `analyze.py` — it never writes to the DB
