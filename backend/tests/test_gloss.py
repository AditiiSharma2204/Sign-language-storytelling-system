import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.gloss import gloss_sentence  # noqa: E402
from app.lemmatizer import lemmatize  # noqa: E402
import pytest  # noqa: E402

from app.pipeline import ALL_WORDS as VOCAB, SIGN_FILES, analyse, metrics_for  # noqa: E402

needs_clips = pytest.mark.skipif(not SIGN_FILES, reason="sign clips are not installed (see README)")


def gloss(text):
    return [t.gloss for t in gloss_sentence(text, VOCAB).gloss]


def test_vocab_loaded():
    assert len(VOCAB) >= 120 and {"school", "pizza", "help"} <= VOCAB


def test_lemmatizer_inflections():
    assert lemmatize("playing", VOCAB)[0] == "play"
    assert lemmatize("running", VOCAB)[0] == "run"
    assert lemmatize("liked", VOCAB)[0] == "like"
    assert lemmatize("families", VOCAB)[0] == "family"
    assert lemmatize("beaches", VOCAB)[0] == "beach"
    assert lemmatize("went", VOCAB)[0] == "go"


def test_lemmatizer_does_not_invent_words():
    assert lemmatize("news", VOCAB)[0] is None


def test_articles_copula_prepositions_dropped():
    assert gloss("The cat is at the park") == ["cat", "park"]


def test_time_words_move_first():
    assert gloss("I go to school tomorrow") == ["tomorrow", "i", "go", "school"]


def test_synonyms_and_plurals():
    assert gloss("The kids played with the puppy") == ["children", "play", "with", "dog"]


def test_unknown_word_is_fingerspelled():
    tokens = gloss_sentence("I like zebra", VOCAB).gloss
    assert [(t.gloss, t.status) for t in tokens] == [("i", "exact"), ("like", "exact"), ("zebra", "spell")]


def test_words_with_their_own_sign_get_text_card_not_spelling():
    s = gloss_sentence("I do not like it", VOCAB)
    assert {t.gloss: t.status for t in s.gloss}["not"] == "card"
    assert {t.gloss: t.status for t in s.gloss}["it"] == "card"


def test_very_long_word_falls_back_to_card():
    s = gloss_sentence("antidisestablishmentarianism", VOCAB)
    assert s.gloss[0].status == "card"


def test_question_wh_word_moves_to_end():
    s = gloss_sentence("Where do you go?", VOCAB)
    assert s.is_question and [t.gloss for t in s.gloss] == ["you", "go", "where"]


def test_contractions_keep_negation():
    assert gloss("I don't like dogs") == ["i", "not", "like", "dog"]


def test_tense_detection():
    assert gloss_sentence("I ate yesterday", VOCAB).tense == "past"
    assert gloss_sentence("We will play tomorrow", VOCAB).tense == "future"


def test_coverage_beats_baseline():
    text = "The children played in the park yesterday and they were running."
    m = metrics_for(analyse(text, VOCAB))
    assert m["sign_coverage"] > m["baseline_coverage"]


def test_spell_word_letter_timings():
    from app.fingerspell import spell_word
    clip, letters = spell_word("zoo")
    assert clip.exists()
    assert [l["letter"] for l in letters] == ["Z", "O", "O"]
    # consecutive letters never overlap, and the repeated O is separated by a pause
    for a, b in zip(letters, letters[1:]):
        assert a["end"] <= b["start"]
    assert letters[2]["start"] > letters[1]["end"]


def test_spelling_counts_toward_conveyed_but_not_sign_coverage():
    text = "I like zebra"
    m = metrics_for(analyse(text, VOCAB))
    assert m["spelled"] == 1
    assert m["conveyed_coverage"] == 1.0 and m["sign_coverage"] < 1.0


def test_have_is_a_sign_as_main_verb_but_dropped_as_auxiliary():
    assert gloss("I have a dog") == ["i", "have", "dog"]
    assert gloss("I have eaten") == ["i", "eat"]


@needs_clips
def test_curated_clips_take_priority_over_auto_built_ones():
    from app.pipeline import sign_source
    assert sign_source("school") == "curated"   # exists in both sets
    assert sign_source("help") == "wlasl"
    assert all(p.exists() for p in SIGN_FILES.values())


def test_wh_words_are_now_real_signs_placed_last():
    s = gloss_sentence("What do you need?", VOCAB)
    assert [(t.gloss, t.status) for t in s.gloss] == [("you", "exact"), ("need", "exact"), ("what", "exact")]


def test_new_irregular_verbs_map_to_new_signs():
    assert gloss("I forgot") == ["i", "forget"]
    assert gloss("He gave me help") == ["he", "give", "i", "help"]
    assert gloss("They told us") == ["they", "tell", "we"]


def test_capitalised_mid_sentence_words_are_names_and_spelled():
    s = gloss_sentence("I met Rose at the park", VOCAB)
    assert [(t.gloss, t.status) for t in s.gloss] == [
        ("i", "exact"), ("meet", "lemma"), ("rose", "spell"), ("park", "exact")]
    assert "name" in [t for t in s.tokens if t.surface == "rose"][0].reason


def test_possessive_names_and_days_of_the_week():
    assert [t.gloss for t in gloss_sentence("We saw Maria's dog", VOCAB).gloss][-2:] == ["maria", "dog"]
    assert [(t.gloss, t.status) for t in gloss_sentence("We visit on Thursday", VOCAB).gloss][-1] == ("thursday", "exact")


def test_sentence_initial_capital_and_title_case_are_not_names():
    assert gloss("Park is nice")[0] == "park"                      # first word is ambiguous
    assert gloss("The Dog And The Cat Play")[:2] == ["dog", "and"]  # Title Case is not a list of names


def test_names_are_never_reordered_as_time_or_wh_words():
    s = gloss_sentence("I saw Morning yesterday", VOCAB)
    assert [t.gloss for t in s.gloss][0] == "yesterday"
    assert [t for t in s.gloss if t.gloss == "morning"][0].status == "spell"
