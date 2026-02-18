"""
Document Validation Module
Validates if uploaded documents are legal documents before processing.
Uses AI to analyze document content and determine document type.
"""

import json
import re
from typing import Dict, Tuple, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.document_loaders import PyPDFLoader
from pathlib import Path

from app.config import get_settings


# Legal document indicators - keywords and patterns commonly found in legal documents
LEGAL_KEYWORDS = [
    # Court and legal proceedings
    "plaintiff", "defendant", "petitioner", "respondent", "appellant", "appellee",
    "court", "tribunal", "bench", "judge", "justice", "magistrate", "arbitrator",
    "verdict", "judgment", "order", "decree", "ruling", "injunction", "stay",
    "hearing", "trial", "proceedings", "litigation", "arbitration", "mediation",
    
    # Legal actions and terms
    "hereby", "whereas", "therefore", "hereinafter", "aforementioned", "herein",
    "pursuant to", "in accordance with", "subject to", "notwithstanding",
    "indemnify", "indemnification", "liability", "damages", "compensation",
    "breach", "violation", "default", "remedy", "relief", "restitution",
    
    # Contract terms
    "agreement", "contract", "covenant", "undertaking", "warranty", "guarantee",
    "terms and conditions", "obligations", "rights", "duties", "responsibilities",
    "termination", "amendment", "modification", "waiver", "severability",
    "force majeure", "confidentiality", "non-disclosure", "non-compete",
    
    # Parties and entities
    "party", "parties", "signatory", "witness", "notary", "affidavit",
    "power of attorney", "legal representative", "authorized signatory",
    
    # Legal references
    "section", "clause", "article", "schedule", "annexure", "exhibit",
    "statute", "act", "regulation", "ordinance", "by-law", "code",
    "case no", "case number", "suit no", "writ petition", "civil suit",
    
    # Legal document types
    "memorandum of understanding", "mou", "letter of intent", "loi",
    "deed", "lease", "license", "mortgage", "conveyance", "assignment",
    "will", "testament", "trust", "estate", "probate", "succession",
    
    # Court documents
    "summons", "notice", "complaint", "plaint", "written statement",
    "rejoinder", "sur-rejoinder", "evidence", "exhibit", "deposition",
    "affirmation", "sworn statement", "testimony",
    
    # Legal phrases
    "in the matter of", "in re", "ex parte", "prima facie", "inter alia",
    "mutatis mutandis", "ipso facto", "res judicata", "stare decisis"
]


VALIDATION_PROMPT = """You are a document classification expert. Analyze the following document excerpt and determine if it is a LEGAL DOCUMENT.

Legal documents include:
- Court judgments, orders, and rulings
- Contracts and agreements (employment, business, lease, etc.)
- Legal notices and summons
- Affidavits and declarations
- Memorandums of Understanding (MOUs)
- Terms and conditions / Privacy policies
- Legal opinions and briefs
- Deeds and conveyances
- Wills and trusts
- Regulatory filings and compliance documents
- Arbitration/mediation documents
- Corporate legal documents (bylaws, resolutions)

Non-legal documents include:
- Research papers and academic articles
- News articles and blog posts
- Marketing materials and brochures
- Technical documentation and manuals
- Personal letters and correspondence
- Financial reports (unless legal filings)
- Scientific studies
- Educational materials
- Fiction and literature

Document excerpt to analyze:
---
{document_text}
---

Respond with a JSON object ONLY (no markdown, no explanation):
{{
    "is_legal_document": true/false,
    "document_type": "Brief description of what type of document this is",
    "confidence": "HIGH/MEDIUM/LOW",
    "reason": "One sentence explanation of why this is or is not a legal document"
}}
"""


