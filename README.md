# 🚀 Universal RAG System

## Kya Hai Ye Project?

**RAG = Retrieval Augmented Generation** (Document ke basis par AI answers)

Ek complete system jismein:
- 📄 Documents upload kar sakte ho (PDF, Word, Excel, PowerPoint)
- 🔍 Documents mein search kar sakte ho
- 🤖 AI se questions pooch sakte ho → AI document se relevant parts nikal kar jawab deta hai

---

## 🎯 How It Works (Simple Example)

```
1. User: Invoice.pdf upload karta hai
   ↓
2. System: PDF se text nikalta hai, AI embeddings banata hai
   ↓
3. System: Embeddings ko Vector Database (Pinecone) mein store karta hai
   ↓
4. User: "Invoice mein total amount kya hai?"
   ↓
5. System: Relevant parts dhoondhta hai, Claude AI ko deta hai
   ↓
6. Claude: "Total amount: Rs. 50,000"
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│      FRONTEND (React + TypeScript)      │
│  - Document upload interface            │
│  - Chat interface                       │
│  - Search functionality                 │
└────────────┬────────────────────────────┘
             │ HTTP/REST API
             ↓
┌─────────────────────────────────────────┐
│    BACKEND (Python + FastAPI)           │
│  - File processing                      │
│  - Embedding generation                 │
│  - RAG logic                            │
│  - Chat endpoints                       │
└────────────┬────────────────────────────┘
             │
      ┌──────┴──────┬────────────┬───────────┐
      ↓             ↓            ↓           ↓
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│PostgreSQL│ │ Pinecone │ │  Redis   │ │ OpenAI  │
│(Metadata)│ │(Vectors) │ │ (Cache)  │ │/ Claude │
└──────────┘ └──────────┘ └──────────┘ └──────────┘
```

---

## 📁 Project Structure

```
Universal_Rag_System/
│
├── backend/                 # Python FastAPI backend
│   └── main.py             # Main application file
│
├── requirements.txt         # Python libraries
├── .env                     # Configuration (secret - git mein nahi)
├── .env.example            # Configuration template
├── .gitignore              # Git ignore rules
└── README.md               # Ye file!
```

---

## 🛠️ Tech Stack

### Frontend (Baad Mein Banayenge)
- **React 18** - UI Framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Axios** - API calls
- **Vite** - Build tool

### Backend (Abhi Bana Rahe Hain)
- **Python 3.10+** - Language
- **FastAPI** - Web framework
- **Uvicorn** - Server
- **Pydantic** - Data validation
- **SQLAlchemy** - ORM

### Databases
- **PostgreSQL** - SQL database (metadata store)
- **Pinecone** - Vector database (embeddings)
- **Redis** - Cache (performance)

### AI/LLM Services
- **OpenAI** - Embeddings (text to vector)
- **Claude (Anthropic)** - AI responses
- **LangChain** - LLM orchestration

### File Processing
- **PyPDF2/pdfplumber** - PDF handling
- **python-docx** - Word documents
- **openpyxl** - Excel sheets
- **python-pptx** - PowerPoint
- **Pillow/pytesseract** - Images & OCR

---

## ⚡ Quick Start

### Prerequisites

```bash
# Check Python version (3.10+ chahiye)
python --version

# Check if pip installed
pip --version

# Check if git installed
git --version
```

### Step 1: Clone/Setup Repository

```bash
cd /path/to/Universal_Rag_System
git init
git add .
git commit -m "Initial setup"
```

### Step 2: Create Virtual Environment

```bash
# Virtual environment banao
python -m venv venv

# Activate karo
# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate
```

Agar terminal mein `(venv)` dikhta hai to sab theek hai! ✅

### Step 3: Install Dependencies

```bash
# requirements.txt se sab libraries install ho jayengi
pip install -r requirements.txt

# Verify installation
python -c "import fastapi; print('FastAPI installed!')"
```

### Step 4: Setup Configuration

```bash
# .env file already hai
# Abhi dummy values hain, baad mein real API keys daalni hongi
cat .env
```

### Step 5: Setup PostgreSQL Database

#### Option 1: Local PostgreSQL (Advanced)
```bash
# PostgreSQL install karo (https://www.postgresql.org/download/)
# Command line mein:
psql -U postgres
CREATE DATABASE rag_system;
```

#### Option 2: Using Docker Compose (Easy - Baad Mein)
```bash
docker-compose up -d
```

### Step 6: Run Backend

```bash
# Make sure venv activated hai
# Bash mein:
uvicorn backend.main:app --reload

# Ya Python se:
python -m uvicorn backend.main:app --reload
```

**Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

✅ Backend running hai!

### Step 7: Test API

#### Browser mein:
```
http://localhost:8000/
```

Response:
```json
{
  "message": "Welcome to Universal RAG System API",
  "version": "1.0.0",
  "docs": "/docs"
}
```

#### Interactive API Docs:
```
http://localhost:8000/docs
```

---

## 🔑 API Endpoints (Abhi)

### Working Endpoints

