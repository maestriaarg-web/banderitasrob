"""Extrae el audio de cada video descargado y lo transcribe con faster-whisper
corriendo en GPU (modelo 'medium', cae a 'small' si la GPU se queda sin
memoria). Guarda un JSON por video en transcripts/ con el texto completo y
los segmentos con timestamp.

Uso:
    .venv/Scripts/python.exe transcribe_videos.py
"""

import json
import subprocess
import sys

from common import add_cuda_dlls_to_path, AUDIO_DIR, TRANSCRIPTS_DIR, VIDEOS_DIR, load_videos

add_cuda_dlls_to_path()

from faster_whisper import WhisperModel  # noqa: E402 (needs PATH set first)

MODELS_TO_TRY = ["medium", "small"]


def extract_audio(video_path, audio_path) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(video_path),
            "-ac", "1", "-ar", "16000", "-vn",
            str(audio_path),
        ],
        check=True,
        capture_output=True,
    )


def load_model(model_size: str) -> WhisperModel:
    print(f"Cargando modelo Whisper '{model_size}' en GPU...")
    return WhisperModel(model_size, device="cuda", compute_type="int8_float16")


def transcribe(model: WhisperModel, audio_path):
    segments, _info = model.transcribe(str(audio_path), language="es", beam_size=5)
    segment_list = [
        {"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()}
        for s in segments
    ]
    full_text = " ".join(s["text"] for s in segment_list)
    return full_text, segment_list


def main():
    videos = load_videos()
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

    model = None
    model_size_used = None
    failed = []

    for v in videos:
        out_path = TRANSCRIPTS_DIR / f"{v['basename']}.json"
        if out_path.exists():
            print(f"[{v['index']:02d}/{len(videos)}] ya transcripto, salteo: {out_path.name}")
            continue

        video_path = VIDEOS_DIR / f"{v['basename']}.mp4"
        if not video_path.exists():
            print(f"[{v['index']:02d}/{len(videos)}] falta el video, salteo: {video_path.name}", file=sys.stderr)
            failed.append(v)
            continue

        audio_path = AUDIO_DIR / f"{v['basename']}.wav"
        print(f"[{v['index']:02d}/{len(videos)}] extrayendo audio: {v['titulo']}")
        try:
            if not audio_path.exists():
                extract_audio(video_path, audio_path)
        except subprocess.CalledProcessError as e:
            print(f"  ERROR extrayendo audio: {e.stderr.decode(errors='ignore')[:500]}", file=sys.stderr)
            failed.append(v)
            continue

        print(f"[{v['index']:02d}/{len(videos)}] transcribiendo...")
        for model_size in MODELS_TO_TRY:
            try:
                if model is None or model_size_used != model_size:
                    model = load_model(model_size)
                    model_size_used = model_size
                full_text, segments = transcribe(model, audio_path)
                break
            except RuntimeError as e:
                if "out of memory" in str(e).lower() and model_size != MODELS_TO_TRY[-1]:
                    print(f"  sin memoria con '{model_size}', probando el siguiente modelo mas chico...")
                    model = None
                    continue
                print(f"  ERROR transcribiendo: {e}", file=sys.stderr)
                failed.append(v)
                full_text = None
                break
        else:
            failed.append(v)
            full_text = None

        if full_text is None:
            continue

        out_path.write_text(
            json.dumps(
                {
                    "semana": v["semana"],
                    "titulo": v["titulo"],
                    "url_video": v["url_video"],
                    "modelo_whisper": model_size_used,
                    "texto_completo": full_text,
                    "segmentos": segments,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"  OK -> {out_path.name}")

    if failed:
        print(f"\n{len(failed)} video(s) fallaron:")
        for v in failed:
            print(f"  - [{v['index']:02d}] {v['titulo']}")
        sys.exit(1)

    print(f"\nListo: transcripciones en {TRANSCRIPTS_DIR}")


if __name__ == "__main__":
    main()
