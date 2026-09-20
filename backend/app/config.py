"""Paths and limits shared across the backend."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

SIGNS_DIR = ROOT / "asl_videos_std"
# Signs added automatically from WLASL by tools/build_signs.py (the hand-curated set above wins on conflicts)
AUTO_SIGNS_DIR = ROOT / "asl_videos_wlasl"
# Drop-in alphabet assets: a.png ... z.png (or .jpg/.webp/.mp4). Missing letters render as letter cards.
FINGERSPELL_DIR = ROOT / "fingerspelling"
VOCAB_FILE = ROOT / "vocab.txt"                 # hand-curated words
EXTRA_VOCAB_FILE = ROOT / "vocab_wlasl.txt"      # words built by tools/build_signs.py
OUTPUT_DIR = ROOT / "backend" / "outputs"
FRONTEND_DIST = ROOT / "frontend" / "dist"

# Output video format (matches the standardised WLASL clips)
WIDTH, HEIGHT, FPS = 640, 480, 30

# Duration (seconds) of the text card shown for words that have no sign clip
CARD_SECONDS = 1.2

# Fingerspelling
LETTER_SECONDS = 0.7      # how long each letter is held when the asset is a still image
LETTER_GAP_SECONDS = 0.12  # short pause between identical consecutive letters (z-z)
MAX_SPELL_LENGTH = 14      # longer words fall back to a text card

MAX_INPUT_CHARS = 1200
MAX_SIGNS = 80

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
