from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Chunk
from app.services.embeddings import embed


async def retrieve(db: AsyncSession, query: str, top_k: int = 6):
    q = embed([query])[0]
    distance = Chunk.embedding.cosine_distance(q)
    stmt = select(Chunk).order_by(distance).limit(top_k)
    rows = (await db.execute(stmt)).scalars().all()
    return rows


async def retrieve_with_scores(db: AsyncSession, query: str, top_k: int = 6):
    q = embed([query])[0]
    distance = Chunk.embedding.cosine_distance(q)
    stmt = select(Chunk, distance.label("distance")).order_by(distance).limit(top_k)
    rows = (await db.execute(stmt)).all()
    return [(chunk, max(0.0, min(1.0, 1.0 - float(dist)))) for chunk, dist in rows]
