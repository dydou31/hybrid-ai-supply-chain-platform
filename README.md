# Hybrid AI Supply Chain Platform

**AI Foundation · Full Stack · AI Platform Engineering — Portfolio Project**

A production-oriented demonstrator combining **Full Stack Engineering, Hybrid AI, RAG, Platform Engineering, Cloud Infrastructure and Observability** around a realistic Supply Chain use case.

The project demonstrates how a business application can evolve from a REST API into an end-to-end AI platform: structured operational data, semantic knowledge retrieval, a local LLM, a web interface, containerized services, cloud infrastructure and full-stack observability.

---

## 🎯 Project Vision

Supply Chain teams work with both **structured operational data** and **unstructured business knowledge**.

A useful AI assistant must therefore be able to answer questions such as:

- How many suppliers do we have?
- Which supplier has the most delayed purchase orders?
- Which high-risk suppliers have the most delays?
- Which suppliers combine high risk, delays and blocked stock?
- Which supplier has recurring delivery issues?
- What is the best-performing supplier according to available KPIs?

This project implements a **Hybrid AI architecture** where deterministic operational analysis and semantic RAG complement each other instead of asking an LLM to calculate or invent business facts.

---

## 🏗️ Architecture

```text
                    HYBRID AI SUPPLY CHAIN PLATFORM

                               React
                                 │
                                 ▼
                              FastAPI
                                 │
             ┌───────────────────┼───────────────────┐
             │                   │                   │
             ▼                   ▼                   ▼
        PostgreSQL             Redis             Hybrid AI
             │                                       │
      SQLAlchemy/Alembic                ┌─────────────┴─────────────┐
                                       │                           │
                                       ▼                           ▼
                            Structured Retrieval                  RAG
                                       │                           │
                              Supply Chain KPIs              MiniLM Embeddings
                                       │                        pgvector
                                       │                           │
                                       └─────────────┬─────────────┘
                                                     │
                                                     ▼
                                                Llama 3.2
                                                  Ollama


                     ─────── PLATFORM LAYER ───────

                    Docker / Docker Compose
                           GitHub Actions
                         Kubernetes / Helm
                           Terraform
                         AWS ECS / Fargate
                              ECR


                     ───── OBSERVABILITY ─────

                           OpenTelemetry
                          /             \
                         ▼               ▼
                   Prometheus          Tempo
                         \               /
                          \             /
                              Grafana
```

---

## 🧠 Hybrid AI

The AI Assistant combines two complementary retrieval strategies.

### Structured Retrieval

Operational questions are answered using data retrieved from PostgreSQL and deterministic backend calculations.

Examples include:

- supplier counts;
- risk-level analysis;
- purchase-order delays;
- delay rates;
- average delay duration;
- blocked stock;
- supplier rankings;
- multi-criteria supplier analysis.

The LLM receives the calculated context and is responsible for **natural-language presentation**, not for inventing the underlying business metrics.

### Semantic RAG

Unstructured operational knowledge is embedded using:

**Sentence Transformers — `all-MiniLM-L6-v2`**

Embeddings are stored directly in PostgreSQL using:

**pgvector**

Relevant documents are retrieved through vector similarity before being supplied to the LLM.

### Local LLM

Generation is performed locally with:

**Llama 3.2 3B via Ollama**

This makes it possible to demonstrate a self-hosted LLM workflow without depending on an external inference API.

### Business Language

A Supply Chain business glossary allows the assistant to understand common terminology and abbreviations such as:

```text
frns → fournisseur / supplier
cmd / cde → commande
PO → purchase order
DA → demande d'achat
BC → bon de commande
BL / DN → delivery note
ASN → advanced shipping notice
EDI → electronic data interchange
LT → lead time
MOQ → minimum order quantity
OTD → on-time delivery
ETA / ETD
RMA
VMI / CMI
KPI
```

The glossary is extensible and helps bridge informal business language and backend concepts.

---

## 📊 Demonstration Dataset

The local environment contains a deterministic Supply Chain dataset designed for reproducible demonstrations.

```text
104 suppliers
501 purchase orders
Multiple countries
Low / medium / high supplier risk
Blocked-stock values
Requested and confirmed delivery dates
On-time and delayed purchase orders
```

The dataset supports realistic operational queries while remaining completely synthetic.

---

## 💬 AI Assistant

The React frontend includes an interactive AI Assistant connected to the FastAPI AI endpoint.

Example questions:

```text
How many suppliers do we have?

Which supplier has the most delays?

Which high-risk suppliers have the most delayed orders?

Which suppliers combine high risk, delays and blocked stock?

Tell me about Dynamic Automotive.

Which supplier has recurring delivery delays?
```

The UI exposes the type of context supplied to the model:

