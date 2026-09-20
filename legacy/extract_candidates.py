import json
import shutil
from pathlib import Path

# Paths
WLASL_DIR = Path("WLASL")
RAW_VIDEOS = WLASL_DIR / "raw_videos"
META_FILE = WLASL_DIR / "WLASL_v0.3.json"

VOCAB_FILE = Path("vocab.txt")
OUT_DIR = Path("curated_candidates")

OUT_DIR.mkdir(exist_ok=True)

# Load vocabulary
with open(VOCAB_FILE, "r") as f:
    vocab = {line.strip().lower() for line in f if line.strip()}

# Load metadata
with open(META_FILE, "r") as f:
    metadata = json.load(f)

found = {}

for entry in metadata:
    gloss = entry["gloss"].lower()

    if gloss not in vocab:
        continue

    for inst in entry["instances"]:
        video_id = inst["video_id"]
        src = RAW_VIDEOS / f"{video_id}.mp4"

        if src.exists():
            dest_dir = OUT_DIR / gloss
            dest_dir.mkdir(exist_ok=True)

            dest = dest_dir / f"{video_id}.mp4"
            if not dest.exists():
                shutil.copy(src, dest)
                found.setdefault(gloss, 0)
                found[gloss] += 1

# Summary
print("Extraction complete.")
print("Words found:")
for word, count in found.items():
    print(f"{word}: {count} candidate video(s)")
