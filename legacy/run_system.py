import time
from pathlib import Path
from subtitle_utils import create_subtitles
from video_utils import add_subtitles
from text_to_sign import text_to_asl_videos
from video_utils import concatenate_videos

print("=== Sign-Based Storytelling System ===")
text = input("Enter a sentence: ")

# 🔹 Start timing
start_time = time.time()

result = text_to_asl_videos(text)

tokens = result["tokens"]
matched_tokens = result["matched_tokens"]
videos = result["video_paths"]

# 🔹 End timing


# 🔹 Sentence-level metrics
VOCAB_SIZE = 46

sentence_accuracy = (
    len(matched_tokens) / len(tokens)
    if tokens else 0.0
)

vocabulary_utilization = (
    len(matched_tokens) / VOCAB_SIZE
)

# 🔹 Generate story video
output = Path("output/story_generated.mp4")
concatenate_videos(videos, output)

print("\n===== GENERATED OUTPUT =====")
print("Story video:", output)
# Generate subtitles
create_subtitles(videos, matched_tokens)

# Add subtitles to final video
add_subtitles(
    "output/story_generated.mp4",
    "subtitles.srt",
    "output/story_with_captions.mp4"
)
execution_time = time.time() - start_time
print("Captioned Video:", "output/story_with_captions.mp4")
print("\n===== SYSTEM METRICS =====")
print("Sentence Accuracy      :", round(sentence_accuracy, 3))
print("Vocabulary Coverage    :", round(vocabulary_utilization, 3))
print("Execution Time (sec)   :", round(execution_time, 6))
print("Story Generation Success:", "Yes" if matched_tokens else "No")
