"""Regenera los embeddings de chunks_with_embeddings.jsonl usando la API de
OpenAI (text-embedding-3-small, 1536 dims) en vez del modelo local, para que
coincidan con lo que la app en Vercel va a generar en cada busqueda.

Uso:
    .venv/Scripts/python.exe reembed_openai.py
"""

import json
import os
import sys

import requests
from dotenv import load_dotenv

from common import PIPELINE_DIR

INPUT_FILE = PIPELINE_DIR / "chunks_with_embeddings.jsonl"
OUTPUT_FILE = PIPELINE_DIR / "chunks_with_embeddings_openai.jsonl"
MODEL = "text-embedding-3-small"
BATCH_SIZE = 100

load_dotenv(PIPELINE_DIR / ".env")


def main():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Falta OPENAI_API_KEY en pipeline/.env", file=sys.stderr)
        sys.exit(1)

    rows = []
    with open(INPUT_FILE, encoding="utf-8") as f:
        for line in f:
            rows.append(json.loads(line))

    print(f"Re-embebiendo {len(rows)} bloques con {MODEL}...")

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i : i + BATCH_SIZE]
            texts = [r["content"] for r in batch]
            resp = requests.post(
                "https://api.openai.com/v1/embeddings",
                headers=headers,
                json={"model": MODEL, "input": texts},
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()["data"]
            for r, d in zip(batch, data):
                r["embedding"] = d["embedding"]
                out.write(json.dumps(r, ensure_ascii=False) + "\n")
            print(f"  {min(i + BATCH_SIZE, len(rows))}/{len(rows)}")

    print(f"\nListo: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
