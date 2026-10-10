from openai import AsyncOpenAI
from app.core.config import settings
from app.core.text import normalize_citations

client = AsyncOpenAI(api_key=settings.llm_api_key or "missing", base_url=settings.llm_base_url)

SYSTEM = """You are FowForge, a grounded enterprise knowledge assistant.
Use only the supplied context for factual claims.
If the context does not contain enough information, explicitly say that the information is not available in the provided knowledge base.
Never invent facts, sources, numbers, or citations.
Cite supporting sources inline as [S1], [S2], etc.
Keep answers concise and useful.
"""



async def answer(question: str, contexts: list[dict]) -> str:
    if not contexts:
        return "I’m sorry, but the provided context does not contain enough information to answer that question."
    context = "\n\n".join(f"[{c['source_id']}] {c['text']}" for c in contexts)
    prompt = f"Question:\n{question}\n\nContext:\n{context}\n\nAnswer concisely and cite factual claims."
    response = await client.chat.completions.create(
        model=settings.llm_model,
        messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
        temperature=0.1,
    )
    return normalize_citations(response.choices[0].message.content or "I could not generate an answer.")


async def stream_answer(question: str, contexts: list[dict]):
    context = "\n\n".join(f"[{c['source_id']}] {c['text']}" for c in contexts)
    prompt = f"Question:\n{question}\n\nContext:\n{context}\n\nAnswer concisely and cite factual claims."
    stream = await client.chat.completions.create(
        model=settings.llm_model,
        messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
        temperature=0.1,
        stream=True,
    )
    async for event in stream:
        delta = event.choices[0].delta.content if event.choices else None
        if delta:
            yield normalize_citations(delta)
