"""Fingerspelling: spell out words that have no sign, letter by letter.

Letter assets are looked up in `fingerspelling/` as a.png ... z.png (also .jpg, .jpeg, .webp
or a short .mp4). A letter without an asset is rendered as a large letter card, so the
feature works out of the box and improves as real hand-shape images are added.
"""
import hashlib
from pathlib import Path

import cv2
import numpy as np

from . import render
from .config import (
    FINGERSPELL_DIR, HEIGHT, LETTER_GAP_SECONDS, LETTER_SECONDS, OUTPUT_DIR, WIDTH,
)

LETTER_DIR = OUTPUT_DIR / "letters"
SPELL_DIR = OUTPUT_DIR / "spell"
LETTER_DIR.mkdir(parents=True, exist_ok=True)
SPELL_DIR.mkdir(parents=True, exist_ok=True)

ALPHABET = "abcdefghijklmnopqrstuvwxyz"
_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".mp4")
_BG = (46, 27, 15)  # dark navy (BGR), matches the text cards


def find_asset(letter: str) -> Path | None:
    for ext in _EXTS:
        p = FINGERSPELL_DIR / f"{letter}{ext}"
        if p.exists():
            return p
    return None


def alphabet_status() -> dict:
    have = [c for c in ALPHABET if find_asset(c)]
    return {"letters_with_assets": len(have), "missing": [c for c in ALPHABET if c not in have]}


def _stamp(letter: str) -> str:
    """Cache key that changes when the asset for a letter is added or replaced."""
    asset = find_asset(letter)
    raw = f"{asset.name}:{asset.stat().st_mtime_ns}" if asset else "card"
    return hashlib.sha1(raw.encode()).hexdigest()[:8]


def _draw_label(frame: np.ndarray, letter: str, big: bool) -> None:
    text = letter.upper()
    font = cv2.FONT_HERSHEY_DUPLEX
    if big:
        scale, thick = 7.0, 8
        (tw, th), _ = cv2.getTextSize(text, font, scale, thick)
        cv2.putText(frame, text, ((WIDTH - tw) // 2, (HEIGHT + th) // 2 - 20),
                    font, scale, (255, 255, 255), thick, cv2.LINE_AA)
        note = "FINGERSPELLING - LETTER CARD"
        (nw, _), _ = cv2.getTextSize(note, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
        cv2.putText(frame, note, ((WIDTH - nw) // 2, HEIGHT - 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 170, 120), 1, cv2.LINE_AA)


_PAPER = (250, 246, 244)  # light card (BGR) so dark line-art hands stay readable


def _hand_frame(asset: Path, letter: str) -> np.ndarray | None:
    """Place a hand-shape image on a light card: flatten transparency, crop margins, fit, label."""
    img = cv2.imread(str(asset), cv2.IMREAD_UNCHANGED)
    if img is None:
        return None
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    if img.shape[2] == 4:
        alpha = img[..., 3:4].astype(np.float32) / 255.0
        paper = np.full(img[..., :3].shape, _PAPER, dtype=np.float32)
        ys, xs = np.where(img[..., 3] > 8)
        img = (img[..., :3] * alpha + paper * (1 - alpha)).astype(np.uint8)
        if len(ys):  # crop transparent margins
            pad = 12
            img = img[max(ys.min() - pad, 0):ys.max() + pad, max(xs.min() - pad, 0):xs.max() + pad]

    box_w, box_h = WIDTH - 60, HEIGHT - 40
    scale = min(box_w / img.shape[1], box_h / img.shape[0])
    w, h = max(1, int(img.shape[1] * scale)), max(1, int(img.shape[0] * scale))
    img = cv2.resize(img, (w, h), interpolation=cv2.INTER_AREA)

    frame = np.full((HEIGHT, WIDTH, 3), _PAPER, dtype=np.uint8)
    y0, x0 = (HEIGHT - h) // 2, (WIDTH - w) // 2
    frame[y0:y0 + h, x0:x0 + w] = img
    cv2.putText(frame, letter.upper(), (24, 64), cv2.FONT_HERSHEY_DUPLEX, 2.0, (60, 40, 30), 3, cv2.LINE_AA)
    return frame


def letter_clip(letter: str) -> Path:
    """Return a normalised clip for one letter (cached)."""
    out = LETTER_DIR / f"{letter}-{_stamp(letter)}.mp4"
    if out.exists():
        return out

    asset = find_asset(letter)
    if asset is not None and asset.suffix == ".mp4":
        clip = render.normalize(asset)
        out.write_bytes(clip.read_bytes())
        return out

    frame = _hand_frame(asset, letter) if asset is not None else None
    if frame is None:
        frame = np.full((HEIGHT, WIDTH, 3), _BG, dtype=np.uint8)
        _draw_label(frame, letter, big=True)

    png = LETTER_DIR / f"{letter}-{_stamp(letter)}.png"
    cv2.imwrite(str(png), frame)
    render.encode_png(png, LETTER_SECONDS, out)
    return out


def _gap_clip(paper: bool) -> Path:
    """Blank frame shown between identical letters, in the same colour as the letter cards."""
    out = LETTER_DIR / f"_gap_{'paper' if paper else 'navy'}.mp4"
    if not out.exists():
        png = LETTER_DIR / "_gap.png"
        cv2.imwrite(str(png), np.full((HEIGHT, WIDTH, 3), _PAPER if paper else _BG, dtype=np.uint8))
        render.encode_png(png, LETTER_GAP_SECONDS, out)
    return out


def spell_word(word: str) -> tuple[Path, list[dict]]:
    """Build (or fetch from cache) the fingerspelled clip for a word.

    Returns the clip path and per-letter offsets (seconds from the start of the clip).
    """
    letters = [c for c in word.lower() if c in ALPHABET]
    parts: list[tuple[str | None, Path]] = []
    for i, ch in enumerate(letters):
        if i and letters[i - 1] == ch:
            parts.append((None, _gap_clip(paper=find_asset(ch) is not None)))  # visible pause so double letters read as two
        parts.append((ch, letter_clip(ch)))

    offsets, t = [], 0.0
    for ch, path in parts:
        dur = render.clip_duration(str(path))
        if ch:
            offsets.append({"letter": ch.upper(), "start": round(t, 3), "end": round(t + dur, 3)})
        t += dur

    key = hashlib.sha1("|".join(p.name for _, p in parts).encode()).hexdigest()[:16]
    out = SPELL_DIR / f"{word.lower()}-{key}.mp4"
    if not out.exists():
        render.concat_clips([p for _, p in parts], out)
    return out, offsets