| Method | Endpoint | Kaam |
|--------|----------|------|
| GET | `/` | Welcome message |
| GET | `/health` | Server status check |
| GET | `/docs` | Interactive API documentation |

### Coming Soon (Baad Mein Banayenge)

| Method | Endpoint | Kaam |
|--------|----------|------|
| POST | `/api/documents/upload` | Document upload |
| GET | `/api/documents` | Documents list |
| DELETE | `/api/documents/{id}` | Document delete |
| POST | `/api/rag/query` | RAG query |
| POST | `/api/chat` | Chat with AI |

---

## 🔐 Environment Variables Guide

### Kaunsi API Keys Chahiye:

#### 1. **OpenAI** (Embeddings ke liye)
```
Website: https://platform.openai.com/api-keys
Key: OPENAI_API_KEY
Use: Text ko vectors mein convert karna
Cost: $0.0001 per 1K tokens
```

#### 2. **Anthropic/Claude** (AI Responses ke liye)
```
Website: https://console.anthropic.com/
Key: ANTHROPIC_API_KEY
Use: Smart AI answers generate karna
Cost: $0.003-0.020 per 1K tokens
```

#### 3. **Pinecone** (Vector Database ke liye)
```
Website: https://pinecone.io/
Key: PINECONE_API_KEY
Use: Vectors store aur search karna
Cost: Free tier available
```

---

## 📊 Project Phases

```
Phase 1: Backend Setup ✅ (DONE)
  ✅ FastAPI app
  ✅ Environment setup
  ✅ Basic endpoints

Phase 2: Database Setup (NEXT)
  ⏳ PostgreSQL setup
  ⏳ Database models (SQLAlchemy)
  ⏳ Migration setup (Alembic)

Phase 3: File Processing (PHASE 3)
  ⏳ PDF upload endpoint
  ⏳ Text extraction
  ⏳ File validation

Phase 4: Embeddings (PHASE 4)
  ⏳ OpenAI integration
  ⏳ Embedding generation
  ⏳ Pinecone connection

Phase 5: RAG Engine (PHASE 5)
  ⏳ Query processing
  ⏳ Similarity search
  ⏳ Claude integration

Phase 6: Frontend (PHASE 6)
  ⏳ React setup
  ⏳ UI components
  ⏳ API integration

Phase 7: Chat Interface (PHASE 7)
  ⏳ Chat UI
  ⏳ Real-time updates
  ⏳ History management

Phase 8: Deployment (PHASE 8)
  ⏳ Docker setup
  ⏳ Production config
  ⏳ Deployment
```

---

## 🐛 Troubleshooting

### Error: "No module named 'fastapi'"
```bash
# Solution: Virtual environment activate nahi hua
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Phir install karo
pip install -r requirements.txt
```

### Error: "Connection refused" (Redis/PostgreSQL)
```bash
# Solution: Database running nahi hai
# Docker compose use karo (baad mein)
docker-compose up -d
```

### Error: "Port 8000 already in use"
```bash
# Solution: Koi aur app port 8000 use kar raha hai
# Different port use karo:
uvicorn backend.main:app --port 8001
```

---

## 📚 Learning Resources

### Python & FastAPI
- [FastAPI Official Docs](https://fastapi.tiangolo.com/)
- [Python Official Docs](https://docs.python.org/3/)

### Databases
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [Pinecone Docs](https://pinecone.io/)
- [Redis Docs](https://redis.io/)

### AI/LLM
- [OpenAI API Docs](https://platform.openai.com/docs/)
- [Anthropic Claude Docs](https://docs.anthropic.com/)
- [LangChain Docs](https://python.langchain.com/)

---

## 💰 Cost Estimation

### Development (FREE)
- All services ke free tier use kar sakte ho
- Local PostgreSQL/Redis

### Production (Estimated Monthly)
```
OpenAI Embeddings:    $0.10 - $1
Claude API:           $15 - $50
Pinecone Vector DB:   $5 - $25
PostgreSQL:           $10 - $20
Redis:                $5 - $15
Hosting:              $5 - $50
───────────────────────────────
TOTAL:                $40 - $161/month
```

---

## 📝 Git Commands

```bash
# Status check
git status

# Add changes
git add .

# Commit
git commit -m "Message"

# View history
git log --oneline
```

---

## ✅ Checklist

- [x] Backend folder setup
- [x] main.py created
- [x] .env files created
- [x] .gitignore created
- [x] requirements.txt created
- [x] README created
- [ ] PostgreSQL setup
- [ ] Database models
- [ ] File upload endpoint
- [ ] Embeddings integration
- [ ] RAG engine
- [ ] Frontend setup
- [ ] Chat interface
- [ ] Deployment

---

## 🚀 Next Step

Ab database setup karte hain!

```bash
# Phase 2: Database Setup
# PostgreSQL models banana
# SQLAlchemy setup
# Database migrations
```

---

## 📞 Support

Koi error ya confusion ho to batao!

---

**Made with ❤️ for Learning**

Happy Coding! 🎉
