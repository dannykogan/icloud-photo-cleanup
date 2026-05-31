# iCloud Photo Cleanup

**Three steps: download, analyze, clean up.**

### 1. Download

```bash
git clone https://github.com/dannykogan/icloud-photo-cleanup.git
cd icloud-photo-cleanup
```

### 2. Analyze - see what would be deleted

```bash
python3 analyze.py
```

Scans your Photos library and prints a count of screenshots, duplicates, and low-quality shots. **Nothing is touched** - this is read-only.

### 3. Clean up - move them to Recently Deleted

```bash
swift cleanup.swift
```

Moves everything from the analysis to **Recently Deleted**. Nothing is permanently gone - you have a 30-day window to review and recover anything before it's truly deleted.

> **Favorites are excluded by default.** Any photo you've hearted in Photos is safe unless you explicitly change that setting.

### 4. Review and confirm

Open **Photos > Albums > Recently Deleted**, look through, and hit **Delete All** when you're happy.

---

## What gets removed

| Category | How it's detected |
|---|---|
| **Screenshots** | `ZISDETECTEDSCREENSHOT = 1` (Apple's own AI flag) |
| **Duplicates** | `ZDUPLICATEASSETVISIBILITYSTATE = 2` (Photos' built-in duplicate detection, keeps the better copy) |
| **Low quality** | `ZOVERALLAESTHETICSCORE < 0.32` (Apple's aesthetic scoring, 0-1 scale) |

---

## Configuration

Edit the top of `analyze.py` to tune the aggressiveness:

```python
# Aesthetic score threshold (0.0-1.0)
QUALITY_THRESHOLD = 0.32   # 0.2 = conservative, 0.32 = recommended, 0.4 = aggressive

# Include favorited photos in the low-quality sweep?
INCLUDE_FAVORITES = False  # default: favorites are protected
```

---

## How it works

macOS Photos stores its full library metadata in a SQLite database at:
```
~/Pictures/Photos Library.photoslibrary/database/Photos.sqlite
```

The key tables/columns used:

- `ZASSET.ZISDETECTEDSCREENSHOT` - Apple's on-device ML screenshot detection
- `ZASSET.ZDUPLICATEASSETVISIBILITYSTATE` - 1 = keep, 2 = redundant copy
- `ZASSET.ZOVERALLAESTHETICSCORE` - Apple's aesthetic score (blur, exposure, composition)
- `ZASSET.ZUUID` - local identifier, matches `PHAsset.localIdentifier`

`analyze.py` reads these directly (read-only). `cleanup.swift` uses `PHPhotoLibrary.shared().performChanges` to delete - the same API the Photos app uses internally, so iCloud sync is handled correctly.

---

## Requirements

- macOS 13+ (Ventura or later)
- iCloud Photos enabled and synced
- Python 3 (pre-installed on macOS)
- Swift (pre-installed on macOS via Xcode Command Line Tools)
- Terminal must have permission to control Photos: **System Settings > Privacy & Security > Automation > Terminal > Photos**

---

## Safety notes

- **Non-destructive first pass:** everything goes to Recently Deleted, not permanent deletion
- **Favorites are excluded by default** - set `INCLUDE_FAVORITES = True` in `analyze.py` to include them
- **Videos are excluded** from the quality sweep (only photos are scored)
- The SQLite database is opened read-only by `analyze.py` - it never writes to the DB
