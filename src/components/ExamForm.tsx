"use client";

import { useState } from "react";

type Fuente = { titulo: string; url_video: string; start_time: number };

export default function ExamForm() {
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [respuesta, setRespuesta] = useState<string | null>(null);
  const [fuentes, setFuentes] = useState<Fuente[]>([]);

  async function handleSubmit() {
    if (!text.trim() && !file) {
      setError("Pegá el texto del examen o subí una foto.");
      return;
    }

    setLoading(true);
    setError(null);
    setRespuesta(null);
    setFuentes([]);

    try {
      const formData = new FormData();
      formData.append("texto", text);
      if (file) formData.append("archivo", file);

      const res = await fetch("/api/resolver-examen", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();

      if (!res.ok) {
        setError(data.error ?? "Ocurrió un error resolviendo el examen.");
        return;
      }

      setRespuesta(data.respuesta);
      setFuentes(data.fuentes ?? []);
    } catch {
      setError("No se pudo conectar con el servidor.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex w-full max-w-2xl flex-col gap-4">
      <div className="flex flex-col gap-1">
        <label htmlFor="exam-text" className="text-sm font-medium">
          Texto del examen
        </label>
        <textarea
          id="exam-text"
          rows={12}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Pegá acá el texto del examen..."
          className="resize-y rounded-md border border-black/10 px-3 py-2 dark:border-white/20"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="exam-photo" className="text-sm font-medium">
          Foto del examen
        </label>
        <input
          id="exam-photo"
          type="file"
          accept="image/*"
          capture="environment"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          className="text-sm"
        />
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <button
        type="button"
        onClick={handleSubmit}
        disabled={loading}
        className="self-start rounded-md bg-foreground px-4 py-2 text-background disabled:opacity-50"
      >
        {loading ? "Resolviendo..." : "Resolver examen"}
      </button>

      {respuesta && (
        <div className="flex flex-col gap-3 rounded-md border border-black/10 p-4 dark:border-white/20">
          <h2 className="font-semibold">Respuesta</h2>
          <p className="whitespace-pre-wrap text-sm">{respuesta}</p>

          {fuentes.length > 0 && (
            <div className="flex flex-col gap-1 border-t border-black/10 pt-3 text-xs opacity-80 dark:border-white/20">
              <span className="font-medium">Fuentes consultadas:</span>
              {fuentes.map((f, i) => (
                <a
                  key={i}
                  href={f.url_video}
                  target="_blank"
                  rel="noreferrer"
                  className="underline"
                >
                  {f.titulo} (min {Math.floor(f.start_time / 60)})
                </a>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
