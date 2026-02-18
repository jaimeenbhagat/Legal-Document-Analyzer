/**
 * API Client for Legal Document Analysis Backend
 * 
 * All API calls go through Next.js rewrites (/api/*) which proxy to FastAPI.
 * This eliminates CORS issues and provides a single entry point.
 * 
 * Route mapping (handled by next.config.ts rewrites):
 *   /api/health      → FastAPI /health
 *   /api/chat        → FastAPI /chat
 *   /api/upload-pdf  → FastAPI /upload-pdf
 *   /api/documents   → FastAPI /documents
 */

// Use relative /api paths - Next.js rewrites handle proxying to backend
const API_BASE = '/api';

export interface Citation {
  page: number | string;
  source: string;
  excerpt: string;
}

export interface DocumentInfo {
  filename: string;
  page_count: number;
  chunk_count: number;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
  citations?: Citation[];
  risk_level?: string;
  risk_reason?: string;
  disclaimer?: string;
  documents_used?: string[];
  isDocumentPicker?: boolean;  // Special flag for document picker UI
  selectedDocument?: string;   // Which document was selected for this query
}

export interface Source {
  source: string;
  page: number | string;
  preview: string;
}

export interface ChatResponse {
  answer: string;
  risk_level: string;
  risk_reason: string;
  citations: Citation[];
  sources: Source[];
  chunk_count: number;
  disclaimer?: string;
  documents_used?: string[];
}

export interface ValidationResult {
  filename: string;
  is_valid: boolean;
  document_type: string;
  reason: string;
  confidence: string;
}

export interface UploadResponse {
  message: string;
  files_processed: number;
  files_failed: number;
  failed_files: string[];
  processed_files?: string[];
  validation_results?: ValidationResult[];
}

export interface ValidationErrorDetail {
  message: string;
  rejected_files: string[];
  validation_results: ValidationResult[];
  hint: string;
}

export interface HealthResponse {
  status: string;
  vector_store: string;
  message: string;
  available_documents?: string[];
}

export interface DocumentsListResponse {
  documents: DocumentInfo[];
  total_count: number;
}

/**
 * Check backend health status
 * @param sessionId - Optional session ID to check session-specific health
 */
export async function checkHealth(sessionId?: string): Promise<HealthResponse> {
  const url = sessionId 
    ? `${API_BASE}/health?session_id=${encodeURIComponent(sessionId)}`
    : `${API_BASE}/health`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error('Backend health check failed');
  }
  return response.json();
}

/**
 * Upload PDF files to the backend
 * Validates that documents are legal documents before processing
 * @param files - Array of PDF files to upload
 * @param sessionId - Optional session ID for isolated document context
 */
export async function uploadPDFs(files: File[], sessionId?: string): Promise<UploadResponse> {
  const formData = new FormData();
  
  files.forEach(file => {
    formData.append('files', file);
  });
  
  // Add session_id if provided
  if (sessionId) {
    formData.append('session_id', sessionId);
  }

  const response = await fetch(`${API_BASE}/upload-pdf`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    
    // Handle validation error (422 - non-legal document)
    if (response.status === 422 && error.detail) {
      const validationError = error.detail as ValidationErrorDetail;
      const errorMessage = `${validationError.message}\n\n${validationError.hint}`;
      throw new Error(errorMessage);
    }
    
    throw new Error(error.detail || 'Upload failed');
  }

  return response.json();
}

/**
 * Send a chat message and get AI response
 * @param question - The question to ask
 * @param topK - Number of chunks to retrieve
 * @param documentFilter - Optional array of document filenames to filter by
 * @param sessionId - Optional session ID for isolated document context
 */
export async function sendChatMessage(
  question: string,
  topK?: number,
  documentFilter?: string[],
  sessionId?: string
): Promise<ChatResponse> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 115000); // 115s timeout

  try {
    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question,
        top_k: topK || 4,
        document_filter: documentFilter || null,
        session_id: sessionId || null,
      }),
      signal: controller.signal,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Chat request failed');
    }

    return response.json();
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * Get list of all uploaded documents with metadata
 * @param sessionId - Optional session ID to get session-specific documents
 */
export async function getDocuments(sessionId?: string): Promise<DocumentsListResponse> {
  const url = sessionId 
    ? `${API_BASE}/documents?session_id=${encodeURIComponent(sessionId)}`
    : `${API_BASE}/documents`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error('Failed to fetch documents');
  }
  return response.json();
}

/**
 * Run pre-defined analysis on documents
 */
export async function runAnalysis(
  analysisType: 'obligations' | 'termination' | 'penalties' | 'risks' | 'parties' | 'duration'
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/analyze/${analysisType}`, {
    method: 'POST',
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Analysis failed');
  }

  return response.json();
}

export interface ResetResponse {
  status: string;
  message: string;
  deleted_files: string[];
  errors: string[] | null;
}

/**
 * Reset the session by clearing all uploaded documents and vector store.
 * Call this when starting a new session or when page reloads.
 */
export async function resetSession(): Promise<ResetResponse> {
  const response = await fetch(`${API_BASE}/reset`, {
    method: 'POST',
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Reset failed');
  }

  return response.json();
}
