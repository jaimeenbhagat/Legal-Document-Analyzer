"""
FastAPI Application - Legal Document Analysis System
Main API endpoints for PDF upload and chat interaction.
Serves both API routes and static Next.js frontend (in Docker deployment).
"""

import os
import shutil
from typing import List, Optional
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException, Body, Request
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.config import get_settings, ensure_directories
from app.ingest import DocumentIngestionPipeline
from app.chat import LegalDocumentChatbot


# Check if we're running in Docker with static frontend
STATIC_DIR = Path("/app/static")
SERVE_STATIC = STATIC_DIR.exists() and (STATIC_DIR / "index.html").exists()

# Initialize FastAPI app
app = FastAPI(
    title="Legal Document Analysis System",
    description="RAG-powered legal document analysis API. Upload PDFs and ask questions about their content.",
    version="1.0.0",
    # Hide docs in production if serving frontend
    docs_url="/api/docs" if SERVE_STATIC else "/docs",
    redoc_url="/api/redoc" if SERVE_STATIC else "/redoc",
    openapi_url="/api/openapi.json" if SERVE_STATIC else "/openapi.json",
)

# CORS Configuration
# In production, set ALLOWED_ORIGINS env var to your Vercel domain
# Example: ALLOWED_ORIGINS=https://your-app.vercel.app,https://your-app-git-main-user.vercel.app
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS", 
    "http://localhost:3000,http://127.0.0.1:3000,https://*.vercel.app"
).split(",")

# Allow all origins if wildcard is present (for development/Vercel previews)
allow_all = any("*" in origin for origin in ALLOWED_ORIGINS)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all else ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for request/response validation
class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    question: str = Field(..., description="Natural language question about the documents")
    top_k: Optional[int] = Field(None, description="Number of document chunks to retrieve (default: 4)")
    document_filter: Optional[List[str]] = Field(None, description="Filter to specific document(s) by filename")


class Citation(BaseModel):
    """Citation model with page, source, and excerpt"""
    page: int | str
    source: str
    excerpt: str


class ChatResponse(BaseModel):
    """Response model for chat endpoint with citations and risk classification"""
    answer: str
    risk_level: str
    risk_reason: str
    citations: List[Citation]
    sources: List[dict]
    chunk_count: int
    disclaimer: str = ""
    documents_used: List[str] = []  # List of document names used in the response


class UploadResponse(BaseModel):
    """Response model for upload endpoint"""
    message: str
    files_processed: int
    files_failed: int
    failed_files: List[str]
    processed_files: List[str] = []  # Add list of successfully processed filenames


class DocumentInfo(BaseModel):
    """Information about an uploaded document"""
    filename: str
    page_count: int
    chunk_count: int
    upload_date: Optional[str] = None


class DocumentsListResponse(BaseModel):
    """Response model for listing documents"""
    documents: List[DocumentInfo]
    total_count: int


# Global instances (initialized on startup)
chatbot = None
ingestion_pipeline = None


@app.on_event("startup")
async def startup_event():
    """
    Application startup tasks:
    1. Create necessary directories
    2. Initialize ingestion pipeline
    3. Initialize chatbot
    4. Load existing vector store (if any)
    """
    global chatbot, ingestion_pipeline
    
    print("=" * 50)
    print("🚀 Starting Legal Document Analysis System")
    print("=" * 50)
    
    # Ensure required directories exist
    ensure_directories()
    
    # Initialize components
    settings = get_settings()
    ingestion_pipeline = DocumentIngestionPipeline()
    chatbot = LegalDocumentChatbot()
    
    # Try to load existing vector store
    chatbot.initialize_vector_store()
    
    print(f"✓ Application started successfully")
    print(f"✓ PDF storage: {settings.pdf_storage_path}")
    print(f"✓ FAISS index: {settings.faiss_index_path}")
    print(f"✓ Serving static frontend: {SERVE_STATIC}")
    print("=" * 50)


