import json
import re
import time
from uuid import uuid4
from pathlib import Path
from fastapi import APIRouter, Depends, File, UploadFile, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.models import Document, Message
from app.services.ingestion import ingest
from app.services.rag import run_rag
from app.services.retrieval import retrieve
from app.services.llm import stream_answer
from app.core.rate_limit import enforce
from app.core.security import require_api_key
from app.core.config import settings

router = APIRouter()

ALLOWED = {".txt", ".md", ".pdf"}


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    conversation_id: str | None = None


@router.get("/health")
async def health():
    return {"status": "ok", "service": "fowforge-api"}


@router.get("/ready")
async def ready(db: AsyncSession = Depends(get_db)):
    await db.execute(select(func.count(Document.id)))
    return {"status": "ready", "database": "ok"}


@router.get("/documents", dependencies=[Depends(require_api_key)])
async def documents(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Document).order_by(Document.created_at.desc()))).scalars().all()
    return [{"id": d.id, "name": d.name, "created_at": d.created_at.isoformat()} for d in rows]


@router.post("/documents", dependencies=[Depends(require_api_key)])
async def upload_document(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    filename = file.filename or "document.txt"
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED:
        raise HTTPException(status_code=415, detail="Supported files: TXT, MD, PDF")
    data = await file.read()
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"Maximum upload size is {settings.max_upload_mb} MB")
    doc = await ingest(db, filename, data)
    return {"id": doc.id, "name": doc.name}


@router.delete("/documents/{document_id}", dependencies=[Depends(require_api_key)])
async def delete_document(document_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail="document not found")
    await db.delete(doc)
    await db.commit()
    return {"message": "document deleted", "id": document_id}


@router.post("/chat", dependencies=[Depends(require_api_key)])
async def chat(payload: ChatRequest, request: Request, db: AsyncSession = Depends(get_db)):
    await enforce(request)
    started = time.perf_counter()
    response, contexts, retrieval_ms = await run_rag(db, payload.question.strip())
    conversation_id = payload.conversation_id or str(uuid4())
    db.add(Message(conversation_id=conversation_id, role="user", content=payload.question, sources=[]))
    db.add(Message(conversation_id=conversation_id, role="assistant", content=response, sources=contexts))
    await db.commit()
    return {
        "answer": response,
        "sources": contexts,
        "conversation_id": conversation_id,
        "meta": {"retrieval_and_generation_ms": round((time.perf_counter() - started) * 1000, 2), "retrieval_ms": retrieval_ms},
    }


@router.post("/chat/stream", dependencies=[Depends(require_api_key)])
async def chat_stream(payload: ChatRequest, request: Request, db: AsyncSession = Depends(get_db)):
    await enforce(request)
    chunks = await retrieve(db, payload.question.strip(), settings.top_k)
    contexts = [{"source_id": f"S{i}", "text": c.text, "document": c.metadata_json.get("filename", "unknown"), "chunk_id": c.id} for i, c in enumerate(chunks, 1)]

    async def events():
        yield f"data: {json.dumps({'type':'sources','sources':contexts})}\n\n"
        if not contexts:
            yield f"data: {json.dumps({'type':'token','text':'I’m sorry, but the provided context does not contain enough information to answer that question.'})}\n\n"
        else:
            async for token in stream_answer(payload.question.strip(), contexts):
                yield f"data: {json.dumps({'type':'token','text':token})}\n\n"
        yield "data: {\"type\":\"done\"}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream", headers={"Cache-Control":"no-cache", "X-Accel-Buffering":"no"})
