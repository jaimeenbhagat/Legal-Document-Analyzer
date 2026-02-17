"""
PDF Ingestion & Vector Store Module
Handles PDF processing, chunking, embedding, and FAISS indexing.
This is the core of the RAG ingestion pipeline.
"""

import os
import pickle
from typing import List
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from backend.config import get_settings


class DocumentIngestionPipeline:
    """
    Manages the complete document ingestion workflow:
    1. Load PDFs
    2. Split into chunks
    3. Generate embeddings
    4. Store in FAISS vector database
    """
    
    def __init__(self):
        self.settings = get_settings()
        
        # Initialize Gemini embeddings model
        # This converts text into high-dimensional vectors for similarity search
        # Using gemini-embedding-001 (the current available model)
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=self.settings.google_api_key
        )
        
        # Text splitter configuration
        # RecursiveCharacterTextSplitter tries to split on natural boundaries
        # (paragraphs, sentences) rather than arbitrary character counts
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]  # Try these in order
        )
        
        self.vector_store = None
    
    
    def load_pdf(self, pdf_path: str) -> List[Document]:
        """
        Load a single PDF and extract text with page metadata.
        
        PyPDFLoader automatically:
        - Extracts text from each page
        - Preserves page numbers in metadata
        - Handles basic formatting
        
        Args:
            pdf_path: Absolute path to PDF file
        
        Returns:
            List of Document objects (one per page initially)
        """
        try:
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()
            
            # Add filename to metadata for better source tracking
            filename = Path(pdf_path).name
            for doc in documents:
                doc.metadata["source"] = filename
            
            print(f"✓ Loaded {len(documents)} pages from {filename}")
            return documents
        
        except Exception as e:
            print(f"✗ Error loading {pdf_path}: {str(e)}")
            return []
    
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into smaller chunks for better retrieval.
        
        Why chunking?
        - Legal documents can be very long
        - Embeddings work best on focused content (500-1500 chars)
        - Smaller chunks = more precise similarity matching
        - Overlap prevents information loss at boundaries
        
        Args:
            documents: Raw documents from PDF loader
        
        Returns:
            List of chunked Document objects with preserved metadata
        """
        chunks = self.text_splitter.split_documents(documents)
        print(f"✓ Created {len(chunks)} chunks from {len(documents)} pages")
        return chunks
    
    
    def create_vector_store(self, documents: List[Document]) -> FAISS:
        """
        Create FAISS vector store from document chunks.
        
        Process:
        1. Generate embeddings for each chunk using Gemini
        2. Build FAISS index for fast similarity search
        3. Store both embeddings and original text
        
        FAISS (Facebook AI Similarity Search):
        - Efficient nearest-neighbor search
        - Works in-memory (fast!)
        - Can handle millions of vectors
        
        Args:
            documents: Chunked documents
        
        Returns:
            FAISS vector store object
        """
        print(f"⏳ Generating embeddings for {len(documents)} chunks...")
        
        try:
            # This call sends all chunks to Gemini for embedding
            # May take time depending on document size
            vector_store = FAISS.from_documents(
                documents=documents,
                embedding=self.embeddings
            )
            
            print("✓ Vector store created successfully")
            return vector_store
        
        except Exception as e:
            print(f"✗ Error creating vector store: {str(e)}")
            raise
    
    
    def save_vector_store(self, vector_store: FAISS, index_name: str = "legal_docs"):
        """
        Persist FAISS index to disk for later retrieval.
        
        Why persist?
        - Avoid re-processing documents on every startup
        - Embeddings are expensive to generate
        - Enables incremental updates
        
        Args:
            vector_store: FAISS vector store to save
            index_name: Name for the saved index
        """
        try:
            index_path = os.path.join(
                self.settings.faiss_index_path,
                index_name
            )
            
            # FAISS provides built-in save method
            vector_store.save_local(index_path)
            print(f"✓ Vector store saved to {index_path}")
        
        except Exception as e:
            print(f"✗ Error saving vector store: {str(e)}")
            raise
    
    
    def load_vector_store(self, index_name: str = "legal_docs") -> FAISS:
        """
        Load a previously saved FAISS index from disk.
        
        Args:
            index_name: Name of the saved index
        
        Returns:
            FAISS vector store object or None if not found
        """
        try:
            index_path = os.path.join(
                self.settings.faiss_index_path,
                index_name
            )
            
            if not os.path.exists(index_path):
                print(f"⚠ No existing index found at {index_path}")
                return None
            
            # Load index with the same embeddings model
            vector_store = FAISS.load_local(
                index_path,
                self.embeddings,
                allow_dangerous_deserialization=True  # Pickle deserialization
            )
            
            print(f"✓ Vector store loaded from {index_path}")
            return vector_store
        
        except Exception as e:
            print(f"✗ Error loading vector store: {str(e)}")
            return None
    
    
    def ingest_pdf(self, pdf_path: str) -> bool:
        """
        Complete ingestion pipeline for a single PDF.
        
        Workflow:
        1. Load PDF
        2. Chunk text
        3. Generate embeddings
        4. Add to vector store (create if doesn't exist)
        5. Save to disk
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Step 1: Load PDF
            documents = self.load_pdf(pdf_path)
            if not documents:
                return False
            
            # Step 2: Chunk documents
            chunks = self.chunk_documents(documents)
            
            # Step 3: Load existing index or create new one
            self.vector_store = self.load_vector_store()
            
            if self.vector_store is None:
                # No existing index - create fresh
                self.vector_store = self.create_vector_store(chunks)
            else:
                # Add to existing index
                print("⏳ Adding new documents to existing index...")
                self.vector_store.add_documents(chunks)
                print("✓ Documents added to existing index")
            
            # Step 4: Save updated index
            self.save_vector_store(self.vector_store)
            
            return True
        
        except Exception as e:
            print(f"✗ Ingestion failed: {str(e)}")
            return False
    
    
    def ingest_multiple_pdfs(self, pdf_paths: List[str]) -> dict:
        """
        Ingest multiple PDFs in batch.
        
        Args:
            pdf_paths: List of PDF file paths
        
        Returns:
            Dictionary with success/failure counts
        """
        results = {"success": 0, "failed": 0, "failed_files": []}
        
        for pdf_path in pdf_paths:
            if self.ingest_pdf(pdf_path):
                results["success"] += 1
            else:
                results["failed"] += 1
                results["failed_files"].append(pdf_path)
        
        return results
    
    
    def ingest_multiple_pdfs_to_session(self, pdf_paths: List[str], session_index_path: str) -> dict:
        """
        Ingest multiple PDFs into a session-specific vector store.
        
        Args:
            pdf_paths: List of PDF file paths
            session_index_path: Path to store session's FAISS index
        
        Returns:
            Dictionary with success/failure counts
        """
        results = {"success": 0, "failed": 0, "failed_files": []}
        
        all_chunks = []
        
        for pdf_path in pdf_paths:
            try:
                # Step 1: Load PDF
                documents = self.load_pdf(pdf_path)
                if not documents:
                    results["failed"] += 1
                    results["failed_files"].append(pdf_path)
                    continue
                
                # Step 2: Chunk documents
                chunks = self.chunk_documents(documents)
                all_chunks.extend(chunks)
                results["success"] += 1
                
            except Exception as e:
                print(f"✗ Failed to process {pdf_path}: {str(e)}")
                results["failed"] += 1
                results["failed_files"].append(pdf_path)
        
        # Step 3: Create or update session vector store
        if all_chunks:
            try:
                session_index_name = os.path.basename(session_index_path)
                existing_store = self.load_vector_store_from_path(session_index_path)
                
                if existing_store is None:
                    # Create new vector store for session
                    self.vector_store = self.create_vector_store(all_chunks)
                else:
                    # Add to existing session store
                    self.vector_store = existing_store
                    print("⏳ Adding new documents to session index...")
                    self.vector_store.add_documents(all_chunks)
                    print("✓ Documents added to session index")
                
                # Save to session path
                self.save_vector_store_to_path(self.vector_store, session_index_path)
                
            except Exception as e:
                print(f"✗ Failed to create session vector store: {str(e)}")
        
        return results
    
    
    def load_vector_store_from_path(self, index_path: str) -> FAISS:
        """
        Load FAISS index from a specific path.
        
        Args:
            index_path: Full path to the index directory
        
        Returns:
            FAISS vector store or None
        """
        try:
            if not os.path.exists(index_path) or not os.listdir(index_path):
                print(f"⚠ No index found at {index_path}")
                return None
            
            vector_store = FAISS.load_local(
                index_path,
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            
            print(f"✓ Vector store loaded from {index_path}")
            return vector_store
        
        except Exception as e:
            print(f"✗ Error loading vector store from {index_path}: {str(e)}")
            return None
    
    
    def save_vector_store_to_path(self, vector_store: FAISS, index_path: str):
        """
        Save FAISS index to a specific path.
        
        Args:
            vector_store: FAISS vector store to save
            index_path: Full path to save the index
        """
        try:
            os.makedirs(index_path, exist_ok=True)
            vector_store.save_local(index_path)
            print(f"✓ Vector store saved to {index_path}")
        
        except Exception as e:
            print(f"✗ Error saving vector store to {index_path}: {str(e)}")
            raise
    
    
    def get_vector_store(self) -> FAISS:
        """
        Get the current vector store instance.
        Loads from disk if not already in memory.
        
        Returns:
            FAISS vector store or None
        """
        if self.vector_store is None:
            self.vector_store = self.load_vector_store()
        
        return self.vector_store