- **PostgreSQL — structured operational data**
- **pgvector — semantic knowledge retrieval**

`Enter` submits a question while `Shift + Enter` creates a new line.

---

## 📦 Supplier Management

The application exposes supplier data through both REST APIs and the React frontend.

The Suppliers interface supports:

- live supplier data from PostgreSQL;
- text filtering;
- filtering through supplier names, countries and risk levels;
- ascending / descending sorting;
- numerical blocked-stock sorting;
- supplier risk visualization.

---

## 📈 Supply Chain KPIs

The backend calculates operational KPIs from suppliers and purchase orders.

Examples include:

- total suppliers;
- high-risk suppliers;
- blocked stock;
- purchase-order counts;
- delayed orders;
- delay rates;
- average delay duration;
- supplier performance comparisons.

Redis is used for KPI caching where appropriate.

---

## 🔌 REST API

The FastAPI backend exposes endpoints for:

### Suppliers

```text
GET    /suppliers
POST   /suppliers
PUT    /suppliers/{id}
DELETE /suppliers/{id}
```

### Purchase Orders

Purchase-order endpoints expose operational procurement data.

### KPIs

```text
/kpis/...
```

### Hybrid AI

```text
POST /ai/ask
```

The response can include:

- generated answer;
- semantic RAG sources;
- structured-data source information.

### API Documentation

FastAPI automatically exposes OpenAPI documentation through Swagger UI.

---

## ❤️ Platform Health

Dedicated health endpoints expose individual infrastructure dependencies.

```text
/health
/health/postgres
/health/redis
/health/prometheus
/health/grafana
/health/tempo
/health/ollama
/health/platform
```

The aggregate platform endpoint distinguishes healthy and degraded states.

The React **Platform Control Center** visualizes the status of the main platform services.

---

## 🔭 Observability

The platform includes an end-to-end observability stack.

### OpenTelemetry

FastAPI is instrumented with OpenTelemetry for application telemetry and distributed tracing.

### Prometheus

Prometheus collects application and platform metrics.

### Grafana

Grafana provides provisioned dashboards and datasource configuration.

### Tempo

Tempo receives and stores distributed traces exported through OpenTelemetry.

The stack makes it possible to investigate API activity and infrastructure behavior from a single observability environment.

---

## 🐳 Containerization

The local platform runs through Docker Compose.

Core services include:

```text
FastAPI
PostgreSQL + pgvector
Redis
Prometheus
Grafana
Tempo
```

Ollama runs locally and is accessed by the containerized API for Llama inference.

---

## ☸️ Kubernetes & Helm

The project includes Kubernetes deployment resources and a Helm chart.

The local Kubernetes environment has been validated using Minikube.

This layer demonstrates:

- application deployment;
- Kubernetes resources;
- Helm-based packaging and configuration;
- separation between application and infrastructure concerns.

---

## 🏗️ Infrastructure as Code

Terraform is used to represent infrastructure declaratively.

The project includes infrastructure work for both local Kubernetes-related resources and AWS deployment.

---

## ☁️ AWS Deployment

A cloud deployment path has been validated on AWS using:

- **Amazon ECR** for container images;
- **Amazon ECS**;
- **AWS Fargate**;
- Terraform-managed infrastructure.

The API container was built for the appropriate Fargate architecture and successfully deployed and health-checked in AWS.

The demonstration infrastructure is not intended to represent a complete production AWS architecture.

---

## 🔄 CI/CD

GitHub Actions validates the project through automated workflows.

The CI environment includes support for the PostgreSQL/pgvector requirements needed by the application.

This provides automated validation of backend changes before integration.

---

## 🖥️ Frontend

The frontend is built with:

```text
React
TypeScript
Vite
CSS
```

Main views include:

### Dashboard

Overview of Supply Chain KPIs and platform information.

### Suppliers

Searchable and sortable supplier dataset.

### AI Assistant

Hybrid AI interface combining PostgreSQL structured context and pgvector RAG.

### Platform Control Center

Infrastructure-health visualization with automatic refresh.

---

## 🧪 Testing

Backend automated tests cover core application capabilities including:

- API health;
- suppliers;
- purchase orders;
- KPIs;
- Redis integration.

The frontend is validated through ESLint and the Vite production build.

---

## 🧱 Technology Stack

### Full Stack

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- PostgreSQL
- Redis
- React
- TypeScript
- Vite
- REST / OpenAPI

### AI / RAG

- Llama 3.2
- Ollama
- Sentence Transformers
- MiniLM
- pgvector
- Structured retrieval
- Semantic retrieval
- Hybrid AI context
- Business terminology normalization

### Platform Engineering

- Docker
- Docker Compose
- Kubernetes
- Minikube
- Helm
- Terraform
- GitHub Actions

### Cloud

- AWS
- Amazon ECR
- Amazon ECS
- AWS Fargate

