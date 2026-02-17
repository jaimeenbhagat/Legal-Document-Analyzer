"""
Sample Test Script
Demonstrates basic usage of the Legal Document Analysis System.

Run this after starting the server with: python -m app.main
"""

import requests
import json
from pathlib import Path


# API Configuration
BASE_URL = "http://localhost:8000"
UPLOAD_ENDPOINT = f"{BASE_URL}/upload-pdf"
CHAT_ENDPOINT = f"{BASE_URL}/chat"
HEALTH_ENDPOINT = f"{BASE_URL}/health"


def check_health():
    """Check if server is running"""
    print("🔍 Checking server health...")
    try:
        response = requests.get(HEALTH_ENDPOINT)
        if response.status_code == 200:
            print("✅ Server is healthy!")
            print(json.dumps(response.json(), indent=2))
            return True
        else:
            print(f"❌ Server returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Is it running?")
        print("   Start with: python -m app.main")
        return False


def upload_pdf(pdf_path):
    """Upload a PDF file"""
    print(f"\n📤 Uploading {pdf_path}...")
    
    if not Path(pdf_path).exists():
        print(f"❌ File not found: {pdf_path}")
        return False
    
    try:
        with open(pdf_path, 'rb') as f:
            files = {'files': f}
            response = requests.post(UPLOAD_ENDPOINT, files=files)
        
        if response.status_code == 200:
            print("✅ Upload successful!")
            print(json.dumps(response.json(), indent=2))
            return True
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(response.text)
            return False
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def ask_question(question, top_k=4):
    """Ask a question about uploaded documents"""
    print(f"\n💬 Asking: '{question}'")
    
    try:
        payload = {
            "question": question,
            "top_k": top_k
        }
        response = requests.post(
            CHAT_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("\n" + "="*70)
            print("📝 ANSWER:")
            print("="*70)
            print(result["answer"])
            print("\n" + "="*70)
            print(f"📚 SOURCES ({result['chunk_count']} chunks used):")
            print("="*70)
            for i, source in enumerate(result["sources"], 1):
                print(f"\n[Source {i}]")
                print(f"  File: {source['source']}")
                print(f"  Page: {source['page']}")
                print(f"  Preview: {source['preview'][:150]}...")
            return True
        else:
            print(f"❌ Query failed: {response.status_code}")
            print(response.text)
            return False
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def main():
    """Main test workflow"""
    print("="*70)
    print("🏛️  LEGAL DOCUMENT ANALYSIS SYSTEM - TEST SCRIPT")
    print("="*70)
    
    # Step 1: Check server health
    if not check_health():
        return
    
    # Step 2: Upload PDF (you'll need to provide a PDF path)
    print("\n" + "="*70)
    print("STEP 1: UPLOAD PDF")
    print("="*70)
    
    pdf_path = input("\nEnter path to a PDF file (or press Enter to skip upload): ").strip()
    
    if pdf_path:
        upload_pdf(pdf_path)
    else:
        print("⏭️  Skipping upload (assuming documents already uploaded)")
    
    # Step 3: Ask sample questions
    print("\n" + "="*70)
    print("STEP 2: ASK QUESTIONS")
    print("="*70)
    
    sample_questions = [
        "Summarize the main points of this document",
        "What are the termination clauses?",
        "Who are the parties involved?",
    ]
    
    print("\nWould you like to:")
    print("1. Use sample questions")
    print("2. Enter your own question")
    choice = input("\nChoice (1 or 2): ").strip()
    
    if choice == "1":
        for question in sample_questions:
            ask_question(question)
            input("\nPress Enter to continue to next question...")
    else:
        while True:
            question = input("\n💭 Your question (or 'quit' to exit): ").strip()
            if question.lower() in ['quit', 'exit', 'q']:
                break
            if question:
                ask_question(question)
    
    print("\n" + "="*70)
    print("✅ Test completed!")
    print("="*70)


if __name__ == "__main__":
    main()
