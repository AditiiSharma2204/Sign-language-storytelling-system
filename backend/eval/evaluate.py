"""Evaluate SignStory on two sentence sets and two vocabularies.

Run from the backend folder:  python -m eval.evaluate

Sign coverage = words that receive a sign / words that need one (articles, "to be", auxiliaries and
prepositions are excluded, as ASL does not sign them). "Conveyed" also counts fingerspelled words.

Sets
  curated : 20 sentences written around the original 46-word vocabulary (favours the old system)
  general : 20 everyday sentences written without reference to either vocabulary
Vocabularies
  46  : hand-curated signs only        127 : curated + 81 signs built from WLASL by tools/build_signs.py
Baseline for "like-for-like": exact vocabulary matches only, same denominator.
"""
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.gloss import gloss_text  # noqa: E402
from app.pipeline import ALL_WORDS, CURATED_WORDS, metrics_for  # noqa: E402

CURATED_SET = [
    "The cat wants to play.", "The dog drinks water in the park.",
    "My brother and sister are running to school.", "Yesterday the kids played at the beach.",
    "I will go to school tomorrow.", "My mom and dad ate breakfast in the morning.",
    "The children were reading books at night.", "We don't like the green bird.",
    "Where do you walk in the afternoon?", "The woman is sleeping and the man is walking.",
    "They played in the park but I stayed at home.", "My family goes to the beach on Sunday.",
    "The puppy drinks water and sleeps.", "Today I want to read a blue book.",
    "Our father runs in the morning and then eats.", "The boy likes cats but not dogs.",
    "She walked to the library with her friend.", "The kids ran to the playground yesterday.",
    "You and I like to play with our dog.", "Tomorrow afternoon we will walk to the park.",
]

GENERAL_SET = [
    "My son needs help with his homework.", "The doctor told my wife to rest at home.",
    "We eat pizza and apples for dinner.", "My cousin works at a big company in the city.",
    "Yesterday I forgot my backpack at school.", "The teacher will help the children study.",
    "She wears a black hat and a white shirt.", "Do you want water or milk?",
    "My brother loves basketball but I like dance.", "Where is the door?",
    "I need a new computer for work.", "The dog sleeps on the bed all night.",
    "On Thursday we visit my mother.", "He gave me a yellow jacket for my birthday.",
    "Who cooks dinner tonight?", "My sister is deaf and she teaches language classes.",
    "What time does the meeting start?", "Please wait here, the doctor will meet you soon.",
    "The children finished their paint and cleaned the table.", "I decided to change my brown shoes.",
]


def run(sentences, vocab):
    rows = []
    for s in sentences:
        m = metrics_for(gloss_text(s, vocab))
        rows.append(dict(baseline=m["baseline_coverage"], signs=m["sign_coverage"],
                         conveyed=m["conveyed_coverage"], cards=m["text_cards"], original=original_metric_for(s, vocab)))
    return rows


def original_metric_for(sentence, vocab):
    tokens = "".join(c if c.isalpha() or c.isspace() else "" for c in sentence.lower()).split()
    return sum(t in vocab for t in tokens) / len(tokens) if tokens else 0.0


def summarise(rows):
    mean = lambda k: statistics.mean(r[k] for r in rows)  # noqa: E731
    return dict(original=mean("original"), baseline=mean("baseline"), signs=mean("signs"),
                conveyed=mean("conveyed"), full=sum(r["conveyed"] == 1 for r in rows), n=len(rows))


def main():
    curated_vocab, VOCAB = CURATED_WORDS, ALL_WORDS
    print(f"vocabularies: curated {len(curated_vocab)} signs, full {len(VOCAB)} signs\n")
    print(f"{'set':8} {'vocab':>5}  {'orig.metric':>11} {'exact-only':>10} {'signs':>7} {'+spelling':>9}  fully conveyed")
    for name, sentences in (("curated", CURATED_SET), ("general", GENERAL_SET)):
        for label, vocab in ((len(curated_vocab), curated_vocab), (len(VOCAB), VOCAB)):
            s = summarise(run(sentences, vocab))
            print(f"{name:8} {label:>5}  {s['original']:>11.1%} {s['baseline']:>10.1%} {s['signs']:>7.1%} "
                  f"{s['conveyed']:>9.1%}  {s['full']}/{s['n']}")
        print()

    print("Unknown words in the general set with the full vocabulary (these get fingerspelled):")
    unknown = []
    for s in GENERAL_SET:
        for sent in gloss_text(s, VOCAB):
            unknown += [t.gloss for t in sent.gloss if t.status in ("spell", "card")]
    print(" ", ", ".join(sorted(set(unknown))))


if __name__ == "__main__":
    main()
