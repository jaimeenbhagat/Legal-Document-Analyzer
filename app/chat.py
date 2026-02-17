"""
Chat & Retrieval Module
Handles user queries through RAG pipeline:
1. Retrieve relevant chunks from FAISS
2. Format context with metadata
3. Generate response using Gemini LLM
4. Parse structured JSON with citations and risk classification
"""

import json
import re
from typing import List, Dict, Optional, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.documents import Document

from app.config import get_settings
from app.ingest import DocumentIngestionPipeline
from app.prompts import (
    create_rag_prompt,
    format_context_with_metadata
)


class LegalDocumentChatbot:
    """
    Main RAG chatbot for legal document analysis.
    Combines retrieval (FAISS) with generation (Gemini).
    """
    
    def __init__(self):
        self.settings = get_settings()
        
        # Initialize LLM (Gemini)
        # Temperature kept low (0.1) to reduce creativity/hallucination
        # Using gemini-2.0-flash (latest stable model)
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=self.settings.google_api_key,
            temperature=self.settings.temperature,
            convert_system_message_to_human=True  # Gemini compatibility
        )
        
        # Initialize ingestion pipeline (for vector store access)
        self.ingestion_pipeline = DocumentIngestionPipeline()
        self.vector_store = None
    
    
    def initialize_vector_store(self) -> bool:
        """
        Load the FAISS vector store into memory.
        Must be called before querying.
        
        Returns:
            True if vector store loaded successfully, False otherwise
        """
        try:
            self.vector_store = self.ingestion_pipeline.get_vector_store()
            
            if self.vector_store is None:
                print("⚠ No vector store found. Please upload documents first.")
                return False
            
            print("✓ Vector store initialized")
            return True
        
        except Exception as e:
            print(f"✗ Error initializing vector store: {str(e)}")
            return False
    
    
    def initialize_vector_store_from_path(self, index_path: str) -> bool:
        """
        Load FAISS vector store from a specific path (for session isolation).
        
        Args:
            index_path: Path to the session's FAISS index
        
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            self.vector_store = self.ingestion_pipeline.load_vector_store_from_path(index_path)
            
            if self.vector_store is None:
                print(f"⚠ No vector store found at {index_path}")
                return False
            
            print(f"✓ Vector store initialized from {index_path}")
            return True
        
        except Exception as e:
            print(f"✗ Error initializing vector store from path: {str(e)}")
            return False
    
    
    def retrieve_relevant_chunks(self, query: str, k: int = None, document_filter: Optional[List[str]] = None) -> List[Document]:
        """
        Retrieve top-k most relevant document chunks for a query.
        
        Process:
        1. Convert query to embedding (using same model as documents)
        2. Find k-nearest neighbors in FAISS index
        3. Optionally filter by specific document(s)
        4. Return corresponding document chunks with metadata
        
        Args:
            query: User's question
            k: Number of chunks to retrieve (defaults to config setting)
            document_filter: Optional list of document filenames to filter by
        
        Returns:
            List of Document objects ranked by similarity
        """
        if self.vector_store is None:
            if not self.initialize_vector_store():
                return []
        
        if k is None:
            k = self.settings.top_k_retrieval
        
        try:
            # If document filter is specified, retrieve more chunks and filter
            fetch_k = k * 3 if document_filter else k
            
            # FAISS similarity search
            # Returns documents sorted by cosine similarity
            relevant_docs = self.vector_store.similarity_search(
                query=query,
                k=fetch_k
            )
            
            # Filter by document if specified
            if document_filter:
                filtered_docs = [
                    doc for doc in relevant_docs 
                    if doc.metadata.get("source", "") in document_filter
                ]
                # Take top k from filtered results
                relevant_docs = filtered_docs[:k]
                print(f"✓ Retrieved {len(relevant_docs)} chunks from filtered documents: {document_filter}")
            else:
                relevant_docs = relevant_docs[:k]
                print(f"✓ Retrieved {len(relevant_docs)} relevant chunks")
            
            return relevant_docs
        
        except Exception as e:
            print(f"✗ Retrieval error: {str(e)}")
            return []
    
    
    def get_available_documents(self) -> List[str]:
        """
        Get list of unique document names in the vector store.
        
        Returns:
            List of document filenames
        """
        if self.vector_store is None:
            return []
        
        try:
            # Access the docstore directly instead of similarity search
            # This avoids embedding an empty query
            documents = set()
            if hasattr(self.vector_store, 'docstore') and self.vector_store.docstore:
                for doc_id in self.vector_store.docstore._dict.values():
                    source = doc_id.metadata.get("source", "")
                    if source:
                        documents.add(source)
            
            return sorted(list(documents))
        
        except Exception as e:
            print(f"✗ Error getting documents: {str(e)}")
            return []
    
    
    def get_documents_info(self) -> List[Dict[str, Any]]:
        """
        Get detailed information about all documents in the vector store.
        
        Returns:
            List of dicts with filename, page_count, and chunk_count
        """
        if self.vector_store is None:
            return []
        
        try:
            # Access the docstore directly instead of similarity search
            # This avoids embedding an empty query
            doc_info = {}
            if hasattr(self.vector_store, 'docstore') and self.vector_store.docstore:
                for doc in self.vector_store.docstore._dict.values():
                    source = doc.metadata.get("source", "Unknown")
                    page = doc.metadata.get("page", 0)
                    
                    if source not in doc_info:
                        doc_info[source] = {
                            "filename": source,
                            "pages": set(),
                            "chunk_count": 0
                        }
                    
                    doc_info[source]["pages"].add(page)
                    doc_info[source]["chunk_count"] += 1
            
            # Convert to list format
            result = []
            for filename, info in doc_info.items():
                result.append({
                    "filename": filename,
                    "page_count": len(info["pages"]),
                    "chunk_count": info["chunk_count"]
                })
            
            return sorted(result, key=lambda x: x["filename"])
        
        except Exception as e:
            print(f"✗ Error getting document info: {str(e)}")
            return []
    
    
    def generate_response(self, query: str, context_docs: List[Document]) -> Dict[str, Any]:
        """
        Generate answer using LLM with retrieved context.
        
        This is the "Generation" phase of RAG:
        - Takes user query + retrieved context
        - Constructs a structured prompt
        - Sends to Gemini for answer generation
        - Parses structured JSON response with citations and risk classification
        - Adds legal disclaimer
        
        Args:
            query: User's question
            context_docs: Retrieved document chunks from FAISS
        
        Returns:
            Dictionary containing:
            - answer: LLM-generated response
            - risk_level: Risk classification (High/Medium/Low)
            - risk_reason: Explanation for risk level
            - citations: List of citations with page numbers and excerpts
        """
        if not context_docs:
            return {
                "answer": (
                    "I couldn't find any relevant information in the uploaded documents "
                    "to answer your question. Please ensure documents are uploaded and "
                    "try rephrasing your question."
                ),
                "risk_level": "Low Risk",
                "risk_reason": "No documents available for analysis",
                "citations": []
            }
        
        try:
            # Step 1: Format context with metadata (source, page numbers)
            formatted_context = format_context_with_metadata(context_docs)
            
            # Step 2: Create RAG prompt with JSON instructions
            prompt = create_rag_prompt(query, formatted_context)
            
            # Step 3: Generate response using LLM
            print("⏳ Generating response with citations and risk analysis...")
            response = self.llm.invoke(prompt)
            
            # Extract text content (LangChain returns BaseMessage object)
            raw_response = response.content if hasattr(response, 'content') else str(response)
            
            # Step 4: Parse structured JSON response
            parsed_response = self._parse_structured_response(raw_response)
            
            print("✓ Response generated with citations")
            return parsed_response
        
        except Exception as e:
            print(f"✗ Generation error: {str(e)}")
            return {
                "answer": f"An error occurred while generating the response: {str(e)}",
                "risk_level": "Low Risk",
                "risk_reason": "Error during analysis",
                "citations": []
            }
    
    
    def _parse_structured_response(self, raw_response: str) -> Dict[str, Any]:
        """
        Parse and validate structured JSON response from LLM.
        
        Handles:
        - JSON extraction from markdown code blocks
        - Malformed JSON graceful fallback
        - Schema validation
        
        Args:
            raw_response: Raw text response from LLM
        
        Returns:
            Validated dictionary with answer, risk_level, risk_reason, citations
        """
        try:
            # Try to extract JSON from markdown code blocks if present
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON object directly
                json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = raw_response
            
            # Parse JSON
            parsed = json.loads(json_str)
            
            # Validate required fields
            answer = parsed.get("answer", "")
            risk_level = parsed.get("risk_level", "Low Risk")
            risk_reason = parsed.get("risk_reason", "No specific analysis available")
            citations = parsed.get("citations", [])
            
            # Validate risk level format
            valid_risk_levels = ["High Risk", "Medium Risk", "Low Risk"]
            if risk_level not in valid_risk_levels:
                risk_level = "Low Risk"
            
            # Validate citations structure
            validated_citations = []
            for citation in citations:
                if isinstance(citation, dict):
                    validated_citations.append({
                        "page": citation.get("page", "Unknown"),
                        "source": citation.get("source", "Unknown"),
                        "excerpt": citation.get("excerpt", "")[:300]  # Limit excerpt length
                    })
            
            return {
                "answer": answer,
                "risk_level": risk_level,
                "risk_reason": risk_reason,
                "citations": validated_citations
            }
        
        except json.JSONDecodeError as e:
            print(f"⚠ JSON parsing failed: {str(e)}")
            print(f"Raw response: {raw_response[:500]}...")
            
            # Fallback: return raw response with default structure
            return {
                "answer": raw_response,
                "risk_level": "Low Risk",
                "risk_reason": "Unable to perform structured analysis",
                "citations": []
            }
        
        except Exception as e:
            print(f"⚠ Response parsing error: {str(e)}")
            return {
                "answer": raw_response,
                "risk_level": "Low Risk",
                "risk_reason": "Error during parsing",
                "citations": []
            }
    
    
    def answer_question(self, query: str, k: int = None, document_filter: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Complete RAG pipeline: Retrieve + Generate.
        
        This is the main method called by the API endpoint.
        
        Args:
            query: User's natural language question
            k: Number of chunks to retrieve (optional)
            document_filter: Optional list of document filenames to filter by
        
        Returns:
            Dictionary containing:
            - answer: Generated response
            - risk_level: Risk classification
            - risk_reason: Explanation for risk level
            - citations: List of citations with page/source/excerpt
            - sources: List of source documents used (for backward compatibility)
            - chunk_count: Number of chunks retrieved
            - documents_used: List of unique documents used in the response
        """
        # Step 1: Retrieve relevant chunks with optional document filter
        relevant_docs = self.retrieve_relevant_chunks(query, k, document_filter)
        
        # Step 2: Generate response with structured output
        result = self.generate_response(query, relevant_docs)
        
        # Step 3: Extract source information for backward compatibility
        sources = []
        documents_used = set()
        for doc in relevant_docs:
            source = doc.metadata.get("source", "Unknown")
            documents_used.add(source)
            sources.append({
                "source": source,
                "page": doc.metadata.get("page", "Unknown"),
                "preview": doc.page_content[:200] + "..."  # First 200 chars
            })
        
        # Step 4: Combine all information
        return {
            "answer": result["answer"],
            "risk_level": result["risk_level"],
            "risk_reason": result["risk_reason"],
            "citations": result["citations"],
            "sources": sources,
            "chunk_count": len(relevant_docs),
            "disclaimer": result.get("disclaimer", ""),
            "documents_used": sorted(list(documents_used))
        }
    
    
    def analyze_document(self, analysis_type: str) -> Dict[str, Any]:
        """
        Perform pre-defined analysis using template queries.
        
        Useful for standardized legal document review:
        - obligations, termination, penalties, risks, etc.
        
        Args:
            analysis_type: Type of analysis (from prompts.QUERY_TEMPLATES)
        
        Returns:
            Analysis results dictionary with citations and risk classification
        """
        from app.prompts import get_template_query, QUERY_TEMPLATES
        
        template_query = get_template_query(analysis_type)
        
        if template_query is None:
            return {
                "error": f"Unknown analysis type: {analysis_type}",
                "available_types": list(QUERY_TEMPLATES.keys())
            }
        
        return self.answer_question(template_query)