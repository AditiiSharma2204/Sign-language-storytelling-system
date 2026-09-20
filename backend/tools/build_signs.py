"""Expand the sign vocabulary from WLASL videos that are already downloaded.

For every gloss that has at least one usable local video and is not already in the hand-curated
set (asl_videos_std/), pick the best-looking instance, trim it to the annotated frame range, crop
to the signer's bounding box, standardise it to 640x480 @ 30 fps H.264 and save it to
asl_videos_wlasl/. A manifest records where each clip came from.

Run from the backend folder:
    python -m tools.build_signs            # build everything
    python -m tools.build_signs --dry-run  # only report what would be built
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import AUTO_SIGNS_DIR, EXTRA_VOCAB_FILE, FPS, HEIGHT, ROOT, SIGNS_DIR, WIDTH  # noqa: E402
from app.render import FFMPEG  # noqa: E402

WLASL = ROOT / "WLASL"
RAW = WLASL / "raw_videos"

# Glosses whose English word has several unrelated senses, so a single clip would often be the
# wrong sign. Better to fingerspell these than to show a confidently wrong sign.
AMBIGUOUS = {
    "bar", "can", "right", "check", "cheat", "last", "cool", "fine", "change", "pull",
    "letter", "class", "orange", "color", "corn", "bowling", "cool", "full", "same",
}

MIN_SECONDS, MAX_SECONDS = 0.6, 5.0
MIN_CROP_HEIGHT = 160  # px of the signer region in the source video


def probe(path: Path):
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return None
    info = dict(w=int(cap.get(3)), h=int(cap.get(4)), n=int(cap.get(7)), fps=cap.get(5))
    cap.release()
    return info if info["w"] and info["h"] and info["n"] and info["fps"] else None


def frame_range(inst: dict, n: int):
    start = max(inst["frame_start"], 1) - 1
    end = n - 1 if inst["frame_end"] in (-1, 0) else min(inst["frame_end"], n) - 1
    return start, max(end, start)


def clamp_box(box, w, h):
    x1, y1, x2, y2 = box
    x1, y1 = max(0, min(x1, w - 2)), max(0, min(y1, h - 2))
    x2, y2 = max(x1 + 2, min(x2, w)), max(y1 + 2, min(y2, h))
    return x1, y1, x2, y2


def sharpness(path: Path, box, start, end) -> float:
    """Mean Laplacian variance over a few frames of the cropped signer region."""
    cap = cv2.VideoCapture(str(path))
    scores = []
    for frac in (0.25, 0.5, 0.75):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(start + (end - start) * frac))
        ok, frame = cap.read()
        if not ok:
            continue
        x1, y1, x2, y2 = box
        crop = frame[y1:y2, x1:x2]
        # compare at a common size so high-resolution sources are not favoured twice
        crop = cv2.resize(crop, (240, 320))
        scores.append(cv2.Laplacian(cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var())
    cap.release()
    return sum(scores) / len(scores) if scores else 0.0


def best_instance(instances):
    best = None
    for inst in instances:
        path = RAW / f"{inst['video_id']}.mp4"
        info = probe(path) if path.exists() else None
        if not info:
            continue
        start, end = frame_range(inst, info["n"])
        seconds = (end - start + 1) / info["fps"]
        box = clamp_box(inst["bbox"], info["w"], info["h"])
        if not MIN_SECONDS <= seconds <= MAX_SECONDS or box[3] - box[1] < MIN_CROP_HEIGHT:
            continue
        score = sharpness(path, box, start, end)
        if best is None or score > best["score"]:
            best = dict(inst=inst, path=path, info=info, start=start, end=end, box=box,
                        seconds=round(seconds, 2), score=round(score, 1))
    return best


def render(c: dict, out: Path):
    x1, y1, x2, y2 = c["box"]
    vf = (f"trim=start_frame={c['start']}:end_frame={c['end'] + 1},setpts=PTS-STARTPTS,"
          f"crop={x2 - x1}:{y2 - y1}:{x1}:{y1},"
          f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,"
          f"pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={FPS},format=yuv420p")
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(c["path"]), "-vf", vf,
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-g", str(FPS),
                    "-an", str(out)], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    meta = json.loads((WLASL / "WLASL_v0.3.json").read_text())
    have_raw = {p.stem for p in RAW.glob("*.mp4")}
    curated = {p.stem for p in SIGNS_DIR.glob("*.mp4")}
    AUTO_SIGNS_DIR.mkdir(exist_ok=True)

    manifest, skipped = [], {"curated": 0, "ambiguous": [], "no_usable_clip": []}
    for entry in sorted(meta, key=lambda e: e["gloss"]):
        gloss = entry["gloss"].lower()
        local = [i for i in entry["instances"] if i["video_id"] in have_raw]
        if not local or not gloss.isalpha():
            continue
        if gloss in curated:
            skipped["curated"] += 1
        elif gloss in AMBIGUOUS:
            skipped["ambiguous"].append(gloss)
        else:
            best = best_instance(local)
            if not best:
                skipped["no_usable_clip"].append(gloss)
                continue
            if not args.dry_run:
                render(best, AUTO_SIGNS_DIR / f"{gloss}.mp4")
            inst = best["inst"]
            manifest.append(dict(gloss=gloss, video_id=inst["video_id"], source=inst["source"],
                                 signer_id=inst["signer_id"], seconds=best["seconds"],
                                 sharpness=best["score"], candidates=len(local)))
            print(f"{gloss:14} {best['seconds']:>4}s  from {inst['source']:<12} ({len(local)} candidates)")

    print(f"\nbuilt {len(manifest)} signs; kept {skipped['curated']} curated; "
          f"ambiguous skipped: {skipped['ambiguous']}; no usable clip: {skipped['no_usable_clip']}")
    if not args.dry_run:
        (AUTO_SIGNS_DIR / "_manifest.json").write_text(json.dumps(manifest, indent=1))
        EXTRA_VOCAB_FILE.write_text("
".join(sorted(m["gloss"] for m in manifest)) + "
")


if __name__ == "__main__":
    main()
