import time
from text_to_sign import text_to_asl_videos

def sentence_metrics(sentence, expected_words):
    start = time.time()

    result = text_to_asl_videos(sentence)
    tokens = result["tokens"]
    matched = result["matched_tokens"]

    expected = set(expected_words)
    matched_set = set(matched)

    # Recall: how many expected story words were covered
    tp = len(expected & matched_set)
    recall = tp / len(expected) if expected else 0

    # Sentence Accuracy: how much of the sentence is usable
    accuracy = tp / len(tokens) if tokens else 0

    # Vocabulary Coverage: same as usability ratio
    coverage = len(matched) / len(tokens) if tokens else 0

    exec_time = time.time() - start

    return {
        "recall": round(recall, 3),
        "accuracy": round(accuracy, 3),
        "coverage": round(coverage, 3),
        "time": round(exec_time, 5)
    }
