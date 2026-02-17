# 🏛️ Legal AI - Document Analysis System

A modern, production-ready **Retrieval-Augmented Generation (RAG)** system for intelligent legal document analysis. Built with Python, FastAPI, LangChain, FAISS, Google Gemini AI, and a beautiful Next.js frontend.

> **⚠️ DISCLAIMER**: This is a document analysis tool, NOT a legal advice system. Always consult a qualified attorney for legal guidance.

---

## ✨ Features

### 🎨 Modern UI/UX
- **Premium Chat Interface** - Clean, ChatGPT-like conversational UI
- **Glass Morphism Design** - Modern frosted glass effects with purple gradients
- **Responsive Layout** - Works seamlessly on desktop and mobile
- **Dark Sidebar** - Elegant session management with gradient accents
- **Smooth Transitions** - Polished hover effects and micro-interactions
- **Drag & Drop Upload** - Intuitive PDF file uploading

### 💬 Chat Features
- **Multi-Session Support** - Create, switch, and manage multiple chat sessions
- **Session Persistence** - Each session maintains its own conversation history
- **Smart Naming** - Sessions auto-named based on uploaded documents
- **Document Context** - Filter queries to specific documents
- **Quick Actions** - Pre-built prompts for common legal queries

### 📄 Document Analysis
- **PDF Upload & Processing** - Upload multiple legal documents
- **Intelligent Chunking** - Smart text splitting for optimal retrieval
- **Semantic Search** - Find relevant information using vector similarity
- **Multi-Document Queries** - Search across all uploaded documents
- **Document Picker** - Select specific documents for focused analysis

### 🤖 AI-Powered Features
- **RAG Architecture** - Retrieval-Augmented Generation for accurate answers
- **Google Gemini Integration** - Powered by Gemini Pro LLM
- **Context-Aware Responses** - Answers grounded in your documents
- **Risk Assessment** - Automatic identification of legal risks
- **No Hallucination** - AI only answers from provided context

### 🔧 Technical Features
- **FastAPI Backend** - High-performance async API
- **FAISS Vector Store** - Fast similarity search
- **Session Isolation** - Each session has its own vector store
- **Real-time Health Checks** - Backend status monitoring
- **Error Handling** - Graceful error recovery and user feedback

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Google Gemini API Key

### 1. Clone & Setup

\`\`\`bash
# Navigate to the project
cd "Legal Document Analysis System using Retrieval-Augmented Generation (RAG)"

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
\`\`\`

### 2. Configure Environment

\`\`\`bash
# Copy example env file
cp .env.example .env

# Edit .env and add your Gemini API key
GOOGLE_API_KEY=your_gemini_api_key_here
\`\`\`

### 3. Start Backend

\`\`\`bash
# From project root
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
\`\`\`

### 4. Start Frontend

\`\`\`bash
# From project root (in a new terminal)
cd frontend
npm install
npm run dev
\`\`\`

### 5. Open Application

Visit **http://localhost:3000** in your browser.

---

## 📁 Project Structure

\`\`\`
Legal Document Analysis System/
├── app/                      # Backend (FastAPI)
│   ├── main.py              # API endpoints
│   ├── chat.py              # RAG chat engine
│   ├── ingest.py            # PDF processing
│   ├── prompts.py           # LLM prompt templates
│   └── config.py            # Configuration
│
├── frontend/                 # Frontend (Next.js)
│   ├── app/
│   │   ├── page.tsx         # Main page
│   │   ├── layout.tsx       # App layout
│   │   └── globals.css      # Global styles
│   ├── components/
│   │   └── PremiumChatInterface.tsx  # Main chat UI
│   └── lib/
│       └── api.ts           # API client
│
├── data/                     # Data storage
│   ├── pdfs/                # Uploaded PDFs
│   └── faiss_index/         # Vector stores
│
├── requirements.txt          # Python dependencies
├── docker-compose.yml        # Docker setup
├── Dockerfile               # Container config
└── README.md                # This file
\`\`\`

---

## 🎯 Usage Guide

### Uploading Documents

1. Click the **paperclip icon** or drag & drop PDF files
2. Wait for processing (documents are chunked and embedded)
3. See uploaded documents in the sidebar

### Asking Questions

1. Type your question in the input box
2. Press **Enter** or click the send button
3. AI responds with context from your documents

### Quick Actions

Use pre-built prompts for common tasks:
- 📋 **Summarize** - Get a document summary
- ⚖️ **Key Clauses** - Extract important clauses
- ⚠️ **Risks** - Identify potential risks
- 💰 **Obligations** - List all obligations

### Managing Sessions

- Click **New Chat** to start a fresh session
- Switch between sessions in the sidebar
- Each session maintains its own documents and history

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | Next.js 15, React, TypeScript | Modern web UI |
| **Styling** | Tailwind CSS | Utility-first CSS |
| **Backend** | FastAPI, Python 3.11+ | High-performance API |
| **RAG** | LangChain | Document processing |
| **Vector DB** | FAISS | Similarity search |
| **Embeddings** | Google Gemini | Text vectorization |
| **LLM** | Gemini Pro | Answer generation |
| **PDF** | PyPDF | Document parsing |

---

## 🔑 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| \`GET\` | \`/health\` | Backend health check |
| \`POST\` | \`/upload\` | Upload PDF documents |
| \`POST\` | \`/chat\` | Send chat message |
| \`GET\` | \`/documents\` | List uploaded documents |

---

## 🐳 Docker Deployment

\`\`\`bash
# Build and run with Docker Compose
docker-compose up --build

# Access at http://localhost:3000
\`\`\`

---

## 🔒 Security Notes

- API keys are stored in \`.env\` (never commit this file)
- Session data is isolated per user session
- No data is sent to external services except Gemini API
- Documents are stored locally in \`data/\` directory

---

## 📝 License

This project is for educational purposes.

---

## 🙏 Acknowledgments

- [LangChain](https://langchain.com/) - RAG framework
- [Google Gemini](https://deepmind.google/technologies/gemini/) - AI model
- [FAISS](https://github.com/facebookresearch/faiss) - Vector search
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
- [Next.js](https://nextjs.org/) - Frontend framework
- [Tailwind CSS](https://tailwindcss.com/) - Styling

---

<p align="center">
  Built with ❤️ for legal document analysis
</p>
