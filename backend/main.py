"""
FastAPI Application - Legal Document Analysis System
Main API endpoints for PDF upload and chat interaction.
Session-based document management for isolated chats.
"""

import os
import shutil
from typing import List, Optional, Dict
from pathlib import Path
from datetime import datetime, timedelta

from fastapi import FastAPI, File, UploadFile, HTTPException, Body, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.config import get_settings, ensure_directories
from backend.ingest import DocumentIngestionPipeline
from backend.chat import LegalDocumentChatbot
from backend.validator import get_document_validator


# Initialize FastAPI app
app = FastAPI(
    title="Legal Document Analysis System",
    description="RAG-powered legal document analysis API. Upload PDFs and ask questions about their content.",
    version="1.0.0"
)

# Add CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Next.js default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# SESSION MANAGEMENT
# ============================================

class SessionManager:
    """
    Manages session-based document storage.
    Each chat session has its own isolated documents.
    """
    
    def __init__(self):
        self.sessions: Dict[str, dict] = {}
        self.settings = get_settings()
    
    def get_or_create_session(self, session_id: str) -> dict:
        """Get existing session or create new one."""
        if session_id not in self.sessions:
            # Create new session with its own chatbot and pipeline
            session_dir = os.path.join(self.settings.faiss_index_path, f"session_{session_id}")
            os.makedirs(session_dir, exist_ok=True)
            
            self.sessions[session_id] = {
                "id": session_id,
                "created_at": datetime.now(),
                "chatbot": LegalDocumentChatbot(),
                "pipeline": DocumentIngestionPipeline(),
                "documents": [],
                "index_path": session_dir
            }
            print(f"✓ Created new session: {session_id}")
        
        return self.sessions[session_id]
    
    def get_session(self, session_id: str) -> Optional[dict]:
        """Get session by ID, returns None if not found."""
        return self.sessions.get(session_id)
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session and clean up its resources."""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            # Clean up session directory
            if os.path.exists(session["index_path"]):
                shutil.rmtree(session["index_path"], ignore_errors=True)
            del self.sessions[session_id]
            print(f"✓ Deleted session: {session_id}")
            return True
        return False
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Remove sessions older than max_age_hours."""
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        old_sessions = [
            sid for sid, data in self.sessions.items() 
            if data["created_at"] < cutoff
        ]
        for sid in old_sessions:
            self.delete_session(sid)
        if old_sessions:
            print(f"✓ Cleaned up {len(old_sessions)} old sessions")


# Global session manager
session_manager = SessionManager()


# Pydantic models for request/response validation
class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    question: str = Field(..., description="Natural language question about the documents")
    session_id: Optional[str] = Field(None, description="Session ID for isolated document context")
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
    validation_results: Optional[List[dict]] = None  # Validation details for each file


class ValidationError(BaseModel):
    """Response model for document validation errors"""
    filename: str
    is_valid: bool
    document_type: str
    reason: str
    confidence: str


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
    print("=" * 50)


