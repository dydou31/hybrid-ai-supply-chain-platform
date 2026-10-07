# Hybrid AI Supply Chain Platform

> A production-oriented hybrid AI platform built around a real Supply Chain use case — from operational data and REST APIs to RAG, cloud infrastructure, security, observability and FinOps.

## Overview

The Hybrid AI Supply Chain Platform started from a concrete operational problem:

**How can Supply Chain teams transform fragmented supplier and delivery data into actionable decisions, while keeping AI workloads deployable both locally and in the cloud?**

The project evolved from a FastAPI/PostgreSQL application into a hybrid platform combining:

- Supply Chain operational data and KPIs
- REST APIs and interactive application interfaces
- PostgreSQL and vector search with pgvector
- Structured and semantic RAG
- Local LLM inference with Ollama
- Cloud LLM inference with Amazon Bedrock
- Docker-based local environments
- Kubernetes deployment concepts
- AWS infrastructure provisioned with Terraform
- ECS Fargate autoscaling
- RDS PostgreSQL and Valkey
- WebAuthn / passkey authentication
- Touch ID protected cloud operations
- OpenTelemetry-based observability
- Prometheus / Amazon Managed Service for Prometheus
- Grafana dashboards
- AWS FinOps monitoring
- CI/CD with GitHub Actions

The goal is not to reproduce a complete enterprise production environment. Instead, the project demonstrates how application engineering, AI engineering and platform engineering can be combined into one coherent architecture.

---

## 1. Business Problem

Supply Chain planners need to continuously understand:

- Which suppliers require attention?
- Which deliveries are late?
- How much stock is blocked?
- Which operational risks should be prioritized?
- What actions should be taken first?

Traditional dashboards provide visibility, but still require users to interpret the data manually.

This project adds an AI decision-support layer on top of structured Supply Chain data and unstructured knowledge.

```text
Raw operational data
        ↓
KPIs and supplier visibility
        ↓
Structured analysis
        ↓
Semantic knowledge retrieval
        ↓
LLM reasoning
        ↓
Actionable recommendation
```

---

## 2. Platform Capabilities

### Supply Chain APIs

The FastAPI backend exposes APIs for suppliers, deliveries, operational KPIs, platform health, AI queries and knowledge-base information.

Supplier data supports standard CRUD operations:

```text
GET     /suppliers
GET     /suppliers/{id}
POST    /suppliers
PUT     /suppliers/{id}
DELETE  /suppliers/{id}
```

Interactive API documentation is exposed through FastAPI / Swagger.

### Operational KPIs

The backend computes indicators such as:

- supplier delivery performance
- delayed deliveries
- delay rate
- average delay
- blocked stock
- supplier prioritization

These deterministic metrics can be injected into the AI reasoning context.

---

## 3. Architecture

The platform follows a hybrid local/cloud architecture.

```text
                         USER
                           │
                           ▼
                  Application / UI
                           │
                           ▼
                       FastAPI
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
         PostgreSQL     AI / RAG    Observability
              │            │            │
              ▼       ┌────┴────┐       ▼
           pgvector    │         │   Metrics/Traces
                       ▼         ▼
                    Ollama    Bedrock
                    LOCAL       AWS
```

### Local environment

```text
FastAPI
   │
PostgreSQL + pgvector
   │
Ollama
   │
Local observability stack
```

### AWS environment

```text
CloudFront
    │
Application Load Balancer
    │
ECS Fargate
    │
    ├────────► RDS PostgreSQL / pgvector
    ├────────► Valkey
    ├────────► Amazon Bedrock
    └────────► AWS Observability
```

---

## 4. Backend and Data Layer

The backend is implemented with Python and FastAPI.

Core responsibilities include:

- REST API exposure
- business logic
- database access
- Supply Chain KPI computation
- AI orchestration
- health monitoring
- authentication integration
- observability instrumentation

The persistence layer uses PostgreSQL, SQLAlchemy, Alembic and pgvector. Database migrations are version-controlled through Alembic.

PostgreSQL stores both structured operational entities and AI knowledge documents:

```text
PostgreSQL
│
├── Suppliers
├── Deliveries
├── Operational data
└── Knowledge documents
        │
        └── pgvector embeddings
```

Using pgvector keeps structured operational data and semantic knowledge close together and avoids adding a separate vector database for the current project scale.

---

## 5. AI and RAG

The AI layer combines deterministic structured retrieval with semantic retrieval.

### Structured Retrieval

Structured retrieval queries operational Supply Chain information directly. It can reason over supplier risk, delivery delays, delay rates, average delay, blocked stock and supplier prioritization.

The LLM is therefore not used as a database. Business calculations are performed deterministically before relevant facts are passed to the model.

### Semantic Retrieval

Unstructured knowledge documents are embedded and stored in PostgreSQL using pgvector.

The current embedding dimension is:

```text
384
```

At query time:

```text
User question
      │
Embedding generation
      │
pgvector cosine search
      │
Relevant knowledge documents
      │
RAG context
```

### Combined RAG

The reasoning context can combine:

```text
Structured Supply Chain facts
              +
Semantic knowledge documents
              +
        User question
              │
              ▼
             LLM
              │
              ▼
Analysis + recommendation
```

This keeps factual operational calculations outside the LLM while allowing natural-language synthesis and recommendations.

---

## 6. Hybrid LLM Inference

The application supports two inference environments.

### Local — Ollama

Local development uses Ollama, currently with:

```text
llama3.2:3b
```

This provides local experimentation, offline capability and predictable development cost.

### Cloud — Amazon Bedrock

The AWS environment uses Amazon Bedrock. The inference provider is selected through configuration.

```text
             AI Service
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
      Ollama           Bedrock
      LOCAL              AWS
```

This separates application logic from the inference environment and provides a portable hybrid design without claiming a complete dynamic model-routing/fallback platform.

---

## 7. Full-Stack Application and Control Center

The application layer combines backend services with a web interface and an operational Control Center.

The Control Center consolidates visibility across:

- application services
- PostgreSQL
- pgvector
- Ollama
- observability services
- authentication
- AWS synchronization
- cloud platform status

Conceptually:

```text
Application
Database
Vector capabilities
LLM services
Containers
Observability
Authentication
AWS synchronization
Cloud services
        │
        ▼
Platform Control Center
```

The Control Center is therefore more than a business dashboard: it acts as an operational interface between the application and its underlying platform.

---

## 8. Docker and Local Platform

The local environment is containerized with Docker and orchestrated with Docker Compose.

Containerization provides:

- reproducible environments
- isolated services
- consistent development setup
- simplified lifecycle management
- a foundation for deployment automation

Platform health endpoints expose the state of services including PostgreSQL, pgvector, Prometheus, Grafana, Tempo and Ollama where applicable.

---

## 9. Kubernetes

The project explores Kubernetes deployment and orchestration as part of the platform-engineering layer.

Kubernetes represents the natural orchestration layer for environments requiring container scheduling, service deployment, workload isolation, portability and horizontal scaling.

The project does **not** claim to reproduce a large production Kubernetes cluster, GPU/CUDA scheduling environment or enterprise multi-cluster platform.

The current AWS deployment uses ECS Fargate. This is an intentional distinction between demonstrated Kubernetes/orchestration concepts and the deployed AWS architecture.

---

## 10. AWS Platform

AWS infrastructure is provisioned as code with Terraform.

```text
Internet
   │
CloudFront
   │
Application Load Balancer
   │
ECS Fargate
   │
   ├── RDS PostgreSQL / pgvector
   ├── Valkey
   ├── Amazon Bedrock
   ├── Secrets Manager
   └── Observability services
```

### ECS Fargate

The application runs on ECS Fargate.

Current scaling configuration:

```text
Minimum tasks : 2
Maximum tasks : 4
CPU target    : 60%
Task CPU      : 512
Task memory   : 2048 MB
```

This demonstrates managed container execution, redundancy, load-balanced traffic and horizontal autoscaling without requiring EC2 host administration.

### RDS PostgreSQL

