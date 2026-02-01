# Read routes for data retrieval
# Handles GET requests for courses, conversations, and messages
# Examples:
# curl "http://localhost:8000/read/courses?user_id=123e4567-e89b-12d3-a456-426614174000"
# curl "http://localhost:8000/read/conversation?user_id=123e4567-e89b-12d3-a456-426614174000"
# curl "http://localhost:8000/read/messages?conversation_id=123e4567-e89b-12d3-a456-426614174000"

from matplotlib import text
from app.services.upload import read_pdf, summarize_chunks
from fastapi import APIRouter, FastAPI, UploadFile, File


app = FastAPI()

router = APIRouter(prefix="/upload", tags=["upload"])

@router.post("/pdf")
async def read_pdfAPI(file: UploadFile = File(...)):

    pdf_data = read_pdf(file)

    summaries = summarize_chunks(pdf_data["chunks"])

    return {
        "slides": summaries
    }


@router.post("/summarize")
async def summarize_chunksAPI(chunks: list[str]):

    summaries = summarize_chunks(chunks)

    return {
        "slides": summaries
    }
