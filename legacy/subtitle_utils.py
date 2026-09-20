import subprocess

def get_video_duration(video_path):
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())


def format_time(seconds):
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = seconds % 60

    return f"{hrs:02}:{mins:02}:{secs:06.3f}".replace(".", ",")


def create_subtitles(video_paths, tokens, output_file="subtitles.srt"):

    current_time = 0
    lines = []

    for i, (video, word) in enumerate(zip(video_paths, tokens), start=1):

        duration = get_video_duration(video)

        start_time = format_time(current_time)
        end_time = format_time(current_time + duration)

        lines.append(str(i))
        lines.append(f"{start_time} --> {end_time}")
        lines.append(word.capitalize())
        lines.append("")

        current_time += duration

    with open(output_file, "w") as f:
        f.write("\n".join(lines))