"""Agrupa los segmentos de cada transcripcion en bloques de ~300 palabras,
genera embeddings locales (multilingual-e5-large) y guarda todo en un
JSONL listo para cargar a Supabase.

Uso:
    .venv/Scripts/python.exe chunk_and_embed.py
"""

import json

from sentence_transformers import SentenceTransformer

from common import TRANSCRIPTS_DIR, load_videos

TARGET_WORDS_PER_CHUNK = 300
OUTPUT_FILE = TRANSCRIPTS_DIR.parent / "chunks_with_embeddings.jsonl"
MODEL_NAME = "intfloat/multilingual-e5-large"


def chunk_segments(segments, target_words=TARGET_WORDS_PER_CHUNK):
    """Agrupa segmentos consecutivos hasta juntar ~target_words palabras."""
    chunks = []
    current_texts = []
    current_words = 0
    start_time = None

    for seg in segments:
        if start_time is None:
            start_time = seg["start"]
        current_texts.append(seg["text"])
        current_words += len(seg["text"].split())

        if current_words >= target_words:
            chunks.append(
                {
                    "start_time": start_time,
                    "end_time": seg["end"],
                    "content": " ".join(current_texts).strip(),
                }
            )
            current_texts = []
            current_words = 0
            start_time = None

    if current_texts:
        chunks.append(
            {
                "start_time": start_time,
                "end_time": segments[-1]["end"],
                "content": " ".join(current_texts).strip(),
            }
        )

    return chunks


def main():
    videos = load_videos()
    model = SentenceTransformer(MODEL_NAME)

    all_chunks = []
    for v in videos:
        transcript_path = TRANSCRIPTS_DIR / f"{v['basename']}.json"
        data = json.loads(transcript_path.read_text(encoding="utf-8"))
        chunks = chunk_segments(data["segmentos"])
        for i, c in enumerate(chunks):
            all_chunks.append(
                {
                    "semana": v["semana"],
                    "titulo": v["titulo"],
                    "url_video": v["url_video"],
                    "chunk_index": i,
                    "start_time": c["start_time"],
                    "end_time": c["end_time"],
                    "content": c["content"],
                }
            )
        print(f"[{v['index']:02d}/{len(videos)}] {len(chunks)} bloques: {v['titulo']}")

    print(f"\nTotal de bloques a embeber: {len(all_chunks)}")

    texts = ["passage: " + c["content"] for c in all_chunks]
    embeddings = model.encode(
        texts, batch_size=16, show_progress_bar=True, normalize_embeddings=True
    )

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for c, emb in zip(all_chunks, embeddings):
            c["embedding"] = emb.tolist()
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    print(f"\nListo: {len(all_chunks)} bloques con embeddings en {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