@app.get("/")
async def root():
    """
    Root endpoint - API health check and info.
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
async def health_check(session_id: Optional[str] = None):
    """
    Health check endpoint.
    If session_id provided, checks that session's vector store.
    Otherwise checks global status.
    """
    if session_id:
        session = session_manager.get_session(session_id)
        if session:
            session_chatbot = session["chatbot"]
            vector_store_status = "initialized" if session_chatbot.vector_store is not None else "not initialized"
            available_documents = session["documents"] if session_chatbot.vector_store else []
            return {
                "status": "healthy",
                "session_id": session_id,
                "vector_store": vector_store_status,
                "message": "Upload PDFs to this session" if vector_store_status == "not initialized" else "Session ready",
                "available_documents": available_documents
            }
    
    # Global health check (for backwards compatibility)
    global_chatbot = chatbot
    vector_store_status = "initialized" if global_chatbot.vector_store is not None else "not initialized"
    
    available_documents = []
    if global_chatbot.vector_store is not None:
        available_documents = global_chatbot.get_available_documents()
    
    return {
        "status": "healthy",
        "vector_store": vector_store_status,
        "message": "Upload PDFs to initialize the system" if vector_store_status == "not initialized" else "System ready",
        "available_documents": available_documents
    }


@app.get("/documents")
async def list_documents(session_id: Optional[str] = None):
    """
    List documents for a specific session or globally.
    
    Args:
        session_id: Optional session ID to get documents for
    
    Returns:
        List of documents with filename, page count, and chunk count
    """
    if session_id:
        session = session_manager.get_session(session_id)
        if session and session["chatbot"].vector_store is not None:
            try:
                documents = session["chatbot"].get_documents_info()
                return DocumentsListResponse(
                    documents=documents,
                    total_count=len(documents)
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")
        return DocumentsListResponse(documents=[], total_count=0)
    
    # Global documents (backwards compatibility)
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
async def upload_pdf(
    files: List[UploadFile] = File(...),
    session_id: Optional[str] = Form(None)
):
    """
    Upload one or more PDF files for analysis.
    
    Process:
    1. Validate file types (must be PDF)
    2. Save files temporarily for validation
    3. Validate if document is a legal document using AI
    4. If valid, ingest into RAG pipeline (extract, chunk, embed, index)
    5. If not valid, delete the file and return error
    
    Args:
        files: List of PDF files (multipart/form-data)
        session_id: Optional session ID for isolated document context
    
    Returns:
        Upload status with success/failure counts and validation results
    
    Example:
        curl -X POST "http://localhost:8000/upload-pdf" \\
             -F "files=@contract.pdf" \\
             -F "session_id=session-123"
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    settings = get_settings()
    validator = get_document_validator()
    
    # Get or create session if session_id provided
    session = None
    session_pipeline = None
    session_chatbot = None
    
    if session_id:
        session = session_manager.get_or_create_session(session_id)
        session_pipeline = session["pipeline"]
        session_chatbot = session["chatbot"]
        print(f"📂 Uploading to session: {session_id}")
    
    saved_paths = []
    failed_files = []
    validation_results = []
    non_legal_files = []
    
    # Create session-specific storage path if needed
    if session_id:
        session_pdf_path = os.path.join(settings.pdf_storage_path, f"session_{session_id}")
        os.makedirs(session_pdf_path, exist_ok=True)
        storage_path = session_pdf_path
    else:
        storage_path = settings.pdf_storage_path
    
    # Step 1: Save files temporarily and validate
    for file in files:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            failed_files.append(f"{file.filename} (not a PDF)")
            validation_results.append({
                "filename": file.filename,
                "is_valid": False,
                "document_type": "Not a PDF",
                "reason": "Only PDF files are accepted",
                "confidence": "HIGH"
            })
            continue
        
        try:
            # Save file to storage directory
            file_path = os.path.join(storage_path, file.filename)
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            print(f"✓ Saved: {file.filename}")
            
            # Step 2: Validate if document is a legal document
            print(f"\n🔍 Validating: {file.filename}")
            validation = validator.validate_document(file_path)
            
            validation_results.append({
                "filename": file.filename,
                "is_valid": validation["is_valid"],
                "document_type": validation["document_type"],
                "reason": validation["reason"],
                "confidence": validation["confidence"]
            })
            
            if validation["is_valid"]:
                # Document is valid legal document
                saved_paths.append(file_path)
                print(f"✓ Valid legal document: {file.filename}")
            else:
                # Not a legal document - delete the file
                os.remove(file_path)
                non_legal_files.append(file.filename)
                failed_files.append(f"{file.filename} (not a legal document: {validation['document_type']})")
                print(f"✗ Rejected: {file.filename} - {validation['reason']}")
        
        except Exception as e:
            failed_files.append(f"{file.filename} (error: {str(e)})")
            print(f"✗ Failed to process: {file.filename}")
            # Clean up if file was saved
            file_path = os.path.join(storage_path, file.filename)
            if os.path.exists(file_path):
                os.remove(file_path)
    
    # Step 3: Ingest validated legal documents
    if saved_paths:
        print(f"\n⏳ Ingesting {len(saved_paths)} legal PDF(s)...")
        
        # Use session-specific pipeline if available
        if session_id and session_pipeline:
            results = session_pipeline.ingest_multiple_pdfs_to_session(
                saved_paths, 
                session["index_path"]
            )
            # Reload vector store in session chatbot
            session_chatbot.initialize_vector_store_from_path(session["index_path"])
            # Track documents in session
            processed_filenames = [os.path.basename(path) for path in saved_paths if os.path.basename(path) not in results['failed_files']]
            session["documents"].extend(processed_filenames)
        else:
            # Global ingestion (backwards compatibility)
            results = ingestion_pipeline.ingest_multiple_pdfs(saved_paths)
            chatbot.initialize_vector_store()
            processed_filenames = [os.path.basename(path) for path in saved_paths if os.path.basename(path) not in results['failed_files']]
        
        # Build appropriate message
        if non_legal_files:
            message = f"Processed {results['success']} legal document(s). Rejected {len(non_legal_files)} non-legal document(s)."
        else:
            message = f"Successfully processed {results['success']} legal document(s)"
        
        return UploadResponse(
            message=message,
            files_processed=results['success'],
            files_failed=results['failed'] + len(failed_files),
            failed_files=results['failed_files'] + failed_files,
            processed_files=processed_filenames,
            validation_results=validation_results
        )
    
    else:
        # No valid legal documents
        if non_legal_files:
            # All files were non-legal documents
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "No legal documents found. Please upload legal documents only.",
                    "rejected_files": non_legal_files,
                    "validation_results": validation_results,
                    "hint": "Legal documents include: contracts, court judgments, legal notices, agreements, MOUs, terms and conditions, etc."
                }
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"No valid PDF files uploaded. Errors: {failed_files}"
            )


