const EMBEDDING_MODEL = "text-embedding-3-small";

export async function embedQuery(text: string): Promise<number[]> {
  const response = await fetch("https://api.openai.com/v1/embeddings", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${process.env.OPENAI_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ model: EMBEDDING_MODEL, input: text }),
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`OpenAI embeddings error (${response.status}): ${body}`);
  }

  const data = await response.json();
  return data.data[0].embedding as number[];
}
