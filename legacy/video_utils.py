import subprocess
import tempfile
from pathlib import Path

def concatenate_videos(video_paths, output_path):
    """
    Concatenate multiple ASL videos into a single video using FFmpeg
    """
    if not video_paths:
        raise ValueError("No videos provided for concatenation")

    output_path = Path(output_path)
    output_path.parent.mkdir(exist_ok=True)

    # Create temporary concat file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for vp in video_paths:
            f.write(f"file '{vp.resolve()}'\n")
        concat_file = f.name

    # FFmpeg concat command
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_file,
        "-c", "copy",
        str(output_path)
    ]

    subprocess.run(cmd, check=True)
import subprocess

def add_subtitles(video_file, subtitle_file, output_file):

    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(video_file),
        "-vf", f"subtitles={subtitle_file}",
        str(output_file)
    ]

    subprocess.run(cmd)