@app.post("/chat", response_model=ChatResponse)
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
        request: ChatRequest with question, session_id, optional top_k, and optional document_filter
    
    Returns:
        ChatResponse with answer, risk classification, citations, sources, and documents_used
    
    Example:
        curl -X POST "http://localhost:8000/chat" \\
             -H "Content-Type: application/json" \\
             -d '{"question": "Summarize this document", "session_id": "session-123", "document_filter": ["contract.pdf"]}'
    """
    # Determine which chatbot to use based on session
    active_chatbot = chatbot
    
    if request.session_id:
        session = session_manager.get_session(request.session_id)
        if session:
            active_chatbot = session["chatbot"]
            print(f"💬 Using session: {request.session_id}")
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Session '{request.session_id}' not found. Please upload documents first."
            )
    
    # Validate vector store is initialized
    if active_chatbot.vector_store is None:
        if request.session_id:
            raise HTTPException(
                status_code=400,
                detail="No documents in this session. Please upload PDFs first."
            )
        if not active_chatbot.initialize_vector_store():
            raise HTTPException(
                status_code=400,
                detail="No documents uploaded yet. Please upload PDFs first using /upload-pdf"
            )
    
    # Validate question
    if not request.question or len(request.question.strip()) == 0:
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    try:
        # Execute RAG pipeline with optional document filter
        result = active_chatbot.answer_question(
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


@app.post("/reset")
async def reset_session():
    """
    Reset the session by clearing all uploaded documents and vector store.
    
    This endpoint should be called when:
    - User starts a new session
    - User wants to clear all previous documents
    - Page is reloaded/reopened
    
    Process:
    1. Clear FAISS vector store from memory
    2. Delete FAISS index files from disk
    3. Delete all uploaded PDF files
    4. Reset chatbot and ingestion pipeline state
    
    Returns:
        Success message with reset status
    """
    global chatbot, ingestion_pipeline
    
    settings = get_settings()
    deleted_files = []
    errors = []
    
    try:
        # Step 1: Clear vector store from chatbot
        if chatbot is not None:
            chatbot.vector_store = None
            print("✓ Cleared vector store from memory")
        
        # Step 2: Delete FAISS index files from disk
        faiss_path = os.path.join(settings.faiss_index_path, "legal_docs")
        if os.path.exists(faiss_path):
            shutil.rmtree(faiss_path)
            print(f"✓ Deleted FAISS index: {faiss_path}")
        
        # Step 3: Delete all uploaded PDF files
        pdf_dir = settings.pdf_storage_path
        if os.path.exists(pdf_dir):
            for filename in os.listdir(pdf_dir):
                if filename.endswith('.pdf'):
                    file_path = os.path.join(pdf_dir, filename)
                    try:
                        os.remove(file_path)
                        deleted_files.append(filename)
                        print(f"✓ Deleted PDF: {filename}")
                    except Exception as e:
                        errors.append(f"Failed to delete {filename}: {str(e)}")
        
        # Step 4: Reset ingestion pipeline vector store
        if ingestion_pipeline is not None:
            ingestion_pipeline.vector_store = None
        
        return {
            "status": "success",
            "message": "Session reset successfully. All documents cleared.",
            "deleted_files": deleted_files,
            "errors": errors if errors else None
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error resetting session: {str(e)}"
        )


# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Auto-reload on code changes (development only)
    )
