from pathlib import Path
from pypdf import PdfReader
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Document, Chunk
from app.services.chunking import chunk_text
from app.services.embeddings import embed

async def ingest(db: AsyncSession, filename: str, data: bytes) -> Document:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        import io
        reader = PdfReader(io.BytesIO(data))
        text = "\n".join((p.extract_text() or "") for p in reader.pages)
    else:
        text = data.decode("utf-8", errors="ignore")
    chunks = chunk_text(text)
    doc = Document(name=filename, content=text)
    db.add(doc)
    await db.flush()
    vectors = embed(chunks) if chunks else []
    for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
        db.add(Chunk(document_id=doc.id, text=chunk, chunk_index=i, embedding=vector,
                     metadata_json={"filename": filename, "chunk_index": i}))
    await db.commit()
    await db.refresh(doc)
    return doc
