import csv
import os
import re
import sys
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent
VIDEOS_CSV = PIPELINE_DIR / "videos.csv"
VIDEOS_DIR = PIPELINE_DIR / "videos"
AUDIO_DIR = PIPELINE_DIR / "audio"
TRANSCRIPTS_DIR = PIPELINE_DIR / "transcripts"


def add_cuda_dlls_to_path():
    """faster-whisper (ctranslate2) needs cuBLAS/cuDNN on PATH to use the GPU
    when those libraries come from pip packages instead of a system install."""
    site_packages = Path(sys.executable).resolve().parent.parent / "Lib" / "site-packages"
    extra_dirs = []
    for pkg in ["cublas", "cudnn", "cuda_nvrtc"]:
        bin_dir = site_packages / "nvidia" / pkg / "bin"
        if bin_dir.is_dir():
            extra_dirs.append(str(bin_dir))
    if extra_dirs:
        os.environ["PATH"] = os.pathsep.join(extra_dirs) + os.pathsep + os.environ.get("PATH", "")


def slugify(text: str) -> str:
    text = text.lower()
    text = (
        text.replace("á", "a").replace("é", "e").replace("í", "i")
        .replace("ó", "o").replace("ú", "u").replace("ñ", "n")
    )
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:80]


def load_videos():
    """Returns a list of dicts: {semana, titulo, url_video, slug, basename}."""
    videos = []
    with open(VIDEOS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            slug = slugify(row["titulo"])
            basename = f"{i:02d}_semana{row['semana']}_{slug}"
            videos.append(
                {
                    "index": i,
                    "semana": row["semana"],
                    "titulo": row["titulo"],
                    "url_video": row["url_video"],
                    "basename": basename,
                }
            )
    return videos