class DocumentValidator:
    """
    Validates if uploaded documents are legal documents.
    Uses both keyword analysis and AI-based classification.
    """
    
    def __init__(self):
        self.settings = get_settings()
        
        # Initialize LLM for document classification
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=self.settings.google_api_key,
            temperature=0.1,  # Low temperature for consistent classification
            convert_system_message_to_human=True
        )
    
    def extract_text_preview(self, pdf_path: str, max_pages: int = 3, max_chars: int = 3000) -> str:
        """
        Extract text from first few pages of PDF for validation.
        
        Args:
            pdf_path: Path to the PDF file
            max_pages: Maximum number of pages to read
            max_chars: Maximum characters to extract
        
        Returns:
            Extracted text preview
        """
        try:
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()
            
            # Combine text from first few pages
            text_preview = ""
            for i, doc in enumerate(documents[:max_pages]):
                text_preview += doc.page_content + "\n\n"
                if len(text_preview) >= max_chars:
                    break
            
            return text_preview[:max_chars]
        
        except Exception as e:
            print(f"✗ Error extracting text preview: {str(e)}")
            return ""
    
    def keyword_analysis(self, text: str) -> Tuple[int, List[str]]:
        """
        Count legal keywords in the document text.
        
        Args:
            text: Document text to analyze
        
        Returns:
            Tuple of (keyword_count, list_of_found_keywords)
        """
        text_lower = text.lower()
        found_keywords = []
        
        for keyword in LEGAL_KEYWORDS:
            if keyword.lower() in text_lower:
                found_keywords.append(keyword)
        
        return len(found_keywords), found_keywords
    
    def ai_classification(self, text: str) -> Dict:
        """
        Use AI to classify if document is legal.
        
        Args:
            text: Document text to analyze
        
        Returns:
            Classification result dict
        """
        try:
            prompt = VALIDATION_PROMPT.format(document_text=text)
            response = self.llm.invoke(prompt)
            
            # Parse JSON response
            response_text = response.content.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = re.sub(r'^```(?:json)?\n?', '', response_text)
                response_text = re.sub(r'\n?```$', '', response_text)
            
            result = json.loads(response_text)
            return result
        
        except json.JSONDecodeError as e:
            print(f"✗ Error parsing AI response: {str(e)}")
            return {
                "is_legal_document": None,
                "document_type": "Unknown",
                "confidence": "LOW",
                "reason": "Could not parse AI response"
            }
        except Exception as e:
            print(f"✗ Error in AI classification: {str(e)}")
            return {
                "is_legal_document": None,
                "document_type": "Unknown",
                "confidence": "LOW",
                "reason": str(e)
            }
    
    def validate_document(self, pdf_path: str) -> Dict:
        """
        Validate if a PDF is a legal document.
        
        Uses a combination of:
        1. Keyword analysis (fast, rule-based)
        2. AI classification (accurate, context-aware)
        
        Args:
            pdf_path: Path to the PDF file
        
        Returns:
            Validation result dict with:
            - is_valid: bool - whether document is legal
            - document_type: str - type of document detected
            - confidence: str - HIGH/MEDIUM/LOW
            - reason: str - explanation
            - keyword_count: int - number of legal keywords found
        """
        print(f"🔍 Validating document: {Path(pdf_path).name}")
        
        # Extract text preview
        text_preview = self.extract_text_preview(pdf_path)
        
        if not text_preview or len(text_preview.strip()) < 100:
            return {
                "is_valid": False,
                "document_type": "Empty or unreadable document",
                "confidence": "HIGH",
                "reason": "The document appears to be empty or could not be read.",
                "keyword_count": 0
            }
        
        # Step 1: Keyword analysis
        keyword_count, found_keywords = self.keyword_analysis(text_preview)
        print(f"   📋 Found {keyword_count} legal keywords")
        
        # Step 2: AI classification
        ai_result = self.ai_classification(text_preview)
        print(f"   🤖 AI classification: {ai_result.get('document_type', 'Unknown')}")
        
        # Combine results
        is_legal = ai_result.get("is_legal_document", False)
        
        # If AI is uncertain but we have many legal keywords, lean towards legal
        if is_legal is None and keyword_count >= 10:
            is_legal = True
            ai_result["confidence"] = "MEDIUM"
            ai_result["reason"] = f"Contains {keyword_count} legal terms/keywords"
        
        # If AI says legal but no keywords, reduce confidence
        if is_legal and keyword_count < 3:
            ai_result["confidence"] = "MEDIUM"
        
        result = {
            "is_valid": bool(is_legal),
            "document_type": ai_result.get("document_type", "Unknown"),
            "confidence": ai_result.get("confidence", "LOW"),
            "reason": ai_result.get("reason", "Unknown"),
            "keyword_count": keyword_count,
            "keywords_found": found_keywords[:10]  # Top 10 keywords
        }
        
        status = "✓ Valid legal document" if result["is_valid"] else "✗ Not a legal document"
        print(f"   {status}: {result['document_type']}")
        
        return result


# Singleton instance
_validator_instance = None

def get_document_validator() -> DocumentValidator:
    """Get or create the document validator singleton."""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = DocumentValidator()
    return _validator_instance
