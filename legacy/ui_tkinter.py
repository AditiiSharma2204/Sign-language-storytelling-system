import tkinter as tk
from tkinter import messagebox
import time
from pathlib import Path
import subprocess

from text_to_sign import text_to_asl_videos
from video_utils import concatenate_videos, add_subtitles
from subtitle_utils import create_subtitles


def generate_story():

    text = text_entry.get("1.0", tk.END).strip()

    if not text:
        messagebox.showwarning("Input Error", "Please enter a story.")
        return

    # START TIMER
    start_time = time.time()

    # Process text
    result = text_to_asl_videos(text)

    tokens = result["tokens"]
    matched_tokens = result["matched_tokens"]
    videos = result["video_paths"]

    # Vocabulary size
    VOCAB_SIZE = 46

    # Sentence Accuracy
    sentence_accuracy = (
        len(matched_tokens) / len(tokens)
        if tokens else 0.0
    )

    # Vocabulary Utilization
    vocabulary_utilization = (
        len(matched_tokens) / VOCAB_SIZE
    )

    # Output paths
    output_video = Path("output/story_generated.mp4")
    captioned_video = Path("output/story_with_captions.mp4")

    # Generate video
    concatenate_videos(videos, output_video)

    # Generate subtitle file
    create_subtitles(videos, matched_tokens)

    # Add subtitles to video
    add_subtitles(
        "output/story_generated.mp4",
        "subtitles.srt",
        "output/story_with_captions.mp4"
    )

    # END TIMER
    execution_time = time.time() - start_time

    # Update UI labels
    accuracy_label.config(
        text=f"Sentence Accuracy: {round(sentence_accuracy, 3)}"
    )

    coverage_label.config(
        text=f"Vocabulary Utilization: {round(vocabulary_utilization, 3)}"
    )

    time_label.config(
        text=f"Execution Time: {round(execution_time, 4)} sec"
    )

    # Success popup
    messagebox.showinfo(
        "Success",
        "Story video with subtitles generated!"
    )

    # Open final captioned video
    subprocess.run(["start", captioned_video], shell=True)


# ================= GUI =================

root = tk.Tk()
root.title("Sign Language Storytelling System")
root.geometry("650x500")

title = tk.Label(
    root,
    text="Sign Language Storytelling System",
    font=("Arial", 18, "bold")
)
title.pack(pady=10)

text_label = tk.Label(
    root,
    text="Enter your story:",
    font=("Arial", 11)
)
text_label.pack()

text_entry = tk.Text(
    root,
    height=7,
    width=70,
    font=("Arial", 11)
)
text_entry.pack(pady=5)

generate_button = tk.Button(
    root,
    text="Generate Story",
    command=generate_story,
    font=("Arial", 11),
    padx=10,
    pady=5
)
generate_button.pack(pady=10)

metrics_frame = tk.Frame(root)
metrics_frame.pack(pady=10)

accuracy_label = tk.Label(
    metrics_frame,
    text="Sentence Accuracy:",
    font=("Arial", 11)
)
accuracy_label.pack()

coverage_label = tk.Label(
    metrics_frame,
    text="Vocabulary Utilization:",
    font=("Arial", 11)
)
coverage_label.pack()

time_label = tk.Label(
    metrics_frame,
    text="Execution Time:",
    font=("Arial", 11)
)
time_label.pack()

root.mainloop()