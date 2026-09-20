"""English -> ASL gloss conversion.

Turns a sentence into a sequence of gloss tokens, applying a handful of real
ASL grammar rules: dropping articles/copula/prepositions, fronting time signs,
moving wh-words to the end, and keeping negation. Every decision is recorded so
the UI can explain what happened to each word.
"""
import re
from dataclasses import dataclass, field

from .config import MAX_SPELL_LENGTH
from .lemmatizer import lemmatize
from .lexicon import (
    CONTRACTION_SUFFIXES, CONTRACTIONS, DROP_REASONS, FUTURE_MARKERS, NO_SPELL,
    PAST_MARKERS, SYNONYMS, TIME_WORDS, WH_WORDS,
)


@dataclass
class TokenInfo:
    surface: str
    status: str            # exact | lemma | synonym | spell | card | dropped
    gloss: str | None = None   # gloss word actually signed (or shown as card)
    reason: str = ""


@dataclass
class SentenceGloss:
    text: str
    tokens: list[TokenInfo] = field(default_factory=list)
    gloss: list[TokenInfo] = field(default_factory=list)   # in ASL order
    tense: str = "present"
    is_question: bool = False
    reordered: bool = False


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    return [p.strip() for p in parts if p and p.strip()]


def _expand_contractions(sentence: str) -> str:
    s = sentence.lower().replace("’", "'")
    for k, v in CONTRACTIONS.items():
        s = re.sub(rf"\b{re.escape(k)}\b", v, s)
    for suffix, repl in CONTRACTION_SUFFIXES:
        s = re.sub(rf"(?<=[a-z]){re.escape(suffix)}\b", repl, s)
    return s


def tokenize(sentence: str) -> list[str]:
    s = _expand_contractions(sentence)
    return re.findall(r"[a-z]+", s)


# Capitalised words that are not people's names and keep their normal sign (days, months, holidays, places).
_PROPER_WITH_SIGN = {
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "january", "february", "march", "april", "may", "june", "july", "august",
    "september", "october", "november", "december", "thanksgiving", "christmas", "africa",
}
_WORD = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)?")


def tokenize_marked(sentence: str) -> list[tuple[str, bool]]:
    """Tokenise and flag words that look like names: capitalised in the middle of a sentence.

    Sentence-initial capitals are ambiguous (every sentence starts with one), so the first word is
    never flagged. Title Case or SHOUTED text is left alone because capitals then carry no meaning.
    """
    raw = _WORD.findall(sentence)
    capitalised = [i for i, w in enumerate(raw)
                   if i > 0 and w[0].isupper() and w[1:].islower() and w not in ("I",) and not w.startswith(("I'", "I’"))]
    later = [w for w in raw[1:] if len(w) >= 3]  # the first word is always capitalised, so skip it
    title_case = len(later) >= 3 and sum(w[0].isupper() for w in later) / len(later) > 0.7

    out: list[tuple[str, bool]] = []
    for i, w in enumerate(raw):
        is_name = i in capitalised and not title_case and w.split("'")[0].split("’")[0].lower() not in _PROPER_WITH_SIGN
        for tok in re.findall(r"[a-z]+", _expand_contractions(w)):
            out.append((tok, is_name and tok == re.findall(r"[a-z]+", w.lower())[0]))
    return out


_IRREGULAR_PARTICIPLES = {"been", "gone", "done", "seen", "eaten", "drunk", "run", "slept", "made",
                          "taken", "given", "known", "got", "gotten", "ate", "went", "came"}


def _is_participle(word: str | None) -> bool:
    return bool(word) and (word.endswith(("ed", "en")) or word in _IRREGULAR_PARTICIPLES)


def _resolve(word: str, vocab: set[str], next_word: str | None = None, is_name: bool = False) -> TokenInfo:
    if is_name:
        if len(word) > MAX_SPELL_LENGTH:
            return TokenInfo(word, "card", word, "name too long to fingerspell - shown as text card")
        return TokenInfo(word, "spell", word, "looks like a name (capitalised mid-sentence) - fingerspelled")
    # "have" is an auxiliary before a participle ("have eaten") but a real sign as a main verb.
    if word in ("have", "has", "had") and "have" in vocab and not _is_participle(next_word) and next_word != "to":
        return TokenInfo(word, "exact" if word == "have" else "lemma", "have", "main verb 'have'")
    if word in DROP_REASONS:
        return TokenInfo(word, "dropped", None, DROP_REASONS[word])
    if word in vocab:
        return TokenInfo(word, "exact", word, "direct vocabulary match")
    if word in SYNONYMS and SYNONYMS[word] in vocab:
        return TokenInfo(word, "synonym", SYNONYMS[word], f"synonym of '{SYNONYMS[word]}'")
    lemma, _ = lemmatize(word, vocab)
    if lemma:
        return TokenInfo(word, "lemma", lemma, f"inflection of '{lemma}'")
    if word in NO_SPELL or len(word) > MAX_SPELL_LENGTH:
        why = "has its own ASL sign, but no clip yet" if word in NO_SPELL else "too long to fingerspell"
        return TokenInfo(word, "card", word, f"{why} - shown as text card")
    return TokenInfo(word, "spell", word, "not in sign vocabulary - fingerspelled")


def _detect_tense(words: list[str], vocab: set[str]) -> str:
    if any(w in FUTURE_MARKERS for w in words) or "tomorrow" in words:
        return "future"
    if any(w in PAST_MARKERS for w in words) or "yesterday" in words:
        return "past"
    for w in words:
        _, tense = lemmatize(w, vocab)
        if tense == "past":
            return "past"
    return "present"


def gloss_sentence(text: str, vocab: set[str]) -> SentenceGloss:
    marked = tokenize_marked(text)
    words = [w for w, _ in marked]
    result = SentenceGloss(text=text)
    result.is_question = text.rstrip().endswith("?") or bool(words and words[0] in WH_WORDS)
    result.tense = _detect_tense([w for w, n in marked if not n], vocab)

    result.tokens = [_resolve(w, vocab, words[i + 1] if i + 1 < len(words) else None, is_name)
                     for i, (w, is_name) in enumerate(marked)]
    kept = [t for t in result.tokens if t.status != "dropped"]

    # ASL word-order rules -------------------------------------------------
    signed = [t for t in kept if t.status != "spell"]  # names/spelled words never get reordered
    time_first = [t for t in signed if t.gloss in TIME_WORDS]
    wh_last = [t for t in signed if t.surface in WH_WORDS and t.gloss not in TIME_WORDS]
    rest = [t for t in kept if t not in time_first and t not in wh_last]
    ordered = time_first + rest + wh_last
    result.reordered = [id(t) for t in ordered] != [id(t) for t in kept]
    result.gloss = ordered
    return result


def gloss_text(text: str, vocab: set[str]) -> list[SentenceGloss]:
    return [gloss_sentence(s, vocab) for s in split_sentences(text)]
