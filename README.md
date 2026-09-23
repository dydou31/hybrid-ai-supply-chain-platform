Hybrid AI Supply Chain Platform

AI Platform Engineering / AI Foundation / Full Stack Portfolio Project

Hybrid AI Supply Chain Platform est une plateforme de démonstration conçue autour d’un cas d’usage Supply Chain.

Le projet combine Backend Engineering, AI Engineering, LLM/RAG, Platform Engineering, Cloud, Kubernetes, Infrastructure as Code, CI/CD et Observability.

L’objectif est de démontrer la capacité à construire une plateforme AI moderne de l’application jusqu’à son infrastructure d’exécution.

⸻

🎯 Project Vision

                    HYBRID AI SUPPLY CHAIN PLATFORM
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
          BACKEND               AI              PLATFORM
              │                  │                  │
           FastAPI              LLM             Docker
         PostgreSQL              RAG            Kubernetes
         SQLAlchemy           pgvector          Terraform
           Alembic            Forecast          CI/CD
           REST API           Scoring          Security
                              Agents          Networking
              │                  │                  │
              └──────────────────┼──────────────────┘
                                 │
                           OBSERVABILITY
                                 │
                    OpenTelemetry / Prometheus
                              Grafana

⸻

🧱 Current Stack

Backend

* Python
* FastAPI
* Pydantic
* SQLAlchemy
* PostgreSQL
* Alembic

Infrastructure

* Docker
* Docker Compose

API

* REST
* OpenAPI
* Swagger UI

AI — planned

* LLM APIs
* RAG
* embeddings
* pgvector
* forecasting
* anomaly detection
* AI agents
* model routing

Platform — planned

* Kubernetes
* Helm
* Terraform
* GitHub Actions
* Container Registry

Observability — planned

* OpenTelemetry
* Prometheus
* Grafana
* structured logging

⸻

📁 Project Structure

hybrid-ai-supply-chain-platform/
│
├── app/
│   ├── main.py
│   │
│   ├── models/
│   │   ├── supplier.py
│   │   └── purchase_order.py
│   │
│   ├── schemas/
│   │   ├── supplier.py
│   │   └── purchase_order.py
│   │
│   ├── routers/
│   │   ├── suppliers.py
│   │   ├── purchase_orders.py
│   │   └── kpis.py
│   │
│   └── services/
│
├── alembic/
│
├── tests/
│
├── data/
│
├── docker/
│
├── kubernetes/
│
├── terraform/
│
├── docs/
│
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
├── requirements.txt
├── PROJECT_SCOPE.md
├── ROADMAP.md
└── README.md

⸻

🏗️ Current Architecture

                    Supply Chain Client
                            │
                            ▼
                    ┌───────────────┐
                    │    FastAPI    │
                    │      API      │
                    └───────┬───────┘
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
        Suppliers      Purchase Orders    KPIs
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                      SQLAlchemy
                            │
                            ▼
                       PostgreSQL
                            │
                         Alembic

⸻

✅ Current Features

API

* FastAPI application
* OpenAPI / Swagger
* Health endpoint
* Modular routers
* Pydantic validation

Suppliers

* Create supplier
* Get suppliers
* Get supplier by ID
* Update supplier
* Delete supplier
* Risk level validation
* Blocked stock tracking

Purchase Orders

* Create purchase order
* Get purchase orders
* Get purchase order by ID
* Supplier foreign key validation
* PO status validation
* Monetary precision with Decimal

KPIs

* Supplier PO count
* Total PO value
* Delayed orders
* Delay rate
* Average delay
* Blocked stock

Database

* PostgreSQL
* SQLAlchemy
* Alembic
* Database migrations
* Foreign keys

⸻

🚧 Roadmap

The project will evolve through the following stages:

Backend
   ↓
Docker
   ↓
CI/CD
   ↓
AI / RAG
   ↓
Observability
   ↓
Kubernetes
   ↓
Terraform
   ↓
Cloud
   ↓
LLMOps

See ROADMAP.md for the complete roadmap.

⸻

🚀 Local Installation

1. Clone the repository

git clone https://github.com/dydou31/hybrid-ai-supply-chain-platform.git
cd hybrid-ai-supply-chain-platform

2. Create the Python environment

