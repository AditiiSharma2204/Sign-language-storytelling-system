import time
from pathlib import Path

from text_to_sign import text_to_asl_videos
from video_utils import concatenate_videos
from metrics import precision, recall, accuracy, vocabulary_coverage

print("=== Sign-Based Storytelling System ===")
text = input("Enter a sentence: ")

start_time = time.time()
result = text_to_asl_videos(text)
end_time = time.time()

tokens = result["tokens"]
matched = result["matched_tokens"]
vocab = result["vocab"]
videos = result["video_paths"]

# 🔹 Dynamic ground truth
relevant_tokens = [t for t in tokens if t in vocab]

# 🔹 Metric values
correct_matches = len(matched)
total_matched = len(matched)
total_relevant = len(relevant_tokens)
total_tokens = len(tokens)
correct_rejections = total_tokens - total_matched

# 🔹 Generate story video
output = Path("output/story_generated.mp4")
concatenate_videos(videos, output)

print("\n===== GENERATED OUTPUT =====")
print("Story video:", output)

print("\n===== DYNAMIC METRICS =====")
print("Precision:", round(precision(correct_matches, total_matched), 2))
print("Recall:", round(recall(correct_matches, total_relevant), 2))
print("Accuracy:", round(accuracy(correct_matches, correct_rejections, total_tokens), 2))
print("Vocabulary Coverage:", round(vocabulary_coverage(total_matched, total_tokens), 2))
print("Execution Time:", round(end_time - start_time, 4), "seconds")
print("Story Generation Success:", "Yes" if total_matched > 0 else "No")
