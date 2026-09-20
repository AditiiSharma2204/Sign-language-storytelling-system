"""Vocabulary-aware rule-based lemmatizer.

Instead of a general-purpose lemmatizer we only accept a candidate base form if
it exists in the sign vocabulary, which avoids false stems such as
"news" -> "new".
"""
from .lexicon import IRREGULAR

_VOWELS = "aeiou"


def _candidates(word: str):
    """Yield (candidate_lemma, tense_hint) in order of preference."""
    if word.endswith("ies") and len(word) > 4:
        yield word[:-3] + "y", None
    if word.endswith("es") and len(word) > 3:
        yield word[:-2], None
    if word.endswith("s") and not word.endswith("ss") and len(word) > 2:
        yield word[:-1], None

    if word.endswith("ing") and len(word) > 4:
        base = word[:-3]
        yield base, "progressive"
        yield base + "e", "progressive"
        if len(base) > 2 and base[-1] == base[-2] and base[-1] not in _VOWELS:
            yield base[:-1], "progressive"

    if word.endswith("ied") and len(word) > 4:
        yield word[:-3] + "y", "past"
    if word.endswith("ed") and len(word) > 3:
        base = word[:-2]
        yield base, "past"
        yield word[:-1], "past"  # liked -> like
        if len(base) > 2 and base[-1] == base[-2] and base[-1] not in _VOWELS:
            yield base[:-1], "past"  # stopped -> stop


def lemmatize(word: str, vocab: set[str]):
    """Return (lemma, tense_hint) or (None, None) if no vocabulary form exists."""
    if word in IRREGULAR:
        lemma, tense = IRREGULAR[word]
        if lemma in vocab:
            return lemma, tense
    for cand, tense in _candidates(word):
        if cand in vocab and cand != word:
            return cand, tense
    return None, None
