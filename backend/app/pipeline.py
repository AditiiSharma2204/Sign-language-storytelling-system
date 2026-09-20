"""End-to-end translation: text -> gloss -> clips -> video + metrics."""
import re
import time
from pathlib import Path

from . import fingerspell, render
from .config import AUTO_SIGNS_DIR, EXTRA_VOCAB_FILE, MAX_INPUT_CHARS, MAX_SIGNS, OUTPUT_DIR, SIGNS_DIR, VOCAB_FILE
from .gloss import SentenceGloss, gloss_text, tokenize


def _read_words(path: Path) -> set[str]:
    return {w.strip().lower() for w in path.read_text().splitlines() if w.strip()} if path.exists() else set()


# Word lists are committed with the code; the video clips they refer to are not (WLASL licence).
CURATED_WORDS = _read_words(VOCAB_FILE)
ALL_WORDS = CURATED_WORDS | _read_words(EXTRA_VOCAB_FILE)


def load_sign_files() -> dict[str, Path]:
    """word -> clip. Auto-built WLASL signs first, then the hand-curated set (curated wins)."""
    files = {p.stem: p for p in AUTO_SIGNS_DIR.glob("*.mp4")} if AUTO_SIGNS_DIR.exists() else {}
    files.update({w: SIGNS_DIR / f"{w}.mp4" for w in CURATED_WORDS if (SIGNS_DIR / f"{w}.mp4").exists()})
    return files


SIGN_FILES = load_sign_files()
VOCAB = set(SIGN_FILES)


def sign_source(word: str) -> str:
    return "curated" if SIGN_FILES[word].parent == SIGNS_DIR else "wlasl"


def original_metric(text: str) -> float:
    """The original project's metric: exact matches / all raw words (function words count as misses)."""
    tokens = re.sub(r"[^a-z\s]", "", text.lower()).split()
    return sum(t in VOCAB for t in tokens) / len(tokens) if tokens else 0.0


def analyse(text: str, vocab: set[str] | None = None) -> list[SentenceGloss]:
    return gloss_text(text, VOCAB if vocab is None else vocab)


def metrics_for(sentences: list[SentenceGloss]) -> dict:
    tokens = [t for s in sentences for t in s.tokens]
    content = [t for t in tokens if t.status != "dropped"]
    signed = [t for t in content if t.status in ("exact", "lemma", "synonym")]
    spelled = [t for t in content if t.status == "spell"]
    used = {t.gloss for t in signed}
    coverage = len(signed) / len(content) if content else 0.0
    conveyed = (len(signed) + len(spelled)) / len(content) if content else 0.0
    # Like-for-like baseline: same denominator (words that need a sign), exact matches only.
    baseline = sum(t.status == "exact" for t in content) / len(content) if content else 0.0
    return {
        "words_in": len(tokens),
        "grammar_dropped": len(tokens) - len(content),
        "signed": len(signed),
        "spelled": len(spelled),
        "text_cards": len(content) - len(signed) - len(spelled),
        "sign_coverage": round(coverage, 3),
        "conveyed_coverage": round(conveyed, 3),
        "baseline_coverage": round(baseline, 3),
        "improvement": round(coverage - baseline, 3),
        "unique_signs": len(used),
        "vocab_utilization": round(len(used) / len(VOCAB), 3) if VOCAB else 0.0,
        "reordered_sentences": sum(s.reordered for s in sentences),
    }


def translate(text: str) -> dict:
    text = text.strip()
    if not text:
        raise ValueError("Please enter some text.")
    if len(text) > MAX_INPUT_CHARS:
        raise ValueError(f"Text is too long (max {MAX_INPUT_CHARS} characters).")

    started = time.perf_counter()
    sentences = analyse(text)

    # Build the clip list ------------------------------------------------
    segments: list[dict] = []
    clips: list[Path] = []
    for si, sent in enumerate(sentences):
        for tok in sent.gloss:
            if len(clips) >= MAX_SIGNS:
                break
            letters = None
            if tok.status == "spell":
                clip, letters = fingerspell.spell_word(tok.gloss)
                kind, label = "spell", "-".join(tok.gloss.upper())
            elif tok.status == "card":
                clip, kind, label = render.normalize(render.make_text_card(tok.gloss)), "card", tok.gloss.upper()
            else:
                clip, kind, label = render.normalize(SIGN_FILES[tok.gloss]), "sign", tok.gloss.upper()
            clips.append(clip)
            segments.append({
                "label": label, "word": tok.gloss, "kind": kind, "letters": letters,
                "surface": tok.surface, "status": tok.status, "sentence": si,
            })

    result = {
        "input": text,
        "sentences": [{
            "text": s.text,
            "tense": s.tense,
            "is_question": s.is_question,
            "reordered": s.reordered,
            "tokens": [{"surface": t.surface, "status": t.status,
                        "gloss": t.gloss, "reason": t.reason} for t in s.tokens],
            "gloss": [("#" + "-".join(t.gloss.upper()) if t.status == "spell" else t.gloss.upper())
                      for t in s.gloss],
        } for s in sentences],
        "timeline": [],
        "video_url": None,
        "vtt_url": None,
        "srt_url": None,
        "duration": 0.0,
        "metrics": metrics_for(sentences),
    }
    if not clips:
        result["metrics"]["latency_ms"] = round((time.perf_counter() - started) * 1000)
        return result

    # Timeline (word-level sync data for the UI) ---------------------------
    t = 0.0
    for seg, clip in zip(segments, clips):
        dur = render.clip_duration(str(clip))
        seg["start"], seg["end"] = round(t, 3), round(t + dur, 3)
        for L in seg["letters"] or []:  # make letter times absolute for the UI
            L["start"], L["end"] = round(L["start"] + t, 3), round(L["end"] + t, 3)
        t += dur
    result["timeline"], result["duration"] = segments, round(t, 3)

    # Render (cached by clip sequence) -----------------------------------
    key = render.cache_key(clips)
    video, vtt, srt = (OUTPUT_DIR / f"{key}.{ext}" for ext in ("mp4", "vtt", "srt"))
    cached = video.exists()
    if not cached:
        render.concat_clips(clips, video)
    render.write_subtitles(segments, vtt, srt)

    result.update(video_url=f"/media/out/{video.name}", vtt_url=f"/media/out/{vtt.name}",
                  srt_url=f"/media/out/{srt.name}")
    result["metrics"]["cached"] = cached
    result["metrics"]["latency_ms"] = round((time.perf_counter() - started) * 1000)
    return result
