# 🔍 SearchSphere Agent

**An AI-powered hybrid search and labeling assistant** that fuses **Elastic Cloud BM25 + kNN** retrieval with **Google Vertex AI Gemini 2.0 reasoning** — built to revolutionize enterprise knowledge search and evaluation.

---

## 📘 Table of Contents
1. [Overview](#overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Tech Stack](#tech-stack)
5. [Installation](#installation)
6. [Environment Variables](#environment-variables)
7. [Running Locally](#running-locally)
8. [Deployment](#deployment)
9. [Usage](#usage)
10. [Project Structure](#project-structure)
11. [Evaluation Metrics](#evaluation-metrics)
12. [Future Upgrades](#future-upgrades)
13. [Contributors](#contributors)
14. [License](#license)

---

## 🧭 Overview

SearchSphere Agent is a full-stack AI search platform that integrates **Elastic Cloud hybrid retrieval** (BM25 + vector search) with **Google Vertex AI Gemini 2.0** for contextual reasoning, evaluation, and dataset labeling.

It helps teams and enterprises **find smarter, label faster, and evaluate efficiently** — a complete foundation for AI-powered RAG systems.

---

## ⚙️ Features

- 🔍 **Hybrid Search** — Combines Elastic BM25 (lexical) + kNN (semantic) for deep understanding.  
- 🤖 **Gemini Reasoning** — Uses Vertex AI Gemini-2.0-Flash for summaries and responses.  
- 🧩 **Label Assist** — Create ground-truth JSONs interactively for model evaluation.  
- 📊 **Metrics Dashboard** — Live precision@K and latency stats (p50/p95).  
- 💬 **Conversational Refinement** — Natural chat-style interface for query reasoning.  
- 🔐 **Cloud Ready** — Dockerized backend, deployed via Google Cloud Run + Netlify.  

---




## 🏗️ Architecture

```

Frontend (Next.js 14, TypeScript, Tailwind)
│
▼
Next.js API routes (proxy)
│
▼
Backend (FastAPI)
├── Elastic Cloud (BM25 + kNN)
├── Vertex AI (Gemini + Embeddings)
├── Evaluation Engine
└── Label Assist Service

````

---

## 🧰 Tech Stack

| Layer | Technology |
|-------|-------------|
| **Frontend** | Next.js 14, React 18, Tailwind CSS, Recharts |
| **Backend** | FastAPI (Python 3.11), Elastic Cloud, Vertex AI |
| **Deployment** | Google Cloud Run (backend), Netlify (frontend) |
| **Database** | Elastic Cloud index (`searchsphere_docs`) |
| **CI/CD** | GitHub Actions, Docker |

---

## 💻 Installation

### 1️⃣ Clone the repository
```bash
git clone https://github.com/MrigankJaiswal-hub/SearchSphere-Agent.git
cd SearchSphere-Agent
````

### 2️⃣ Backend setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # (Windows)
pip install -r requirements.txt
```

### 3️⃣ Frontend setup

```bash
cd ../web
npm install
```

---

## 🔐 Environment Variables

### Backend `.env`

```ini
ELASTIC_CLOUD_ID=your_elastic_cloud_id
ELASTIC_API_KEY=your_elastic_api_key
ELASTIC_INDEX=searchsphere_docs
VERTEX_LOCATION=us-central1
GCP_PROJECT_ID=searchsphere-ai
VERTEX_EMBED_MODEL=text-embedding-005
VERTEX_CHAT_MODEL=gemini-2.0-flash-001
ES_KNN_NUM_CANDIDATES=120
CORS_ORIGIN=*
```

### Frontend `.env.local`

```ini
NEXT_PUBLIC_API_BASE=http://127.0.0.1:8080
```

---

## ▶️ Running Locally

### Start backend

```bash
cd backend
uvicorn app:app --reload --port 8080
```

### Start frontend

```bash
cd web
npm run dev
```

Visit 👉 **[http://localhost:3000](http://localhost:3000)**

---

## ☁️ Deployment

### Google Cloud Run (Backend)

```bash
gcloud run deploy searchsphere-backend \
  --source . \
  --region us-central1 \
  --set-env-vars "CORS_ORIGIN=https://your-frontend-url.netlify.app"
```

### Netlify (Frontend)

1. Import `/web` directory from GitHub.
2. Add Environment Variable:

   ```
   NEXT_PUBLIC_API_BASE=https://<your-cloudrun-url>
   ```
3. Deploy site.

---

## 🧠 Usage

* `/` → Main chat & hybrid search page
* `/metrics` → Live latency & precision dashboard
* `/label` → Label Assist tool for dataset generation

**To test evaluation manually:**

```bash
curl -X POST "$URL/api/eval/precision" \
-H "Content-Type: application/json" \
-d '{"query":"hybrid search","k":10}'
```

---

## 📂 Project Structure

```
SearchSphere-Agent/
├── backend/
│   ├── app.py
│   ├── routes/
│   ├── utils/
│   ├── tests/
│   └── requirements.txt
│
├── web/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── public/
│   ├── package.json
│   └── tailwind.config.ts
│
├── scripts/
├── assets/
└── README.md
```

---

## 📊 Evaluation Metrics

* **Precision@K**: Evaluates top-K relevance.
* **Latency Tracking**: p50/p95 in milliseconds.
* **Label Assist**: Exports `groundtruth.json` for retraining.

Example output:

```
p50: 730 ms | p95: 1100 ms | Precision@10: 0.86
```

---

## 🔮 Future Upgrades

* Multi-modal retrieval (text, images, audio, video).
* Auth & multi-tenant support (Firebase/Cognito).
* Feedback-driven fine-tuning of hybrid fusion weights.
* Enhanced real-time dashboards and analytics.

---

## 👨‍💻 Contributors

**Mrigank Jaiswal**
*B.Tech in ECE | AI/ML & Cloud Enthusiast*
🖥️ Built full-stack architecture, Elastic-Vertex integration, frontend UI, and deployment automation.

---

## 🪪 License

This project is licensed under the **MIT License**.
© 2025 Mrigank Jaiswal

---

```

---

Would you like me to generate a **short version (under 1 page)** specifically formatted for Devpost “Project Documentation” too?
```




