import time
from app.core.config import settings
from app.services.retrieval import retrieve_with_scores
from app.services.llm import answer


async def run_rag(db, question: str):
    started = time.perf_counter()
    ranked = await retrieve_with_scores(db, question, settings.top_k)
    contexts = []
    for i, (chunk, score) in enumerate(ranked, 1):
        contexts.append({
            "source_id": f"S{i}",
            "text": chunk.text,
            "document": chunk.metadata_json.get("filename", "unknown"),
            "chunk_id": chunk.id,
            "score": round(score, 4),
        })
    response = await answer(question, contexts)
    return response, contexts, round((time.perf_counter() - started) * 1000, 2)
