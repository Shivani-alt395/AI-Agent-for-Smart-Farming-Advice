# Smart Farming AI Agent 🌾
### Powered by IBM Granite (watsonx.ai) | Problem Statement #9

> An AI Agent for Smart Farming Advice, powered by **RAG (Retrieval-Augmented Generation)**, supports small-scale farmers with real-time, localized agricultural guidance using **IBM Cloud Lite** + **IBM Granite** LLM.

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Smart Farming AI Agent                        │
│                                                                  │
│  Frontend (HTML/CSS/JS)   FastAPI Backend   IBM Cloud Services  │
│  ┌─────────────────┐      ┌─────────────┐   ┌───────────────┐  │
│  │  Chat Interface │─────▶│  /api/v1    │──▶│ IBM Granite   │  │
│  │  Multilingual   │      │  /ask       │   │ watsonx.ai    │  │
│  │  Weather Widget │      │  /weather   │   └───────────────┘  │
│  │  Quick Q&A      │      │  /prices    │                       │
│  └─────────────────┘      └──────┬──────┘                       │
│                                  │                               │
│         ┌────────────────────────┼──────────────────┐           │
│         ▼                        ▼                   ▼           │
│  ┌─────────────┐    ┌────────────────────┐  ┌──────────────┐   │
│  │ ChromaDB    │    │   External APIs     │  │  Language    │   │
│  │ Vector Store│    │ ┌────────────────┐  │  │  Service     │   │
│  │ RAG Context │    │ │ Open-Meteo API │  │  │ (Translation)│   │
│  │             │    │ │ Weather Data   │  │  └──────────────┘   │
│  │ sentence-   │    │ └────────────────┘  │                     │
│  │ transformers│    │ ┌────────────────┐  │                     │
│  └─────────────┘    │ │ data.gov.in    │  │                     │
│                     │ │ Mandi Prices   │  │                     │
│                     │ └────────────────┘  │                     │
│                     └────────────────────-┘                     │
└─────────────────────────────────────────────────────────────────┘
```

## 🛠️ Technology Stack

| Layer | Technology |
|-------|-----------|
| **LLM** | IBM Granite (`ibm/granite-3-8b-instruct`) via watsonx.ai |
| **RAG** | LangChain + ChromaDB + SentenceTransformers |
| **Backend** | Python 3.11 + FastAPI + Uvicorn |
| **Frontend** | HTML5 + CSS3 + Vanilla JavaScript |
| **Weather API** | Open-Meteo (free, no API key) |
| **Market API** | data.gov.in APMC prices |
| **Translation** | deep-translator (Google Translate) |
| **IBM Cloud** | watsonx.ai (Lite plan), IBM Watson Assistant (optional) |

---

## 📁 Project Structure

```
Smart_Farming_IBMProject/
├── app/
│   ├── core/
│   │   ├── config.py          # Pydantic Settings (reads .env)
│   │   ├── granite_llm.py     # IBM Granite LLM wrapper
│   │   └── rag_pipeline.py    # ChromaDB + embeddings
│   ├── api/
│   │   └── routes.py          # FastAPI endpoint definitions
│   ├── services/
│   │   ├── farming_agent.py   # Main RAG + Granite orchestrator
│   │   ├── knowledge_base.py  # Agricultural knowledge documents
│   │   ├── weather_service.py # Open-Meteo weather API
│   │   ├── market_service.py  # Mandi/APMC price service
│   │   └── language_service.py # Multi-language translation
│   ├── models/
│   │   └── schemas.py         # Pydantic request/response models
│   └── main.py                # FastAPI app factory + startup
├── frontend/
│   ├── index.html             # Main UI
│   └── static/
│       ├── css/style.css      # IBM Design-inspired styles
│       └── js/app.js          # Chat interface logic
├── data/
│   ├── knowledge_base/        # Add custom .txt files here
│   └── chroma_db/             # Auto-created vector store
├── tests/
│   └── test_agent.py          # Pytest test suite
├── run.py                     # Application entry point
├── requirements.txt           # Python dependencies
└── env.example                # Environment variable template
```

---

## 🚀 Quick Start

### Step 1 — Clone & Install

```bash
# Clone the project
cd Smart_Farming_IBMProject

# Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Step 2 — Configure IBM Credentials

Copy `env.example` to `.env`:
```bash
copy env.example .env
```

Edit `.env` and fill in your IBM credentials:
```env
IBM_API_KEY=your_ibm_cloud_api_key_here
IBM_WATSONX_PROJECT_ID=your_watsonx_project_id_here
```

**How to get IBM Cloud credentials (free):**
1. Sign up at [cloud.ibm.com](https://cloud.ibm.com) (Lite plan is free)
2. Go to **Manage → Access (IAM) → API Keys** → Create API Key
3. Go to [dataplatform.cloud.ibm.com](https://dataplatform.cloud.ibm.com) → Create a Project → Copy the Project ID
4. Paste both values in your `.env` file

> **Note:** The app runs in **Demo Mode** even without IBM credentials — it uses template responses. Add your IBM API key for full IBM Granite-powered answers.

### Step 3 — Run the Application

```bash
python run.py
```

Open your browser at: **http://localhost:8000**

API documentation: **http://localhost:8000/api/docs**

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/ask` | Main chat endpoint — ask a farming question |
| `GET`  | `/api/v1/weather` | Get weather forecast by coordinates |
| `GET`  | `/api/v1/prices` | Get mandi/APMC commodity prices |
| `GET`  | `/api/v1/health` | Health check (IBM Granite + vector store status) |
| `GET`  | `/api/v1/languages` | List supported languages |
| `GET`  | `/api/v1/sample-questions` | Sample farming questions |
| `POST` | `/api/v1/ingest` | Reload knowledge base into ChromaDB |

### Example API Call

```bash
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What crop should I sow this Kharif season?",
    "language": "en",
    "location": "Nashik, Maharashtra",
    "latitude": 19.9975,
    "longitude": 73.7898
  }'
```

---

## 🌾 Capabilities

### 1. Multilingual Support
- Supports **10 Indian languages**: English, Hindi, Marathi, Telugu, Tamil, Kannada, Gujarati, Punjabi, Bengali, Odia
- Auto-detects language and translates queries/responses

### 2. Real-Time Weather Advice
- 7-day forecasts from Open-Meteo (free, no API key needed)
- Smart irrigation scheduling based on weather
- Pest risk assessment based on humidity/temperature

### 3. Live Mandi Prices
- Connects to **data.gov.in** for APMC market prices
- Falls back to curated MSP (Minimum Support Price) data
- Covers 18+ major commodities

### 4. RAG-Powered Knowledge Base
- 18 curated agricultural knowledge documents covering:
  - Kharif/Rabi/Zaid crop calendars
  - IPM pest management
  - Fertilizer recommendations
  - Soil health management
  - Government schemes (PM-KISAN, PMFBY, KCC, e-NAM)
  - Post-harvest management

### 5. IBM Granite LLM
- Uses `ibm/granite-3-8b-instruct` via watsonx.ai
- Contextual prompting with retrieved knowledge + weather + market data
- Graceful fallback to demo mode when credentials not configured

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

---

## 📦 Adding Custom Knowledge

Add `.txt` files to the `data/knowledge_base/` directory, then call:
```bash
curl -X POST http://localhost:8000/api/v1/ingest
```
The new documents will be chunked, embedded, and added to ChromaDB automatically.

---

## 🏛️ IBM Cloud Services Used

| Service | Tier | Purpose |
|---------|------|---------|
| **IBM watsonx.ai** | Lite (free) | IBM Granite LLM inference |
| **IBM Watson Assistant** | Lite (optional) | Dialog management |
| **IBM Watson Discovery** | Lite (optional) | Document retrieval |

---

## 📄 License

MIT License — Built for IBM Cloud hackathon | Problem Statement #9
