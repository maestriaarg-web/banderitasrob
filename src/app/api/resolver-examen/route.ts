import { NextRequest, NextResponse } from "next/server";
import Anthropic from "@anthropic-ai/sdk";
import { createClient } from "@/lib/supabase/server";
// TODO: volver a la búsqueda semántica (embedQuery + match_knowledge_chunks)
// una vez que haya créditos cargados en OpenAI. Mientras tanto usamos
// match_knowledge_chunks_keyword (búsqueda por palabras clave, sin API paga).
// import { embedQuery } from "@/lib/openai/embeddings";

const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

type KnowledgeChunk = {
  id: number;
  semana: number;
  titulo: string;
  url_video: string;
  start_time: number;
  end_time: number;
  content: string;
  similarity: number;
};

type ImageMediaType = "image/jpeg" | "image/png" | "image/gif" | "image/webp";

function toImageMediaType(mime: string): ImageMediaType {
  if (mime === "image/png" || mime === "image/gif" || mime === "image/webp") {
    return mime;
  }
  return "image/jpeg";
}

export async function POST(request: NextRequest) {
  try {
    return await resolverExamen(request);
  } catch (err) {
    console.error("Error en /api/resolver-examen:", err);
    return NextResponse.json(
      { error: "No se pudo resolver el examen. Intentá de nuevo en unos minutos." },
      { status: 500 },
    );
  }
}

async function resolverExamen(request: NextRequest) {
  const formData = await request.formData();
  const texto = (formData.get("texto") as string | null)?.trim() ?? "";
  const archivo = formData.get("archivo") as File | null;

  let imageBase64: string | null = null;
  let imageMediaType: ImageMediaType = "image/jpeg";

  if (archivo && archivo.size > 0) {
    const buffer = Buffer.from(await archivo.arrayBuffer());
    imageBase64 = buffer.toString("base64");
    imageMediaType = toImageMediaType(archivo.type);
  }

  if (!texto && !imageBase64) {
    return NextResponse.json(
      { error: "Pegá el texto del examen o subí una foto." },
      { status: 400 },
    );
  }

  // Si solo hay foto, le pedimos a Claude que transcriba las preguntas
  // primero, para tener con qué buscar en la base de conocimiento.
  let queryText = texto;
  if (!queryText && imageBase64) {
    const extraction = await anthropic.messages.create({
      model: "claude-opus-5",
      max_tokens: 4096,
      messages: [
        {
          role: "user",
          content: [
            {
              type: "image",
              source: { type: "base64", media_type: imageMediaType, data: imageBase64 },
            },
            {
              type: "text",
              text: "Transcribí textualmente todas las preguntas y opciones de este examen de opción múltiple, en texto plano.",
            },
          ],
        },
      ],
    });
    const textBlock = extraction.content.find((b) => b.type === "text");
    queryText = textBlock && textBlock.type === "text" ? textBlock.text : "";
  }

  let chunks: KnowledgeChunk[] = [];
  if (queryText) {
    const supabase = await createClient();
    const { data, error } = await supabase.rpc("match_knowledge_chunks_keyword", {
      query_text: queryText,
      match_count: 10,
    });
    if (error) {
      return NextResponse.json(
        { error: `Error buscando en la base de conocimiento: ${error.message}` },
        { status: 500 },
      );
    }
    chunks = (data ?? []) as KnowledgeChunk[];
  }

  const contexto = chunks
    .map(
      (c) =>
        `### ${c.titulo} (semana ${c.semana}, min ${Math.floor(c.start_time / 60)})\n${c.content}`,
    )
    .join("\n\n---\n\n");

  const userContent: Anthropic.MessageParam["content"] = [];
  if (imageBase64) {
    userContent.push({
      type: "image",
      source: { type: "base64", media_type: imageMediaType, data: imageBase64 },
    });
  }
  userContent.push({
    type: "text",
    text:
      `Examen a resolver:\n${texto || queryText}\n\n` +
      `Material de referencia de las clases del curso (usalo como fuente principal para responder):\n\n${contexto}`,
  });

  const answer = await anthropic.messages.create({
    model: "claude-opus-5",
    max_tokens: 8000,
    system:
      "Sos un asistente que ayuda a resolver exámenes de opción múltiple de un curso de terapia " +
      "intensiva (shock y sepsis). Respondé cada pregunta indicando la opción correcta y una " +
      "justificación breve basada casi exclusivamente en el material de referencia provisto, " +
      "citando de qué clase sale cada respuesta. Si el material no alcanza para responder con " +
      "confianza, decilo explícitamente en vez de inventar.",
    messages: [{ role: "user", content: userContent }],
  });

  const respuesta = answer.content
    .filter((b): b is Anthropic.TextBlock => b.type === "text")
    .map((b) => b.text)
    .join("\n");

  return NextResponse.json({
    respuesta,
    fuentes: chunks.map((c) => ({ titulo: c.titulo, url_video: c.url_video, start_time: c.start_time })),
  });
}
