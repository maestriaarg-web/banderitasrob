"""Carga chunks_with_embeddings.jsonl a la tabla public.knowledge_chunks
de Supabase usando la service_role key (bypassa RLS).

Uso:
    .venv/Scripts/python.exe load_to_supabase.py
"""

import json
import os
import sys

from dotenv import load_dotenv
from supabase import create_client

from common import PIPELINE_DIR

INPUT_FILE = PIPELINE_DIR / "chunks_with_embeddings.jsonl"
BATCH_SIZE = 50

load_dotenv(PIPELINE_DIR / ".env")


def main():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("Falta SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY en pipeline/.env", file=sys.stderr)
        sys.exit(1)

    client = create_client(url, key)

    rows = []
    with open(INPUT_FILE, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            rows.append(
                {
                    "semana": int(r["semana"]),
                    "titulo": r["titulo"],
                    "url_video": r["url_video"],
                    "chunk_index": r["chunk_index"],
                    "start_time": r["start_time"],
                    "end_time": r["end_time"],
                    "content": r["content"],
                    "embedding": r["embedding"],
                }
            )

    print(f"Cargando {len(rows)} filas en lotes de {BATCH_SIZE}...")
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i : i + BATCH_SIZE]
        client.table("knowledge_chunks").insert(batch).execute()
        print(f"  {min(i + BATCH_SIZE, len(rows))}/{len(rows)}")

    print("Listo.")


if __name__ == "__main__":
    main()