python3 -m venv .venv
source .venv/bin/activate

3. Install dependencies

pip install -r requirements.txt

4. Start PostgreSQL

docker compose up -d

5. Apply database migrations

alembic upgrade head

6. Start the API

uvicorn app.main:app --reload

API:

http://127.0.0.1:8000

Swagger:

http://127.0.0.1:8000/docs

⸻

🐳 Docker

The application is progressively being containerized.

Build:

docker build -t hybrid-ai-platform .

Run:

docker run -p 8000:8000 hybrid-ai-platform

The final architecture will use Docker containers for the API, database and AI services where appropriate.

⸻

🧪 API Examples

Health

GET /health

Example:

{
  "status": "healthy",
  "timestamp": "2026-09-23T..."
}

Suppliers

GET /suppliers

Purchase Orders

GET /purchase-orders

Supplier KPIs

GET /kpis/suppliers

Example:

{
  "supplier": "ZF",
  "purchase_orders": 1,
  "total_value_eur": 6250,
  "delayed_orders": 1,
  "delay_rate": 100,
  "average_delay_days": 2
}

⸻

🤖 AI Architecture — Planned

The AI layer will progressively introduce:

                   AI REQUEST
                       │
                       ▼
                 AI API / Agent
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
           RAG                LLM Router
             │                   │
        pgvector             Model A/B/C
             │                   │
       ┌─────┴─────┐             │
       ▼           ▼             ▼
   Documents    SQL Data      Response
       │           │
       └─────┬─────┘
             ▼
        AI RESPONSE

Planned capabilities:

* RAG
* embeddings
* vector search
* Supply Chain AI assistant
* forecasting
* anomaly detection
* supplier risk scoring
* model routing
* model fallback
* AI evaluation

⸻

☁️ Platform Architecture — Planned

GitHub
   │
   ▼
GitHub Actions
   │
   ▼
Container Registry
   │
   ▼
Kubernetes
   │
   ├── FastAPI
   ├── AI Service
   ├── PostgreSQL
   ├── Redis
   └── Observability
          │
          ├── OpenTelemetry
          ├── Prometheus
          └── Grafana

Infrastructure will progressively be managed using:

* Terraform
* Kubernetes
* Helm
* cloud-native services

⸻

🔐 Security — Planned

* JWT authentication
* RBAC
* secrets management
* TLS
* secure configuration
* dependency scanning
* container image scanning
* IAM
* least privilege
* network isolation

⸻

📊 Observability — Planned

The platform will expose technical and AI metrics.

Examples:

API latency
HTTP errors
Request throughput
Database latency
Container health
LLM latency
Token usage
Model errors
AI request traces

Technologies:

* OpenTelemetry
* Prometheus
* Grafana
* structured logging

⸻

🎓 Skills Demonstrated

This project is designed to demonstrate:

Software Engineering

* Python
* FastAPI
* REST APIs
* SQLAlchemy
* PostgreSQL
* testing
* modular architecture

AI Engineering

* LLM integration
* RAG
* vector databases
* embeddings
* forecasting
* AI agents
* model evaluation

Platform Engineering

* Docker
* Kubernetes
* Helm
* Terraform
* CI/CD
* container registries
* cloud infrastructure

Cloud Engineering

* AWS / Azure / OVHcloud concepts
* networking
* IAM
* storage
* compute
* infrastructure automation

Observability

* OpenTelemetry
* Prometheus
* Grafana
* logs
* metrics
* traces

Domain

* Supply Chain
* suppliers
* purchase orders
* risk
* delays
* inventory

⸻

👤 Author

Dylan Taibi

AI Platform Engineering / AI Full Stack — Portfolio Project

France

⸻

📌 Project Status

Current stage: Backend foundation + Supply Chain API

Next major stage: Containerization and platform engineering

[x] FastAPI
[x] PostgreSQL
[x] SQLAlchemy
[x] Alembic
[x] Suppliers API
[x] Purchase Orders API
[x] KPI API
[ ] Dockerized API
[ ] CI/CD
[ ] AI / LLM
[ ] RAG / pgvector
[ ] Observability
[ ] Kubernetes
[ ] Helm
[ ] Terraform
[ ] Cloud deployment
[ ] LLMOps