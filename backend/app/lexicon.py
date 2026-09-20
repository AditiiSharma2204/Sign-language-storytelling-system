"""Linguistic resources: words dropped in ASL gloss, synonym map, irregular forms."""

# Words with no direct ASL counterpart. ASL has no articles or copula, and it
# expresses prepositions spatially, so these are removed from the gloss.
ARTICLES = {"a", "an", "the"}
COPULA = {"is", "am", "are", "was", "were", "be", "been", "being"}
AUXILIARIES = {"do", "does", "did", "will", "would", "shall", "should", "has", "have", "had"}
PREPOSITIONS = {"to", "of", "at", "in", "on", "for", "from", "by", "into", "onto"}

DROP_REASONS = {
    **{w: "article - ASL has no articles" for w in ARTICLES},
    **{w: "copula - ASL omits 'to be'" for w in COPULA},
    **{w: "auxiliary - tense is shown by time signs" for w in AUXILIARIES},
    **{w: "preposition - expressed spatially in ASL" for w in PREPOSITIONS},
}

# ASL places time signs first (topic-comment structure).
TIME_WORDS = {"today", "tomorrow", "yesterday", "morning", "afternoon", "night"}

WH_WORDS = {"who", "what", "where", "when", "why", "how", "which"}

# Words that have a real ASL sign (or are pointing/grammar signs) but no clip in our vocabulary.
# Spelling them letter by letter would be wrong ASL, so they get a text card instead.
NO_SPELL = WH_WORDS | {
    "not", "he", "she", "it", "with", "this", "that", "these", "those", "there", "here",
    "very", "so", "if", "because", "or", "as", "than", "no", "yes", "can", "could", "may",
    "must", "just", "too", "all", "some", "any", "more", "much", "many",
}

# Contractions -> expansion (applied before tokenising).
CONTRACTIONS = {
    "won't": "will not",
    "can't": "can not",
    "cannot": "can not",
    "i'm": "i am",
}
CONTRACTION_SUFFIXES = [
    ("n't", " not"),
    ("'re", " are"),
    ("'ll", " will"),
    ("'ve", " have"),
    ("'d", " would"),
    ("'m", " am"),
    ("'s", ""),  # possessive / "is" - both are dropped in gloss
]

# Word -> vocabulary word. These are near-synonyms or inflections that the
# rule-based lemmatizer cannot derive (pronoun cases, family terms, ...).
SYNONYMS = {
    # pronouns
    "me": "i", "myself": "i",
    "my": "mine", "ours": "our", "us": "we", "ourselves": "we",
    "yours": "your", "yourself": "you", "them": "they", "their": "they", "theirs": "they",
    # family
    "mom": "mother", "mum": "mother", "mommy": "mother", "mama": "mother", "mother": "mother",
    "dad": "father", "daddy": "father", "papa": "father",
    "kid": "children", "kids": "children", "child": "children",
    "sibling": "brother", "siblings": "brother",
    "lady": "woman", "gentleman": "man", "guy": "man",
    # animals / places
    "puppy": "dog", "pup": "dog", "kitten": "cat", "kitty": "cat",
    "sea": "beach", "ocean": "beach", "shore": "beach", "seaside": "beach",
    "garden": "park", "playground": "park",
    # verbs
    "stroll": "walk", "hike": "walk", "jog": "run", "sprint": "run", "dash": "run",
    "nap": "sleep", "slumber": "sleep",
    "beverage": "drink", "sip": "drink",
    "enjoy": "like", "wish": "want", "desire": "want",
    "novel": "book",
    # connectors
    "also": "and", "plus": "and",
    "after": "then", "afterwards": "then", "next": "then",
    "however": "but", "yet": "but", "though": "but",
    # time
    "tonight": "night", "midnight": "night",
    "noon": "afternoon", "midday": "afternoon",
}

# Irregular inflections -> (lemma, tense).
IRREGULAR = {
    "went": ("go", "past"), "gone": ("go", "past"), "goes": ("go", "present"),
    "ate": ("eat", "past"), "eaten": ("eat", "past"),
    "slept": ("sleep", "past"),
    "ran": ("run", "past"),
    "drank": ("drink", "past"), "drunk": ("drink", "past"),
    "men": ("man", None), "women": ("woman", None),
    "children": ("children", None),
    "flew": ("fly", "past"),
    "forgot": ("forget", "past"), "forgotten": ("forget", "past"),
    "gave": ("give", "past"), "given": ("give", "past"),
    "told": ("tell", "past"), "met": ("meet", "past"),
}

PAST_MARKERS = {"was", "were", "did", "had"}
FUTURE_MARKERS = {"will", "shall", "gonna"}