Cloud persistence uses managed PostgreSQL while retaining pgvector capabilities for semantic retrieval.

### Valkey

Valkey provides Redis-compatible capabilities for cloud platform concerns such as caching and server-side state.

---

## 11. Hybrid Local-to-AWS Workflow

A core design goal is to keep local development productive while maintaining a controlled cloud environment.

```text
LOCAL
─────────────────────────
FastAPI
PostgreSQL
pgvector
Ollama
Docker
Control Center
        │
        │ authenticated sync
        ▼
AWS
─────────────────────────
ECS Fargate
RDS PostgreSQL
pgvector
Valkey
Bedrock
Cloud observability
```

Cloud synchronization is not exposed as an unrestricted operation. Sensitive cloud actions are protected through authentication mechanisms integrated into the Control Center.

---

## 12. Security

Security is treated as a platform capability rather than an afterthought.

Implemented mechanisms include:

- AWS IAM
- AWS Secrets Manager
- server-side authentication sessions
- WebAuthn / passkeys
- Touch ID integration on supported devices
- authenticated AWS synchronization
- controlled cloud operations
- network separation within the AWS architecture

### WebAuthn and Touch ID

The platform supports WebAuthn authentication. On compatible Apple hardware, Touch ID can act as a strong authentication mechanism.

```text
Sensitive operation
       │
Authentication challenge
       │
WebAuthn / Touch ID
       │
Verified server session
       │
Authorized operation
```

This protects sensitive operations at the server/authentication layer rather than relying on a frontend-only control.

### Secrets and IAM

Application secrets are not intended to be hard-coded in source code. AWS Secrets Manager is integrated into the cloud architecture, while IAM policies control access between AWS services.

---

## 13. Observability

The platform is instrumented to expose operational and AI-specific telemetry.

The observability architecture includes:

- OpenTelemetry
- Prometheus-compatible metrics
- Amazon Managed Service for Prometheus
- Grafana
- tracing
- application health endpoints
- AI/RAG-specific metrics

### AI / RAG Metrics

The application exposes metrics including:

```text
rag_requests_total
rag_errors_total
rag_request_duration_seconds
```

Tracing covers operations such as:

```text
rag.semantic_search
embedding.generate
pgvector.search
llm.ollama.generate
llm.bedrock.converse
```

This makes the AI pipeline observable instead of treating LLM execution as a black box.

---

## 14. FinOps

Cloud infrastructure must be observable both technically and economically.

The project therefore includes AWS FinOps visibility to connect infrastructure decisions with operational cost awareness.

The FinOps layer is designed to answer questions such as:

- What is the infrastructure costing?
- Which services contribute to cost?
- How does cloud/AI usage affect consumption?
- How can capacity and cost be balanced?

FinOps information is surfaced through dedicated observability dashboards.

---

## 15. Infrastructure as Code

AWS infrastructure is managed with Terraform.

Terraform provides:

- reproducible infrastructure
- version-controlled architecture
- explicit dependencies
- reviewable infrastructure changes
- repeatable deployments

Infrastructure definitions are located under:

```text
terraform/aws/
```

The Terraform configuration includes core application infrastructure and observability components.

---

## 16. CI/CD

GitHub Actions provides the repository's automated CI/CD workflow.

```text
.github/workflows/ci.yml
```

CI/CD complements Docker and Terraform by connecting application development, validation and platform delivery.

---

## 17. Engineering Decisions

### Why PostgreSQL + pgvector?

Structured business data and semantic knowledge can remain within the same database technology. For the current scale, this reduces infrastructure complexity while preserving vector-search capabilities.

### Why Ollama + Bedrock?

Ollama provides fast local experimentation, offline development and low development cost. Bedrock provides managed cloud inference and AWS-native security/integration.

Supporting both demonstrates separation between application logic and model infrastructure.

### Why ECS Fargate on AWS?

Kubernetes is valuable for complex orchestration requirements, but also introduces operational overhead. ECS Fargate provides a simpler managed container runtime for this project's AWS environment while retaining load balancing, redundancy and horizontal autoscaling.

