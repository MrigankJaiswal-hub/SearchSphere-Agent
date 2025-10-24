🔍 SearchSphere Agent

An AI-powered hybrid search and labeling assistant that fuses Elastic Cloud BM25 + kNN retrieval with Google Vertex AI Gemini 2.0 reasoning — designed for enterprise knowledge search, evaluation, and agentic workflows.



🚀 Features

Hybrid Retrieval – Combines Elastic BM25 lexical relevance with kNN semantic search.

Generative Reasoning – Uses Vertex AI Gemini 2.0 Flash for natural-language refinement and summaries.

Context-Aware Filters – Filters by team, document type, and recency.

Label Assist UI – Rapidly generate ground-truth datasets for evaluation.

Live Metrics – View latency (p50/p95 ms) and Precision@K in real time.

Modular APIs – /api/search, /api/chat, /api/eval, /api/label-assist.


🧠 Architecture Overview

Frontend (Next.js 14, TypeScript, Tailwind)
     │
     ▼
API Gateway (Next.js route proxies / FastAPI endpoints)
     │
     ▼
Backend (FastAPI)
 ├─ Elastic Cloud (BM25 + kNN)
 ├─ Vertex AI Gemini 2.0 Flash + Text-Embedding-005
 ├─ Evaluation Engine (Precision@K, Latency)
 └─ Label Assist / Ground-truth Generator

🛠️ Tech Stack

Frontend: Next.js 14 • TypeScript • Tailwind CSS • Recharts
Backend: FastAPI • Python 3.11 • Elastic Cloud • Vertex AI SDK
Deployment: Google Cloud Run (backend) + Netlify (frontend)
CI/CD: Docker • GitHub Actions

⚙️ Installation & Local Setup
1️⃣ Clone the repo
git clone https://github.com/MrigankJaiswal-hub/SearchSphere-Agent.git
cd SearchSphere-Agent

2️⃣ Backend setup
cd backend
python -m venv .venv
.venv\Scripts\activate        # (Windows)
pip install -r requirements.txt


Create .env in backend/ using the template:

ELASTIC_CLOUD_ID=<your_id>
ELASTIC_API_KEY=<your_key>
ELASTIC_INDEX=searchsphere_docs
VERTEX_LOCATION=us-central1
GCP_PROJECT_ID=searchsphere-ai
VERTEX_EMBED_MODEL=text-embedding-005
VERTEX_CHAT_MODEL=gemini-2.0-flash-001
ES_KNN_NUM_CANDIDATES=120
CORS_ORIGIN=*


Run locally:

uvicorn app:app --reload --port 8080

3️⃣ Frontend setup
cd ../web
npm install
npm run dev


Create .env.local in web/:

NEXT_PUBLIC_API_BASE=http://127.0.0.1:8080


Then open 👉 http://localhost:3000

☁️ Deployment
Backend (Google Cloud Run)
gcloud run deploy searchsphere-backend \
  --source . \
  --region us-central1 \
  --set-env-vars "CORS_ORIGIN=https://your-frontend-domain.netlify.app"

Frontend (Netlify)

Deploy /web folder via GitHub import.

Set env var:

NEXT_PUBLIC_API_BASE=https://<your-cloudrun-backend-url>

📊 Evaluation & Label Assist

Label Assist Page: /label

Enter query → fetch candidates.

Select relevant chunks → add to ground truth.

Export groundtruth.json for evaluation.

Evaluation API:

curl -X POST "$URL/api/eval/precision" \
  -H "Content-Type: application/json" \
  -d '{"query":"hybrid search","k":10}'


🧩 Folder Structure
SearchSphere-Agent/
├─ backend/
│  ├─ app.py
│  ├─ routes/
│  ├─ utils/
│  ├─ requirements.txt
│  └─ .env.example
│
├─ web/
│  ├─ app/
│  ├─ components/
│  ├─ lib/
│  ├─ public/
│  ├─ package.json
│  └─ tailwind.config.ts
│
├─ scripts/
├─ assets/
└─ README.md

🏆 Metrics & Performance

Precision@K: live computed via /api/eval/precision.

Latency: p50 ≈ 700 ms | p95 ≈ 1100 ms.

Ground-truth assist: reduces labeling time by ~60%.

💡 Future Upgrades

Auth / multi-tenant support (Firebase or Cognito).

Multi-modal retrieval (images, audio, video).

Auto fine-tuning via Label Assist feedback.

Enhanced dashboards & metrics visualizations.

👨‍💻 Contributors

Mrigank Jaiswal – Full-stack developer, AI/ML integration & system architecture.

📄 License

MIT License © 2025 Mrigank Jaiswal
