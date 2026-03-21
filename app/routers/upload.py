# ---------------------------------------------------------------------------
# Upload router — PDF processing
# ---------------------------------------------------------------------------

from __future__ import annotations

from fastapi import APIRouter, UploadFile, File

from app.services.upload import read_pdf, summarize_chunks

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post("/pdf")
async def read_pdf_api(file: UploadFile = File(...)):
    """Extract text from a PDF and return summarised slides."""
    pdf_data = read_pdf(file)
    summaries = summarize_chunks(pdf_data["chunks"])
    return {"slides": summaries}


@router.post("/summarize")
async def summarize_chunks_api(chunks: list[str]):
    """Summarise a list of text chunks into slide-ready cards."""
    summaries = summarize_chunks(chunks)
    return {"slides": summaries}