@app.get("/api")
async def api_root():
    """
    API root endpoint - health check and info.
    """
    return {
        "message": "Legal Document Analysis System API",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "upload": "POST /upload-pdf",
            "chat": "POST /chat",
            "health": "GET /health"
        }
    }


@app.get("/health")
@app.get("/api/health")
async def health_check():
    """
    Health check endpoint.
    Verifies that vector store is initialized.
    """
    vector_store_status = "initialized" if chatbot.vector_store is not None else "not initialized"
    
    # Get list of available documents
    available_documents = []
    if chatbot.vector_store is not None:
        available_documents = chatbot.get_available_documents()
    
    return {
        "status": "healthy",
        "vector_store": vector_store_status,
        "message": "Upload PDFs to initialize the system" if vector_store_status == "not initialized" else "System ready",
        "available_documents": available_documents
    }


@app.get("/documents", response_model=DocumentsListResponse)
@app.get("/api/documents", response_model=DocumentsListResponse)
async def list_documents():
    """
    List all uploaded documents with metadata.
    
    Returns:
        List of documents with filename, page count, and chunk count
    """
    if chatbot.vector_store is None:
        return DocumentsListResponse(documents=[], total_count=0)
    
    try:
        documents = chatbot.get_documents_info()
        return DocumentsListResponse(
            documents=documents,
            total_count=len(documents)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing documents: {str(e)}"
        )


@app.post("/upload-pdf", response_model=UploadResponse)
@app.post("/api/upload-pdf", response_model=UploadResponse)
async def upload_pdf(files: List[UploadFile] = File(...)):
    """
    Upload one or more PDF files for analysis.
    
    Process:
    1. Validate file types (must be PDF)
    2. Save files to storage directory
    3. Ingest into RAG pipeline (extract, chunk, embed, index)
    4. Update FAISS vector store
    
    Args:
        files: List of PDF files (multipart/form-data)
    
    Returns:
        Upload status with success/failure counts
    
    Example:
        curl -X POST "http://localhost:8000/upload-pdf" \\
             -F "files=@contract.pdf" \\
             -F "files=@nda.pdf"
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    settings = get_settings()
    saved_paths = []
    failed_files = []
    
    # Step 1: Validate and save files
    for file in files:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            failed_files.append(f"{file.filename} (not a PDF)")
            continue
        
        try:
            # Save file to storage directory
            file_path = os.path.join(settings.pdf_storage_path, file.filename)
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            saved_paths.append(file_path)
            print(f"✓ Saved: {file.filename}")
        
        except Exception as e:
            failed_files.append(f"{file.filename} (save error: {str(e)})")
            print(f"✗ Failed to save: {file.filename}")
    
    # Step 2: Ingest saved PDFs
    if saved_paths:
        print(f"\n⏳ Ingesting {len(saved_paths)} PDF(s)...")
        results = ingestion_pipeline.ingest_multiple_pdfs(saved_paths)
        
        # Reload vector store in chatbot
        chatbot.initialize_vector_store()
        
        # Extract just the filenames from saved paths
        processed_filenames = [os.path.basename(path) for path in saved_paths if os.path.basename(path) not in results['failed_files']]
        
        return UploadResponse(
            message=f"Successfully processed {results['success']} file(s)",
            files_processed=results['success'],
            files_failed=results['failed'] + len(failed_files),
            failed_files=results['failed_files'] + failed_files,
            processed_files=processed_filenames
        )
    
    else:
        raise HTTPException(
            status_code=400,
            detail=f"No valid PDF files uploaded. Errors: {failed_files}"
        )


@app.post("/chat", response_model=ChatResponse)
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Ask questions about uploaded documents.
    
    RAG Pipeline with Citations and Risk Classification:
    1. Retrieve relevant chunks from FAISS (based on semantic similarity)
    2. Optionally filter by specific document(s)
    3. Format context with metadata (source, page numbers)
    4. Generate answer using Gemini LLM with structured JSON output
    5. Parse citations and risk classification
    6. Return answer with citations, risk level, and source metadata
    
    Args:
        request: ChatRequest with question, optional top_k, and optional document_filter
    
    Returns:
        ChatResponse with answer, risk classification, citations, sources, and documents_used
    
    Example:
        curl -X POST "http://localhost:8000/chat" \\
             -H "Content-Type: application/json" \\
             -d '{"question": "Summarize this document", "document_filter": ["contract.pdf"]}'
    """
    # Validate vector store is initialized
    if chatbot.vector_store is None:
        if not chatbot.initialize_vector_store():
            raise HTTPException(
                status_code=400,
                detail="No documents uploaded yet. Please upload PDFs first using /upload-pdf"
            )
    
    # Validate question
    if not request.question or len(request.question.strip()) == 0:
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    try:
        # Execute RAG pipeline with optional document filter
        result = chatbot.answer_question(
            query=request.question,
            k=request.top_k,
            document_filter=request.document_filter
        )
        
        return ChatResponse(
            answer=result["answer"],
            risk_level=result["risk_level"],
            risk_reason=result["risk_reason"],
            citations=result["citations"],
            sources=result["sources"],
            chunk_count=result["chunk_count"],
            disclaimer=result.get("disclaimer", ""),
            documents_used=result.get("documents_used", [])
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing question: {str(e)}"
        )