### Observability

- OpenTelemetry
- Prometheus
- Grafana
- Tempo

---

## 📁 Repository Structure

```text
hybrid-ai-supply-chain-platform/
│
├── app/
│   ├── ai/
│   │   ├── business_glossary.py
│   │   ├── embeddings.py
│   │   ├── ingest.py
│   │   ├── models.py
│   │   ├── retrieval.py
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── structured_context.py
│   │   └── structured_retrieval.py
│   │
│   ├── models/
│   ├── routers/
│   ├── schemas/
│   ├── services/
│   ├── database.py
│   └── main.py
│
├── frontend/
├── tests/
├── scripts/
├── alembic/
├── kubernetes/
├── helm/
├── terraform/
├── monitoring/
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## 🚀 Local Development

### Start the platform

```bash
docker compose up -d --build
```

Check running services:

```bash
docker compose ps
```

### Start Ollama

Make sure Ollama is available locally with the expected model:

```bash
ollama pull llama3.2:3b
```

### Start the frontend

```bash
cd frontend
npm install
npm run dev
```

### Run backend tests

```bash
docker compose run --rm \
  -e PYTHONPATH=/app \
  -v "$PWD/tests:/app/tests" \
  api pytest tests -v
```

### Validate the frontend

```bash
cd frontend
npm run lint
npm run build
```

---

## 🧩 Engineering Challenges

The project was deliberately built incrementally, exposing realistic integration and debugging scenarios.

Examples encountered during development include:

- SQLAlchemy/Alembic model metadata integration;
- PostgreSQL connection failures;
- Redis service addressing inside Docker;
- pgvector embedding-dimension alignment;
- pgvector support in CI;
- ARM64 vs AMD64 container architecture for AWS Fargate;
- Python PostgreSQL driver dependencies in cloud containers;
- OpenTelemetry and Tempo integration;
- frontend graceful degradation when backend services are unavailable;
- filtering irrelevant semantic retrieval results;
- preventing LLMs from altering deterministic business rankings;
- scaling structured AI context beyond a small supplier dataset.

These issues are part of the engineering value of the project: the objective is not only to assemble technologies, but to understand how they interact and how to troubleshoot them.

---

## 🔐 Scope & Limitations

This repository is a **portfolio demonstrator**, not a production Supply Chain system.

It intentionally demonstrates a broad engineering chain while keeping the environment manageable on a local development machine.

The current implementation does **not** claim to provide:

- production multi-cloud infrastructure;
- enterprise IAM or network architecture;
- production disaster recovery;
- GPU scheduling;
- production autoscaling;
- full LLMOps lifecycle management;
- autonomous AI agents;
- MCP infrastructure;
- production-grade model routing;
- enterprise secrets management.

These would represent logical extensions of the platform rather than capabilities already implemented.

---

## 🎯 Engineering Focus

The project sits at the intersection of two engineering perspectives.

### AI Foundation / Full Stack Engineering

```text
React
  ↓
FastAPI
  ↓
PostgreSQL / Redis
  ↓
Structured Retrieval + RAG
  ↓
Local LLM
```

### AI Foundation / Platform Engineering

```text
Application
    ↓
Docker
    ↓
CI/CD
    ↓
Kubernetes / Helm
    ↓
Terraform / AWS
    ↓
OpenTelemetry
    ↓
Prometheus / Grafana / Tempo
```

The same application is used across both perspectives, demonstrating the relationship between **building AI-enabled product features** and **building the platform required to run and observe them**.

---

## 👤 Author

**Dylan Taibi**

AI Foundation · AI Platform Engineering · Full Stack Engineering

Portfolio Project — France

---

## 📌 Project Status

The core demonstrator is implemented and operational.

- [x] FastAPI backend
- [x] PostgreSQL
- [x] SQLAlchemy
- [x] Alembic migrations
- [x] Suppliers API
- [x] Purchase Orders API
- [x] KPI API
- [x] Redis caching
- [x] Docker / Docker Compose
- [x] Automated backend tests
- [x] GitHub Actions
- [x] PostgreSQL pgvector
- [x] Sentence Transformer embeddings
- [x] Semantic RAG
- [x] Structured Supply Chain retrieval
- [x] Business terminology glossary
- [x] Local Llama inference with Ollama
- [x] Hybrid AI Assistant
- [x] React / TypeScript frontend
- [x] Supplier search and sorting
- [x] Platform Control Center
- [x] OpenTelemetry
- [x] Prometheus
- [x] Grafana
- [x] Tempo
- [x] Kubernetes
- [x] Helm
- [x] Terraform
- [x] AWS ECR
- [x] AWS ECS / Fargate deployment

**Next stage: portfolio documentation, architecture presentation and technical interview demonstration.**
