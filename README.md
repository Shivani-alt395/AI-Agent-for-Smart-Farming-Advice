# 🌾 Smart Farming AI Agent

### AI Agent for Smart Farming Advice · Powered by IBM Granite (watsonx.ai) · Problem Statement #9

> A multi-agent, **RAG-powered** assistant that gives small-scale farmers real-time, localized agricultural guidance in their own language. It combines **IBM Granite** on **IBM watsonx.ai (IBM Cloud Lite)** with live weather, live mandi prices, and a curated agricultural knowledge base.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-ff4b4b)
![FastAPI](https://img.shields.io/badge/API-FastAPI-009688)
![IBM Granite](https://img.shields.io/badge/LLM-IBM%20Granite-0f62fe)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📌 Problem Statement

Small-scale farmers struggle with **crop selection, pest and disease control, irrigation timing, and fair market prices**. The information they need is scattered across weather services, government portals, and agri-tech platforms, and is mostly available only in English. Without localized, real-time guidance in their own language, farmers face higher risk, lower yields, and reduced income.

## 🎯 Solution

The Smart Farming AI Agent answers questions such as *"What crop is best for this season?"* or *"What is today's mandi rate for tomatoes?"* by:

1. **Classifying** the question (weather, crop, pest, soil, market, or general).
2. **Retrieving** trusted knowledge from a ChromaDB vector store (RAG) and **fetching** live weather and mandi data in parallel.
3. **Generating** a grounded answer with **IBM Granite** on watsonx.ai.
4. **Translating** the reply into the farmer's language and showing it with sources and a confidence score.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **Multi-agent system** | Weather Advisory, Market Price, Agri Knowledge, and Pest & Soil Health agents coordinated by a query classifier |
| 📚 **RAG pipeline** | 18 curated knowledge documents embedded with Sentence-Transformers and stored in ChromaDB |
| 🌦️ **Live weather advisory** | Open-Meteo data: current rain, today's total, rain chance, 7-day forecast and rain chart |
| 💰 **Live mandi prices** | data.gov.in (Agmarknet) prices with min, max and modal rates, with a curated MSP fallback |
| 🌐 **10 Indian languages** | English, Hindi, Marathi, Telugu, Tamil, Kannada, Gujarati, Punjabi, Bengali, Odia. The AI answer **and the whole interface** switch language |
| 📍 **Location-aware** | Search any Indian city or district (OpenStreetMap Nominatim) for local advice |
| 🔐 **Authentication** | Email OTP registration, login, and guest mode |
| 🔎 **Transparent answers** | Every answer shows its category, confidence score, and source references |
| 🛟 **Graceful fallback** | Demo mode with template answers when no IBM key is configured; clear warning when live weather is unavailable |

---

## 🏗️ Architecture

```
                     ┌──────────────────────────────┐
   Farmer ─────────▶ │  Streamlit UI  /  Web UI     │
 (10 languages)      └──────────────┬───────────────┘
                                    ▼
                     ┌──────────────────────────────┐
                     │  Query Classifier (Router)   │
                     └──────────────┬───────────────┘
        ┌───────────────┬───────────┴───────┬─────────────────┐
        ▼               ▼                   ▼                 ▼
 Weather Advisory  Market Price      Agri Knowledge    Pest & Soil Health
     Agent            Agent             Agent (RAG)        Agent (RAG)
        │               │                   │                 │
        ▼               ▼                   └────────┬────────┘
   Open-Meteo     data.gov.in                        ▼
      API        (Agmarknet)              ChromaDB + Sentence-Transformers
        │               │                            │
        └───────────────┴──────────────┬─────────────┘
                                       ▼
                     ┌──────────────────────────────┐
                     │  Prompt Builder (LangChain)  │
                     └──────────────┬───────────────┘
                                    ▼
                     ┌──────────────────────────────┐
                     │ IBM Granite · watsonx.ai     │
                     │ (granite-4-h-small)          │
                     └──────────────┬───────────────┘
                                    ▼
              Deep Translator → Confidence + Sources → Dashboard
```

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **LLM** | IBM Granite (`ibm/granite-4-h-small`) via IBM watsonx.ai (IBM Cloud Lite) |
| **RAG** | LangChain + ChromaDB + Sentence-Transformers (`all-MiniLM-L6-v2`) |
| **Frontend (deployment)** | Streamlit |
| **Backend API (optional)** | Python 3.11 + FastAPI + Uvicorn, plus an HTML/CSS/JS web UI |
| **Weather** | Open-Meteo (free, no API key) |
| **Market prices** | data.gov.in APMC / Agmarknet |
| **Geocoding** | OpenStreetMap Nominatim |
| **Translation** | deep-translator, langdetect |
| **Auth** | Email OTP (SMTP) with a local JSON user store |

---

## 📁 Project Structure

```
AI-Agent-for-Smart-Farming-Advice/
├── streamlit_app.py            # Streamlit frontend (main file for deployment)
├── translations.json           # UI strings for all 10 languages
├── .streamlit/
│   ├── config.toml             # Theme and server settings
│   └── secrets.toml.example    # Template for Streamlit secrets
├── app/
│   ├── main.py                 # FastAPI app factory
│   ├── api/routes.py           # REST endpoints
│   ├── core/
│   │   ├── config.py           # Pydantic settings (.env / secrets)
│   │   ├── granite_llm.py      # IBM Granite (watsonx.ai) wrapper
│   │   └── rag_pipeline.py     # ChromaDB + embeddings
│   ├── models/schemas.py       # Request / response models
│   └── services/
│       ├── farming_agent.py    # Query classifier + agent orchestrator
│       ├── knowledge_base.py   # 18 agricultural knowledge documents
│       ├── weather_service.py  # Open-Meteo weather and rain data
│       ├── market_service.py   # Mandi price service
│       ├── language_service.py # Translation and language detection
│       ├── email_service.py    # OTP email
│       └── user_store.py       # Users (JSON)
├── frontend/                   # Original HTML/CSS/JS web UI (FastAPI)
├── data/knowledge_base/        # Add custom .txt knowledge files here
├── tests/test_agent.py         # Pytest suite
├── run.py                      # FastAPI entry point
├── requirements.txt
├── env.example                 # Environment variable template
├── Procfile / render.yaml      # Render deployment (FastAPI)
└── runtime.txt                 # Python version
```

---

## 🚀 Quick Start

### 1. Clone and install

```bash
git clone https://github.com/Shivani-alt395/AI-Agent-for-Smart-Farming-Advice.git
cd AI-Agent-for-Smart-Farming-Advice

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / Mac

pip install -r requirements.txt
```

### 2. Configure IBM credentials

```bash
copy env.example .env          # Windows
# cp env.example .env          # Linux / Mac
```

Edit `.env`:

```env
IBM_API_KEY=your_ibm_cloud_api_key
IBM_WATSONX_PROJECT_ID=your_watsonx_project_id
```

**Getting free IBM credentials**
1. Sign up at [cloud.ibm.com](https://cloud.ibm.com) (the Lite plan is free).
2. Go to **Manage → Access (IAM) → API keys** and create an API key.
3. Open [dataplatform.cloud.ibm.com](https://dataplatform.cloud.ibm.com), create a project, and copy its **Project ID**.

> **Demo mode:** the app also runs without IBM credentials, using template answers. Add your key for full IBM Granite answers.

### 3. Run the app

**Option A: Streamlit UI (recommended)**
```bash
streamlit run streamlit_app.py
```
Opens at **http://localhost:8501**

**Option B: FastAPI + web UI**
```bash
python run.py
```
Opens at **http://localhost:8000** (API docs at `/api/docs`)

> The first start downloads the embedding model and builds the vector store, so it can take a minute.

---

## ☁️ Deploy on Streamlit Community Cloud

1. Push the repository to GitHub (make sure `.env` and `.streamlit/secrets.toml` are **not** committed).
2. On [share.streamlit.io](https://share.streamlit.io), create a new app and set the main file to `streamlit_app.py`. Choose **Python 3.11** in advanced settings.
3. In **App → Settings → Secrets**, paste:

```toml
IBM_API_KEY = "your_ibm_cloud_api_key"
IBM_WATSONX_URL = "https://us-south.ml.cloud.ibm.com"
IBM_WATSONX_PROJECT_ID = "your_watsonx_project_id"
GRANITE_MODEL_ID = "ibm/granite-4-h-small"

# Optional
DATA_GOV_API_KEY = ""
SMTP_USER = ""
SMTP_PASSWORD = ""
```

**Deployment notes**
- `sentence-transformers` pulls in PyTorch, which is heavy for the free tier. If the app runs out of memory, deploy on Render or Hugging Face Spaces instead (`render.yaml` is included).
- Registered users are stored in `data/users.json`, which Streamlit Cloud resets on restart. Guest mode always works; use an external database for persistent accounts.
- Without `SMTP_USER` and `SMTP_PASSWORD`, the email OTP is shown on screen (demo mode).

---

## 🌐 REST API (FastAPI mode)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/ask` | Ask a farming question |
| `GET` | `/api/v1/weather` | Weather forecast by coordinates |
| `GET` | `/api/v1/prices` | Mandi commodity prices |
| `GET` | `/api/v1/health` | Health check (Granite and vector store status) |
| `GET` | `/api/v1/languages` | Supported languages |
| `GET` | `/api/v1/sample-questions` | Sample questions |
| `POST` | `/api/v1/ingest` | Reload the knowledge base into ChromaDB |
| `POST` | `/api/v1/auth/send-otp` | Send an OTP to an email address |
| `POST` | `/api/v1/auth/verify-otp` | Verify the OTP |
| `POST` | `/api/v1/auth/register` | Register a farmer (verified OTP required) |
| `POST` | `/api/v1/auth/login` | Log in |

**Example**

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

## 📚 Knowledge Base

18 curated documents covering Kharif / Rabi / Zaid crop calendars, integrated pest management, fertilizer recommendations, soil health, government schemes (PM-KISAN, PMFBY, KCC, e-NAM), MSP, and post-harvest management.

To add your own knowledge, drop `.txt` files into `data/knowledge_base/` and run:

```bash
curl -X POST http://localhost:8000/api/v1/ingest
```

---

## 🏛️ IBM Cloud Services Used

| Service | Plan | Purpose |
|---|---|---|
| **IBM watsonx.ai** | Lite (free) | IBM Granite LLM inference |
| **IBM Granite** | `ibm/granite-4-h-small` | Reasoning, answer generation, personalization |

---

## 🧪 Tests

```bash
pytest tests/ -v
```

---

## 🔮 Future Scope

- IoT soil sensors and satellite data for field-level advice
- Voice assistant and more regional dialects
- Crop disease detection from leaf photos
- Mobile app with offline access, SMS and WhatsApp alerts

---

## 🔒 Security

- Never commit `.env` or `.streamlit/secrets.toml`. Make sure both are listed in `.gitignore` (add the line `.streamlit/secrets.toml` if it is missing).
- If a key was ever committed, rotate it immediately in IBM Cloud.

---

## 📄 License

MIT License. Built for the IBM Cloud hackathon · Problem Statement #9.

## 🙌 Acknowledgements

IBM watsonx.ai and Granite · Open-Meteo · data.gov.in (Agmarknet) · OpenStreetMap Nominatim · LangChain · ChromaDB · Streamlit
