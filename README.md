<div align="center">

# ⚖️ Legal AI — Document Analysis System

### AI-powered legal document analysis using Retrieval-Augmented Generation (RAG)

[![Live Demo](https://img.shields.io/badge/🌐_Live_Demo-legal--document--analyzer-7c3aed?style=for-the-badge)](https://legal-document-analyzer-65ex.onrender.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-16-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Google Gemini](https://img.shields.io/badge/Google_Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://deepmind.google/technologies/gemini/)

**[🚀 Try it Live](https://legal-document-analyzer-65ex.onrender.com)** &nbsp;|&nbsp; **[📖 Quick Start](#-quick-start)** &nbsp;|&nbsp; **[🐳 Docker](#-docker-deployment)**

> ⚠️ **DISCLAIMER**: This tool is for document analysis only and does **not** constitute legal advice. Always consult a qualified attorney for legal guidance.

</div>

---

## 📸 Overview

A production-ready **RAG (Retrieval-Augmented Generation)** system that lets you upload legal PDFs and have intelligent, context-grounded conversations about them. The AI only answers from the content of your documents — no hallucination, no fabrication.

**Upload a court judgment, contract, or legal notice → Ask any question → Get cited, accurate answers in seconds.**

---

## ✨ Features

### 🤖 AI & RAG Pipeline
- **Gemini 2.5 Flash** — Latest Google model for fast, accurate legal reasoning
- **Semantic Search** — FAISS vector store finds the most relevant document chunks
- **Gemini Embeddings** — `gemini-embedding-001` for high-quality text vectorization
- **Cited Answers** — Every response includes page-level citations from source documents
- **Risk Assessment** — Automatic HIGH / MEDIUM / LOW legal risk classification
- **Grounded Responses** — AI strictly answers from uploaded content, no hallucination

### � Document Intelligence
- **Legal Document Validator** — AI-powered classifier rejects non-legal files before processing
- **Keyword Analysis** — 100+ legal keyword patterns for fast pre-screening
- **Smart Chunking** — Overlap-aware text splitting preserves context across boundaries
- **Multi-Document Support** — Upload and query multiple PDFs simultaneously
- **Document Picker** — Filter queries to a specific document for precision analysis
- **Supported Types** — Court judgments, contracts, agreements, notices, MOUs, deeds, affidavits, and more

### � Chat Experience
- **Multi-Session Management** — Create unlimited parallel chat sessions
- **localStorage Persistence** — All sessions, messages, and documents survive page reloads
- **Auto Session Naming** — Sessions are automatically named from the uploaded document
- **Smart Scroll** — New AI responses always scroll to the **top** of the reply, not the bottom
- **Quick Action Prompts** — One-click buttons for Summarize, Key Clauses, Risks, Obligations
- **Empty Session Deduplication** — No accumulation of blank "New conversation" entries
- **Stale State Detection** — If the server restarts, the UI detects it and prompts re-upload

### 🎨 UI / UX
- **Premium Chat Interface** — Clean, ChatGPT-inspired conversational layout
- **Glass Morphism Design** — Frosted glass effects with purple/indigo gradient accents
- **Dark Sidebar** — Session list with document badges and timestamps
- **Drag & Drop Upload** — Drop PDFs anywhere on the chat area
- **Responsive Design** — Fully functional on desktop and mobile
- **Smooth Animations** — Polished micro-interactions throughout
- **No Hydration Errors** — Two-phase localStorage loading for SSR compatibility

### 🔧 Backend & Infrastructure
- **FastAPI** — Async Python API with automatic OpenAPI docs
- **Session Reset API** — `/api/reset` cleanly wipes vector store between sessions
- **Auto Re-index on Startup** — If FAISS index is lost (server restart), PDFs are automatically re-ingested
- **Docker Ready** — Single-container deployment with Dockerfile + docker-compose
- **Render Deployment** — Live on Render with CORS configured for any origin
- **120s Proxy Timeout** — Handles large documents and slow AI responses gracefully

---

## 🌐 Live Demo

**[https://legal-document-analyzer-65ex.onrender.com](https://legal-document-analyzer-65ex.onrender.com)**

> **Note:** The live demo runs on Render's free tier. The server may take **~30 seconds to wake up** on the first visit (cold start). Once running, it's fast.
>
> Because the free tier uses ephemeral storage, uploaded documents are lost when the server restarts. If you see a "server restarted" message, simply re-upload your PDF.

---

## 🛠️ Tech Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Frontend** | Next.js | 16.x | React framework with SSR |
| **Language** | TypeScript | 5.x | Type-safe frontend code |
| **Styling** | Tailwind CSS | 4.x | Utility-first styling |
| **Backend** | FastAPI | 0.115 | Async Python API |
| **Runtime** | Python | 3.11+ | Backend runtime |
| **RAG Framework** | LangChain | 0.3 | Document pipeline orchestration |
| **Vector DB** | FAISS | 1.9 | In-memory similarity search |
| **Embeddings** | Gemini Embedding 001 | — | Text vectorization |
| **LLM** | Gemini 2.5 Flash | — | Answer generation |
| **PDF Parsing** | PyPDF | 5.x | Text extraction from PDFs |
| **Containerization** | Docker | — | Single-container deployment |
| **Hosting** | Render | — | Cloud deployment platform |

---

## 📁 Project Structure

```
Legal-Document-Analyzer/
├── app/                          # Python Backend (FastAPI)
│   ├── main.py                  # All API endpoints + startup logic
│   ├── chat.py                  # RAG chatbot (retrieval + generation)
│   ├── ingest.py                # PDF loading, chunking, embedding, FAISS
│   ├── validator.py             # Legal document classifier (AI + keywords)
│   ├── prompts.py               # LLM prompt templates
│   └── config.py                # Settings from environment variables
│
├── frontend/                     # Next.js Frontend
│   ├── app/
│   │   ├── page.tsx             # Root page
│   │   ├── layout.tsx           # App shell
│   │   └── globals.css          # Global styles
│   ├── components/
│   │   └── PremiumChatInterface.tsx  # Entire UI — sessions, chat, upload
│   └── app/api.ts               # Typed API client (fetch wrappers)
│
├── data/                         # Runtime data (gitignored)
│   ├── pdfs/                    # Uploaded PDF files
│   └── faiss_index/             # FAISS vector index
│
├── Dockerfile                    # Single-container build
├── docker-compose.yml            # Local Docker orchestration
├── requirements.txt              # Python dependencies
└── .env                          # Environment variables (never commit)
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Google Gemini API Key** — Get one free at [Google AI Studio](https://aistudio.google.com/app/apikey)

### 1. Clone the Repository

```bash
git clone https://github.com/jaimeenbhagat/Legal-Document-Analyzer.git
cd Legal-Document-Analyzer
```

### 2. Set Up Python Environment

```bash
python -m venv venv
source venv/bin/activate          # macOS/Linux
# venv\Scripts\activate           # Windows

pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
cp .env.example .env              # or create .env manually
```

Edit `.env`:
```properties
GOOGLE_API_KEY=your_gemini_api_key_here
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_RETRIEVAL=4
PDF_STORAGE_PATH=./data/pdfs
FAISS_INDEX_PATH=./data/faiss_index
```

### 4. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

### 5. Run the App (One Command)

```bash
npm run dev          # from the project root — starts both backend and frontend
```

Or start them separately:

```bash
# Terminal 1 — Backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — Frontend
cd frontend && npm run dev
```

### 6. Open in Browser

**[http://localhost:3000](http://localhost:3000)**

Backend API docs: **[http://localhost:8000/docs](http://localhost:8000/docs)**

---

## 🎯 Usage Guide

### Uploading a Legal Document
1. Drag & drop a PDF onto the chat area, **or** click the paperclip icon
2. The validator checks if it's a legal document (rejects non-legal files automatically)
3. Wait ~10–30 seconds for embedding generation
4. You'll see a success message with quick-action prompts

### Asking Questions
- Type any natural language question: *"What are the termination clauses?"*
- Press **Enter** or click the send button
- The AI retrieves the most relevant chunks and generates a grounded answer with citations

### Quick Actions (one click)
| Button | Query sent |
|--------|-----------|
| 📋 Summarize | "Summarize this document" |
| ⚖️ Key clauses | "What are the key clauses?" |
| ⚠️ Risks | "Identify potential risks" |
| 💰 Obligations | "List all obligations" |

### Managing Sessions
- **New Chat** — Creates a fresh session (backend is reset, previous docs cleared)
- **Switch Session** — Click any session in the sidebar to restore its messages and documents
- **Delete Session** — Hover over a session and click the trash icon
- **Reload page** — All sessions and messages are restored from localStorage automatically

---

## 🔑 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check — returns vector store status and available documents |
| `POST` | `/upload-pdf` | Upload one or more PDFs — validates, embeds, and indexes |
| `POST` | `/chat` | Ask a question — returns answer with citations and risk level |
| `GET` | `/documents` | List all documents currently in the vector store |
| `POST` | `/reset` | Clear all uploaded documents and the vector store |
| `GET` | `/docs` | Interactive Swagger UI (local only) |

**Example chat request:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the termination clauses?", "document_filter": ["contract.pdf"]}'
```

---

## 🐳 Docker Deployment

### Build and run locally

```bash
docker-compose up --build
```

Open **[http://localhost:3000](http://localhost:3000)**

### Deploy to Render (one-click)

1. Push your code to GitHub
2. Create a new **Web Service** on [Render](https://render.com)
3. Connect your repository
4. Set **Build Command**: `docker build -t app .`
5. Add environment variable: `GOOGLE_API_KEY=your_key_here`
6. Deploy — Render builds the Docker image and serves both frontend and backend

> **Persistent Storage on Render:** The free tier uses ephemeral disk. For permanent document storage across restarts, add a Render Persistent Disk (~$1/month) mounted at `/data`.

---

## 🔒 Security

- API keys are stored in `.env` and **never committed** to git (`.gitignore` excludes `.env`)
- No user data is stored externally — documents live only on the server's local disk
- Data sent to Google: document text chunks (for embeddings) and questions (for LLM answers)
- CORS is configured to allow all origins in development; restrict `ALLOWED_ORIGINS` in production

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "Add my feature"`
4. Push and open a Pull Request

---

## 📝 License

This project is for **educational purposes**. See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- [LangChain](https://langchain.com/) — RAG orchestration framework
- [Google Gemini](https://deepmind.google/technologies/gemini/) — LLM and embeddings
- [FAISS](https://github.com/facebookresearch/faiss) — Facebook AI similarity search
- [FastAPI](https://fastapi.tiangolo.com/) — High-performance Python API framework
- [Next.js](https://nextjs.org/) — React framework
- [Tailwind CSS](https://tailwindcss.com/) — Utility-first CSS

---

<div align="center">

Built with ❤️ by [Jaimeen Bhagat](https://github.com/jaimeenbhagat)

**[🌐 Live Demo](https://legal-document-analyzer-65ex.onrender.com)** &nbsp;·&nbsp; **[🐛 Report Bug](https://github.com/jaimeenbhagat/Legal-Document-Analyzer/issues)** &nbsp;·&nbsp; **[💡 Request Feature](https://github.com/jaimeenbhagat/Legal-Document-Analyzer/issues)**

</div>
