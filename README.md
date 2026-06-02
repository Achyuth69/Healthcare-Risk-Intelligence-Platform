# Explainable Healthcare Risk Intelligence Platform

## Production-Grade AI System | Google DeepMind Architecture Standards

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    HEALTHCARE RISK INTELLIGENCE PLATFORM             │
├─────────────────────────────────────────────────────────────────────┤
│  Frontend (React + TypeScript)                                       │
│  ├── Dashboard / Risk Visualization                                  │
│  ├── Patient Risk Reports                                            │
│  ├── SHAP/LIME Explainability UI                                     │
│  └── LLM Chat Interface (RAG)                                        │
├─────────────────────────────────────────────────────────────────────┤
│  API Gateway (FastAPI)                                               │
│  ├── Auth Service (JWT + RBAC)                                       │
│  ├── Prediction Service                                              │
│  ├── Explainability Service                                          │
│  └── RAG / LLM Service                                               │
├─────────────────────────────────────────────────────────────────────┤
│  ML Layer                                                            │
│  ├── XGBoost / Random Forest / LightGBM                             │
│  ├── SHAP + LIME Explainability                                      │
│  ├── Fine-Tuned Llama 3 (LoRA/QLoRA)                                │
│  └── RAG Pipeline (LangChain + ChromaDB)                            │
├─────────────────────────────────────────────────────────────────────┤
│  Data Layer                                                          │
│  ├── PostgreSQL (Structured Data)                                    │
│  ├── ChromaDB (Vector Store)                                         │
│  └── S3 (Model Artifacts / PDFs)                                    │
├─────────────────────────────────────────────────────────────────────┤
│  Infrastructure                                                      │
│  ├── Docker + Kubernetes (EKS)                                       │
│  ├── CI/CD (GitHub Actions)                                          │
│  └── Monitoring (Prometheus + Grafana)                               │
└─────────────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Clone and setup
git clone <repo>
cd healthcare-risk-platform

# Environment setup
cp .env.example .env
# Fill in your secrets

# Docker Compose (development)
docker-compose up --build

# Access
# Frontend:  http://localhost:3000
# API Docs:  http://localhost:8000/docs
# Grafana:   http://localhost:3001
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| ML Models | XGBoost, Random Forest, LightGBM |
| Explainability | SHAP, LIME |
| LLM | Llama 3 + LoRA/QLoRA via HuggingFace |
| RAG | LangChain + ChromaDB + Sentence Transformers |
| Backend | FastAPI + PostgreSQL |
| Frontend | React + TypeScript + Recharts |
| Auth | JWT + RBAC |
| Infra | Docker + Kubernetes + AWS EKS |
| CI/CD | GitHub Actions |
| Monitoring | Prometheus + Grafana |