### Why instrument the AI layer?

AI systems require visibility beyond HTTP availability. The project therefore observes API/platform health, RAG request volume, errors, latency, semantic search, embeddings, LLM calls and cloud cost.

---

## 18. Technology Stack

### Application

```text
Python
FastAPI
SQLAlchemy
Alembic
PostgreSQL
HTML / CSS / JavaScript
```

### AI

```text
RAG
Structured retrieval
Semantic retrieval
pgvector
384-dimensional embeddings
Ollama
Amazon Bedrock
```

### Platform

```text
Docker
Docker Compose
Kubernetes
Terraform
GitHub Actions
```

### AWS

```text
CloudFront
Application Load Balancer
ECS Fargate
RDS PostgreSQL
Valkey
Amazon Bedrock
AWS Secrets Manager
IAM
Amazon Managed Service for Prometheus
Grafana
```

### Observability

```text
OpenTelemetry
Prometheus
Grafana
Tracing
Custom RAG metrics
FinOps dashboards
```

### Security

```text
IAM
Secrets Manager
WebAuthn
Passkeys
Touch ID
Server-side sessions
```

---

## 19. Repository Structure

```text
.
├── app/
│   ├── ai/
│   ├── observability/
│   ├── routers/
│   └── main.py
├── control_agent/
├── frontend/
│   └── src/
├── alembic/
├── terraform/
│   └── aws/
├── .github/
│   └── workflows/
├── scripts/
├── docker-compose.yml
├── README.md
├── PROJECT_SCOPE.md
└── ROADMAP.md
```

---

## 20. Scope and Limitations

This repository is a production-oriented engineering demonstrator. It demonstrates production architecture concepts without claiming to reproduce every capability or operational condition of a large enterprise AI platform.

### Implemented / Demonstrated

- full-stack application architecture
- REST APIs
- PostgreSQL persistence
- Supply Chain business logic and KPIs
- structured retrieval
- semantic RAG
- pgvector
- local LLM inference
- cloud LLM inference
- Docker / Docker Compose
- Kubernetes concepts
- AWS deployment
- Terraform
- ECS Fargate autoscaling
- RDS PostgreSQL
- Valkey
- authentication and server-side sessions
- WebAuthn / Touch ID
- Secrets Manager and IAM
- authenticated local-to-AWS synchronization
- OpenTelemetry / Prometheus / Grafana observability
- AI-specific telemetry
- FinOps visibility
- CI/CD

### Outside the Current Scope

The current implementation does not claim to provide:

- large-scale production Kubernetes operations
- GPU / CUDA workload scheduling
- enterprise multi-cloud orchestration
- complete disaster-recovery automation
- MLflow-based model lifecycle management
- complete ML training/retraining pipelines
- advanced dynamic model routing and automatic fallback
- a complete enterprise MCP / multi-agent ecosystem
- enterprise-scale load validation
- years of production operational history

These are potential production evolutions, not hidden claims of the current demonstrator.

---

## 21. Production Evolution

Natural extensions include:

```text
Advanced model routing and fallback
        │
Prompt and model version management
        │
Automated LLM evaluation
        │
MCP / agent tooling
        │
Advanced Kubernetes workloads
        │
GPU scheduling
        │
Multi-region resilience
        │
Disaster recovery automation
        │
Enterprise-scale load testing
        │
Extended LLMOps / MLOps lifecycle
```

The architecture is intended to allow these capabilities to be introduced incrementally.

---

## 22. Project Status

```text
STATUS: INTERVIEW FREEZE
```

The implementation is currently frozen for demonstration and interview preparation.

Current focus:

```text
Documentation
Architecture review
Demo preparation
Technical interview preparation
```

No additional feature development is planned during the freeze.

---

## 23. Core Engineering Principle

> **AI is only one layer of a production system.**

A useful AI application also requires reliable data, APIs, infrastructure, security, deployment, scalability, observability and cost control.

The Hybrid AI Supply Chain Platform explores that complete engineering lifecycle around a concrete Supply Chain use case.
