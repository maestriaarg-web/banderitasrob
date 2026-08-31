"use client";

import { useState } from "react";

export default function ExamForm() {
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);

  function handleSubmit() {
    console.log("Resolver examen:", {
      texto: text,
      archivo: file ? { nombre: file.name, tipo: file.type, tamano: file.size } : null,
    });
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

      <button
        type="button"
        onClick={handleSubmit}
        className="self-start rounded-md bg-foreground px-4 py-2 text-background"
      >
        Resolver examen
      </button>
    </div>
  );
}
