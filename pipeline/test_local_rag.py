"""Prueba end-to-end SIN depender de OpenAI ni de Vercel: busca en
chunks_with_embeddings.jsonl (embeddings locales e5-large, generados en el
Sub-proyecto B) y le pide a Claude que responda usando ese contexto.
Sirve para validar el concepto mientras se cargan creditos en OpenAI.

Uso:
    .venv/Scripts/python.exe test_local_rag.py "pregunta del examen"
"""

import json
import os
import sys

import numpy as np
import requests
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from common import PIPELINE_DIR

load_dotenv(PIPELINE_DIR / ".env")
load_dotenv(PIPELINE_DIR.parent / ".env.local")

TOP_K = 8


def cosine_search(query_emb, rows, top_k=TOP_K):
    embs = np.array([r["embedding"] for r in rows])
    q = np.array(query_emb)
    sims = embs @ q / (np.linalg.norm(embs, axis=1) * np.linalg.norm(q))
    top_idx = np.argsort(-sims)[:top_k]
    return [(rows[i], float(sims[i])) for i in top_idx]


def main():
    pregunta = sys.argv[1] if len(sys.argv) > 1 else "Cual es el tratamiento del shock septico refractario?"

    print("Cargando bloques locales...")
    rows = []
    with open(PIPELINE_DIR / "chunks_with_embeddings.jsonl", encoding="utf-8") as f:
        for line in f:
            rows.append(json.loads(line))

    print("Cargando modelo de embeddings (e5-large, local)...")
    model = SentenceTransformer("intfloat/multilingual-e5-large")
    query_emb = model.encode(["query: " + pregunta], normalize_embeddings=True)[0]

    print("Buscando bloques relevantes...")
    resultados = cosine_search(query_emb, rows)

    contexto = "\n\n---\n\n".join(
        f"### {r['titulo']} (min {int(r['start_time'] // 60)})\n{r['content']}"
        for r, _ in resultados
    )

    print("\nBloques encontrados:")
    for r, sim in resultados:
        print(f"  [{sim:.3f}] {r['titulo']} (min {int(r['start_time'] // 60)})")

    print("\nLlamando a Claude...")
    key = os.environ["ANTHROPIC_API_KEY"]
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-opus-5",
            "max_tokens": 2000,
            "system": (
                "Sos un asistente que ayuda a resolver examenes de opcion multiple de un curso de "
                "terapia intensiva (shock y sepsis). Respondé indicando la opcion correcta y una "
                "justificacion breve basada en el material de referencia provisto, citando de que "
                "clase sale. Si el material no alcanza, decilo en vez de inventar."
            ),
            "messages": [
                {
                    "role": "user",
                    "content": f"Pregunta:\n{pregunta}\n\nMaterial de referencia:\n\n{contexto}",
                }
            ],
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    texto = "".join(b["text"] for b in data["content"] if b["type"] == "text")

    print("\n" + "=" * 60)
    print("RESPUESTA DE CLAUDE:")
    print("=" * 60)
    print(texto)


if __name__ == "__main__":
    main()
