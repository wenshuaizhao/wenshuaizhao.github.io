"""Render the square LOOK thumbnail using FFmpeg and the sibling LOOK repository.

Usage: python3 scripts/render_look_thumbnail.py [path/to/look]
Source: origin/gh-pages, assets/teaser-source.md (including the crop coordinates).
"""

from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(sys.argv[1]).expanduser().resolve() if len(sys.argv) > 1 else ROOT.parent / "look"
OUTPUT = ROOT / "images" / "paper" / "look"


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, args)], check=True)


def render(work):
    for source, name in (
        ("assets/sheep.jpg", "sheep.jpg"),
        ("assets/fonts/source-sans-pro-semibold.ttf", "font.ttf"),
    ):
        (work / name).write_bytes(subprocess.check_output([
            "git", "-C", str(SOURCE), "show", "origin/gh-pages:" + source,
        ]))

    # The LOOK scene retains the full photo, revealing only the supervised crop.
    # The next scenes enlarge precisely that same crop, without stretching it.
    scenes = (
        (
            "LOOK", "Where am I looking?", "0x187f86",
            "[0:v]scale=432:324,split=2[full][crop];"
            "[full]drawbox=color=white@0.65:t=fill[dim];"
            "[crop]crop=151:151:0:108[visible];"
            "[dim][visible]overlay=0:108,"
            "drawbox=x=0:y=108:w=151:h=151:color=0x187f86:t=4,"
            "pad=480:480:24:82:color=0xf3f8f8",
        ),
        (
            "PERCEIVE", "A sheep", "0x456eac",
            "[0:v]crop=224:224:0:160,scale=360:360,"
            "pad=480:480:60:72:color=0xf3f6fa",
        ),
        (
            "UNDERSTAND", "Likely grazing", "0x8358aa",
            "[0:v]crop=224:224:0:160,scale=360:360,"
            "pad=480:480:60:72:color=0xf7f4fa",
        ),
    )
    for i, (title, caption, color, layout) in enumerate(scenes):
        labels = (
            f",drawtext=fontfile='{work / 'font.ttf'}':text='{title}':"
            f"fontsize=40:fontcolor={color}:x=(w-tw)/2:y=14"
            f",drawtext=fontfile='{work / 'font.ttf'}':text='{caption}':"
            f"fontsize=28:fontcolor={color}:x=(w-tw)/2:y=440"
            ",setsar=1"
        )
        ffmpeg("-i", work / "sheep.jpg", "-filter_complex", layout + labels,
               "-frames:v", "1", work / f"scene-{i}.png")

    inputs = []
    for i in (0, 1, 2, 0):
        inputs += ["-loop", "1", "-framerate", "30", "-i", work / f"scene-{i}.png"]
    # Hold each scene for 1.6 seconds, then slide for 0.4 seconds. The final
    # transition returns to LOOK so playback loops without an abrupt cut.
    transitions = (
        "[0:v][1:v]xfade=transition=slideleft:duration=0.4:offset=1.6[a];"
        "[a][2:v]xfade=transition=slideleft:duration=0.4:offset=3.6[b];"
        "[b][3:v]xfade=transition=slideleft:duration=0.4:offset=5.6,"
        "format=yuv420p[out]"
    )
    OUTPUT.mkdir(parents=True, exist_ok=True)
    ffmpeg(*inputs, "-filter_complex", transitions, "-map", "[out]", "-t", "6",
           "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "20",
           "-movflags", "+faststart", OUTPUT / "teaser.mp4")
    ffmpeg("-i", work / "scene-0.png", "-frames:v", "1", "-q:v", "2",
           OUTPUT / "teaser-poster.jpg")


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="look-thumbnail-") as directory:
        render(Path(directory))
