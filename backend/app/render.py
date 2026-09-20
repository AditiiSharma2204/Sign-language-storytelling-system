"""Video assembly: text cards, FFmpeg concatenation and subtitle files."""
import hashlib
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path

import cv2
import imageio_ffmpeg
import numpy as np

from .config import CARD_SECONDS, FPS, HEIGHT, OUTPUT_DIR, WIDTH

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
CARD_DIR = OUTPUT_DIR / "cards"
CARD_DIR.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=512)
def clip_duration(path: str) -> float:
    cap = cv2.VideoCapture(path)
    frames, fps = cap.get(cv2.CAP_PROP_FRAME_COUNT), cap.get(cv2.CAP_PROP_FPS)
    cap.release()
    return round(frames / fps, 3) if fps else 0.0


def encode_png(png: Path, seconds: float, out: Path) -> None:
    """Turn a still image into a clip using exactly the same encoder settings as normalize()."""
    subprocess.run(
        [FFMPEG, "-y", "-loglevel", "error", "-loop", "1", "-i", str(png), "-t", str(seconds),
         "-vf", f"fps={FPS},format=yuv420p", "-c:v", "libx264", "-preset", "veryfast",
         "-crf", "23", "-g", str(FPS), "-an", str(out)],
        check=True,
    )
    png.unlink(missing_ok=True)


def make_text_card(word: str) -> Path:
    """Render a short title card for a word that has no sign clip."""
    out = CARD_DIR / f"{word}.mp4"
    if out.exists():
        return out

    frame = np.full((HEIGHT, WIDTH, 3), (46, 27, 15), dtype=np.uint8)  # dark navy (BGR)
    text = word.upper()
    font, thickness = cv2.FONT_HERSHEY_DUPLEX, 3
    scale = 3.0
    while cv2.getTextSize(text, font, scale, thickness)[0][0] > WIDTH - 80 and scale > 0.6:
        scale -= 0.2
    (tw, th), _ = cv2.getTextSize(text, font, scale, thickness)
    cv2.putText(frame, text, ((WIDTH - tw) // 2, (HEIGHT + th) // 2 - 10),
                font, scale, (255, 255, 255), thickness, cv2.LINE_AA)
    label = "NO SIGN CLIP - TEXT CARD"
    (lw, _), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
    cv2.putText(frame, label, ((WIDTH - lw) // 2, HEIGHT - 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 170, 120), 1, cv2.LINE_AA)

    png = CARD_DIR / f"{word}.png"
    cv2.imwrite(str(png), frame)
    encode_png(png, CARD_SECONDS, out)
    return out


NORM_DIR = OUTPUT_DIR / "norm"
NORM_DIR.mkdir(parents=True, exist_ok=True)


def normalize(clip: Path) -> Path:
    """Re-encode a clip once to the uniform output format (cached on disk)."""
    out = NORM_DIR / f"{clip.parent.name}_{clip.stem}.mp4"
    if out.exists() and out.stat().st_mtime >= clip.stat().st_mtime:
        return out
    vf = (f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,"
          f"pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={FPS},format=yuv420p")
    subprocess.run(
        [FFMPEG, "-y", "-loglevel", "error", "-i", str(clip), "-vf", vf,
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-g", str(FPS),
         "-an", str(out)],
        check=True,
    )
    return out


def concat_clips(clips: list[Path], out_path: Path) -> None:
    """Join normalized clips losslessly (identical streams, so stream copy is safe)."""
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        for c in clips:
            f.write(f"file '{c.resolve().as_posix()}'\n")
        listing = f.name
    try:
        subprocess.run(
            [FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
             "-i", listing, "-c", "copy", "-movflags", "+faststart", str(out_path)],
            check=True,
        )
    finally:
        Path(listing).unlink(missing_ok=True)


def cache_key(clips: list[Path]) -> str:
    return hashlib.sha1("|".join(c.name for c in clips).encode()).hexdigest()[:16]


def _ts(seconds: float, sep: str) -> str:
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02}{sep}{ms:03}"


def write_subtitles(timeline: list[dict], vtt_path: Path, srt_path: Path) -> None:
    vtt, srt = ["WEBVTT", ""], []
    for i, seg in enumerate(timeline, 1):
        label = seg["label"]
        vtt += [f"{_ts(seg['start'], '.')} --> {_ts(seg['end'], '.')}", label, ""]
        srt += [str(i), f"{_ts(seg['start'], ',')} --> {_ts(seg['end'], ',')}", label, ""]
    vtt_path.write_text("\n".join(vtt), encoding="utf-8")
    srt_path.write_text("\n".join(srt), encoding="utf-8")
