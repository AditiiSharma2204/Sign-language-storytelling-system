# text_to_sign.py
import re
from pathlib import Path

ASL_DIR = Path("asl_videos_std")
VOCAB_FILE = Path("vocab.txt")

with open(VOCAB_FILE, "r") as f:
    VOCAB = set(word.strip().lower() for word in f.readlines())


def preprocess_text(text: str):
    text = text.lower()
    text = re.sub(r"[^a-z\s]", "", text)
    return text.split()


def text_to_asl_videos(text: str):
    tokens = preprocess_text(text)

    matched = []
    video_paths = []

    for token in tokens:
        video_file = ASL_DIR / f"{token}.mp4"
        if token in VOCAB and video_file.exists():
            matched.append(token)
            video_paths.append(video_file)

    return {
        "tokens": tokens,
        "matched_tokens": matched,
        "video_paths": video_paths,
        "vocab": VOCAB
    }