@app.post("/analyze/{analysis_type}")
@app.post("/api/analyze/{analysis_type}")
async def analyze_document(analysis_type: str):
    """
    Run pre-defined analysis on uploaded documents.
    
    Available analysis types:
    - obligations: Extract obligations and responsibilities
    - termination: Identify termination clauses
    - penalties: Find penalties and consequences
    - risks: Highlight risks and liabilities
    - parties: List involved parties
    - duration: Extract timeline information
    
    Args:
        analysis_type: Type of analysis to perform
    
    Returns:
        Analysis results
    
    Example:
        curl -X POST "http://localhost:8000/analyze/termination"
    """
    if chatbot.vector_store is None:
        if not chatbot.initialize_vector_store():
            raise HTTPException(
                status_code=400,
                detail="No documents uploaded yet. Please upload PDFs first"
            )
    
    try:
        result = chatbot.analyze_document(analysis_type)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during analysis: {str(e)}"
        )


# =============================================================================
# STATIC FILE SERVING (Docker Deployment)
# =============================================================================

if SERVE_STATIC:
    # Mount static files for Next.js assets (_next folder)
    app.mount("/_next", StaticFiles(directory=str(STATIC_DIR / "_next")), name="next-static")
    
    # Serve other static assets
    @app.get("/favicon.ico")
    async def favicon():
        favicon_path = STATIC_DIR / "favicon.ico"
        if favicon_path.exists():
            return FileResponse(favicon_path)
        raise HTTPException(status_code=404)
    
    # Catch-all route for SPA - must be last!
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """
        Serve the Next.js static export.
        - Try to serve the exact file if it exists
        - Fall back to index.html for SPA routing
        """
        # Don't intercept API routes
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        
        # Try exact file path
        file_path = STATIC_DIR / full_path
        
        # Check for directory with index.html (Next.js trailingSlash)
        if file_path.is_dir():
            index_path = file_path / "index.html"
            if index_path.exists():
                return FileResponse(index_path, media_type="text/html")
        
        # Try with .html extension
        html_path = STATIC_DIR / f"{full_path}.html"
        if html_path.exists():
            return FileResponse(html_path, media_type="text/html")
        
        # Try exact file
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        
        # Fall back to index.html for SPA routing
        index_path = STATIC_DIR / "index.html"
        if index_path.exists():
            return FileResponse(index_path, media_type="text/html")
        
        raise HTTPException(status_code=404, detail="Page not found")
    
    # Root route
    @app.get("/")
    async def serve_index():
        """Serve the main index.html"""
        index_path = STATIC_DIR / "index.html"
        if index_path.exists():
            return FileResponse(index_path, media_type="text/html")
        raise HTTPException(status_code=404, detail="Frontend not found")


# Run the application
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True  # Auto-reload on code changes (development only)
    )
