"""
Prompt Engineering Module
Contains all prompt templates for the Legal RAG system.
Includes citation-grounded responses and legal risk classification.
"""

from typing import List
from langchain_core.documents import Document


# =============================================================================
# LEGAL DISCLAIMER
# =============================================================================

LEGAL_DISCLAIMER = """

---
⚠️ **DISCLAIMER**: This analysis is AI-generated for informational purposes only and does NOT constitute legal advice. 
Consult with a qualified attorney for legal guidance specific to your situation.
"""


# =============================================================================
# ADVANCED RAG PROMPT WITH CITATION + RISK CLASSIFICATION
# =============================================================================

RAG_SYSTEM_PROMPT = """You are an expert legal document analysis assistant with deep expertise in contract law, compliance, and risk assessment.

Your task is to answer questions about legal documents using ONLY the provided context. You must:

1. **STRICT GROUNDING**: Answer ONLY from the retrieved context. Never use external knowledge.
2. **CITATIONS**: Cite every piece of information with exact page numbers and source filenames in this format:
   (Source: filename.pdf, Page X)
3. **EXACT QUOTES**: When possible, quote exact text from the document using quotation marks.
4. **RISK CLASSIFICATION**: Analyze the legal clauses mentioned and classify risk level as:
   - **High Risk**: Unilateral termination rights, heavy penalties, unlimited liability, ambiguous financial obligations
   - **Medium Risk**: Conditional obligations, moderate penalties, shared responsibilities
   - **Low Risk**: Procedural clauses, neutral definitions, administrative provisions

5. **RESPONSE FORMAT**: You MUST respond ONLY with valid JSON in this exact structure:
```json
{
  "answer": "Your detailed answer here with inline citations like (Source: contract.pdf, Page 5)",
  "risk_level": "High Risk" | "Medium Risk" | "Low Risk",
  "risk_reason": "Brief explanation of why this risk level was assigned",
  "citations": [
    {
      "page": 5,
      "source": "contract.pdf",
      "excerpt": "Exact quoted text from the document that supports your answer"
    }
  ]
}
```

**CRITICAL RULES**:
- If information is NOT in the context, set answer to: "Not found in the provided document."
- If no risk assessment is applicable (e.g., general questions), set risk_level to "Low Risk" and risk_reason to "No specific legal clauses analyzed"
- Extract at least 1-3 citations for each substantive answer
- Keep excerpts under 200 characters but ensure they're meaningful
- DO NOT add any text before or after the JSON object
- DO NOT use markdown code blocks around the JSON
- Ensure all JSON fields are present and properly formatted
"""


def create_rag_prompt(query: str, context: str) -> str:
    """
    Create a structured RAG prompt with context and query.
    
    This prompt enforces:
    - Strict grounding (no hallucination)
    - Citation with page numbers
    - Risk classification
    - Structured JSON output
    
    Args:
        query: User's natural language question
        context: Retrieved document chunks with metadata
    
    Returns:
        Complete prompt string for the LLM
    """
    prompt = f"""{RAG_SYSTEM_PROMPT}

---
**RETRIEVED CONTEXT FROM DOCUMENTS**:
{context}

---
**USER QUESTION**: {query}

---
**YOUR JSON RESPONSE** (no other text, just the JSON):"""
    
    return prompt


# =============================================================================
# CONTEXT FORMATTING WITH METADATA
# =============================================================================

def format_context_with_metadata(documents: List[Document]) -> str:
    """
    Format retrieved documents with clear source and page metadata.
    
    This ensures the LLM can properly cite sources in its response.
    
    Args:
        documents: List of retrieved Document objects from FAISS
    
    Returns:
        Formatted context string with metadata headers
    """
    if not documents:
        return "No relevant documents found."
    
    formatted_chunks = []
    
    for idx, doc in enumerate(documents, 1):
        source = doc.metadata.get("source", "Unknown")
        # PyPDFLoader uses 0-based page indexing, convert to 1-based for human-readable citations
        raw_page = doc.metadata.get("page", 0)
        page = raw_page + 1 if isinstance(raw_page, int) else raw_page
        content = doc.page_content.strip()
        
        chunk = f"""[CHUNK {idx}]
Source: {source}
Page: {page}
Content: {content}
"""
        formatted_chunks.append(chunk)
    
    return "\n".join(formatted_chunks)


# =============================================================================
# TEMPLATE QUERIES FOR ANALYSIS
# =============================================================================

QUERY_TEMPLATES = {
    "obligations": "What are the key obligations and responsibilities of each party in this agreement? List them clearly with citations.",
    
    "termination": "What are the termination clauses in this agreement? Include conditions, notice periods, and consequences. Assess the risk level.",
    
    "penalties": "What penalties, damages, or financial consequences are mentioned in this agreement? Include specific amounts or calculation methods.",
    
    "risks": "What are the main legal risks and liabilities in this agreement? Focus on clauses that could expose parties to significant obligations or losses.",
    
    "parties": "Who are the parties involved in this agreement? Include their roles, definitions, and any relevant identifying information.",
    
    "duration": "What is the duration or term of this agreement? Include start date, end date, renewal terms, and any automatic extension clauses.",
    
    "payment": "What are the payment terms and financial obligations in this agreement? Include amounts, schedules, and payment conditions.",
    
    "confidentiality": "What confidentiality or non-disclosure provisions are in this agreement? Include scope, duration, and exceptions.",
    
    "jurisdiction": "What governing law and jurisdiction clauses are in this agreement? Include dispute resolution mechanisms.",
    
    "definitions": "What are the key defined terms in this agreement? Provide the definitions as stated in the document."
}


def get_template_query(analysis_type: str) -> str:
    """
    Get a pre-defined template query for document analysis.
    
    Args:
        analysis_type: Type of analysis (e.g., 'obligations', 'termination')
    
    Returns:
        Template query string, or None if type not found
    """
    return QUERY_TEMPLATES.get(analysis_type.lower())
