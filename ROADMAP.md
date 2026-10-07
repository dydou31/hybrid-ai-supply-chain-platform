# ROADMAP — Hybrid AI Supply Chain Platform

## 1. Roadmap Purpose

This roadmap records the engineering progression of the Hybrid AI Supply Chain Platform from a Supply Chain backend into a hybrid, observable and secured AI platform.

It has two goals:

1. document the capabilities that have already been implemented or demonstrated;
2. separate the current interview-ready platform from possible future production evolution.

The project is currently under **INTERVIEW FREEZE**. The roadmap is therefore no longer a development checklist.

---

## 2. Engineering Journey

```text
Supply Chain Use Case
        ↓
FastAPI / REST
        ↓
PostgreSQL / Alembic
        ↓
Business KPIs
        ↓
Docker
        ↓
AI / LLM
        ↓
RAG / pgvector
        ↓
Full-Stack Application
        ↓
Kubernetes Concepts
        ↓
Terraform / CI-CD
        ↓
AWS Platform
        ↓
Hybrid Local / Cloud
        ↓
Security
        ↓
Observability
        ↓
FinOps
        ↓
Platform Control Center
```

Each phase extended the same system rather than creating disconnected demonstrations.

---

# COMPLETED MILESTONES

## Phase 1 — Supply Chain Domain Foundation ✅

**Objective:** start from a realistic business problem.

Implemented:

- supplier domain model;
- delivery / operational data concepts;
- supplier risk information;
- blocked-stock information;
- realistic Supply Chain use cases.

Outcome:

The platform is grounded in a business domain rather than a generic AI chatbot.

---

## Phase 2 — FastAPI Backend ✅

**Objective:** expose the business domain through a modern Python API.

Implemented:

- Python backend;
- FastAPI application;
- REST endpoints;
- request/response validation;
- Swagger / OpenAPI documentation;
- health endpoints;
- modular routing.

Outcome:

A testable API layer became the foundation of the application.

---

## Phase 3 — PostgreSQL, SQLAlchemy and Alembic ✅

**Objective:** move from application logic to persistent data.

Implemented:

- PostgreSQL;
- SQLAlchemy;
- Alembic migrations;
- persistent Supply Chain entities;
- database schema versioning.

Outcome:

The platform gained a reproducible relational persistence layer.

---

## Phase 4 — Supply Chain KPIs and Decision Data ✅

**Objective:** transform raw operational data into useful information.

Implemented or demonstrated:

- delivery-performance indicators;
- delayed-delivery analysis;
- delay rate;
- average delay;
- blocked-stock visibility;
- supplier prioritization;
- structured operational facts.

Outcome:

The application could provide deterministic business information before introducing generative AI.

---

## Phase 5 — Dockerized Local Environment ✅

**Objective:** make the development environment reproducible.

Implemented:

- Docker;
- Docker Compose;
- containerized services;
- service health visibility;
- reproducible local startup.

Outcome:

The application evolved from a local Python process into a multi-service platform environment.

---

## Phase 6 — AI / Local LLM Integration ✅

**Objective:** add natural-language reasoning without making cloud inference mandatory.

Implemented:

- Ollama integration;
- local LLM inference;
- AI service abstraction;
- natural-language Supply Chain queries.

Current local model:

`llama3.2:3b`

Outcome:

AI experimentation became possible locally and offline.

---

## Phase 7 — Retrieval-Augmented Generation ✅

**Objective:** ground LLM responses in application data and knowledge.

Implemented:

- structured retrieval;
- semantic retrieval;
- PostgreSQL pgvector;
- 384-dimensional embeddings;
- cosine similarity search;
- combined RAG context;
- AI reasoning over retrieved facts and knowledge.

Outcome:

The LLM became a reasoning layer over retrieved information rather than an isolated chatbot.

---

## Phase 8 — Full-Stack Application ✅

**Objective:** expose business and AI capabilities through an interactive application.

Implemented:

- web application layer;
- backend/API integration;
- Supply Chain information;
- AI interaction;
- operational views;
- platform-oriented Control Center capabilities.

Outcome:

The project became an end-to-end application rather than an API-only demonstrator.

---

## Phase 9 — Kubernetes Concepts and Portability ✅ / Scoped

**Objective:** demonstrate container-orchestration concepts and deployment portability.

Demonstrated:

- declarative deployment concepts;
- deployments/services;
- container scheduling concepts;
- workload isolation;
- horizontal-scaling concepts.

Scope boundary:

The project does not claim operation of a large production Kubernetes or GPU/CUDA cluster.

AWS deployment intentionally uses ECS Fargate rather than EKS.

Outcome:

Kubernetes knowledge is represented without overstating production experience.

---

## Phase 10 — Infrastructure as Code with Terraform ✅

**Objective:** make cloud infrastructure reproducible and reviewable.

Implemented:

- Terraform;
- version-controlled AWS infrastructure;
- explicit infrastructure dependencies;
- application infrastructure definitions;
- observability infrastructure definitions.

Location:

`terraform/aws/`

Outcome:

Cloud architecture became infrastructure as code rather than manually configured infrastructure.

---

## Phase 11 — CI/CD ✅

**Objective:** connect development with automated validation and delivery practices.

Implemented:

- GitHub Actions;
- automated CI workflow;
- validation pipeline;
- container/delivery-oriented workflow.

Location:

`.github/workflows/ci.yml`

Outcome:

The repository demonstrates a repeatable engineering delivery lifecycle.

---

## Phase 12 — AWS Cloud Platform ✅

**Objective:** evolve the local application into a production-oriented cloud architecture.

Implemented or provisioned:

- CloudFront;
- Application Load Balancer;
- ECS Fargate;
- RDS PostgreSQL;
- pgvector capability;
- Valkey;
- Amazon Bedrock;
- AWS Secrets Manager;
- IAM;
- AWS networking;
- managed observability components.

ECS configuration:

```text
Minimum tasks : 2
Maximum tasks : 4
CPU target    : 60%
Task CPU      : 512
Task memory   : 2048 MB
```

Outcome:

The platform gained a managed AWS runtime with redundancy and horizontal autoscaling.

---

## Phase 13 — Hybrid Local / Cloud AI Architecture ✅

**Objective:** preserve productive local development while enabling managed cloud inference.

Implemented architecture:

```text
LOCAL                              AWS
─────                              ───
FastAPI                            ECS Fargate
PostgreSQL / pgvector              RDS / pgvector
Ollama                             Amazon Bedrock
Docker                             Valkey
Local observability                Cloud observability
          │                            ▲
          └──── controlled sync ───────┘
```

Outcome:

Application logic is not tightly coupled to a single inference environment.

---

## Phase 14 — Security and Strong Authentication ✅

**Objective:** protect sensitive platform and cloud operations.

Implemented or integrated:

- IAM;
- Secrets Manager;
- server-side authentication sessions;
- WebAuthn;
- passkeys;
- Touch ID on supported devices;
- authenticated local-to-AWS synchronization;
- protected cloud actions;
- network/access-control concepts.

Outcome:

Security became a first-class platform layer rather than a frontend-only control.

---

## Phase 15 — Observability and AI Telemetry ✅

**Objective:** make both the application and the AI pipeline observable.

Implemented or integrated:

- OpenTelemetry;
- Prometheus-compatible metrics;
- Amazon Managed Service for Prometheus;
- Grafana;
- tracing;
- health monitoring;
- RAG metrics;
- AI-specific spans.

Examples:

```text
rag_requests_total
rag_errors_total
rag_request_duration_seconds
```

Trace operations include:

```text
rag.semantic_search
embedding.generate
pgvector.search
llm.ollama.generate
llm.bedrock.converse
```

Outcome:

AI execution can be inspected as an engineering workload rather than treated as a black box.

---

## Phase 16 — FinOps Visibility ✅

**Objective:** connect cloud architecture with cost awareness.

Implemented:

- AWS FinOps observability;
- cloud cost visibility;
- dedicated dashboarding;
- cost/architecture awareness in the operational platform.

Outcome:

The platform addresses not only whether infrastructure works, but also what operating it means economically.

---

## Phase 17 — Platform Control Center ✅

**Objective:** consolidate platform operations into one coherent interface.

The Control Center brings together visibility across:

- application;
- database;
- vector capabilities;
- LLM services;
- containers;
- authentication;
- local/cloud state;
- AWS synchronization;
- observability;
- FinOps.

Outcome:

The final application exposes both business functionality and the platform required to operate it.

---

## Phase 18 — Documentation and Interview Freeze 🔒

**Objective:** stabilize the project and prepare a clear technical demonstration.

Current work:

- README modernization;
- PROJECT_SCOPE alignment;
- ROADMAP alignment;
- architecture review;
- demo validation;
- interview preparation.

Freeze rule:

No speculative feature development or risky infrastructure changes before the interview.

---

# CURRENT ARCHITECTURE

```text
                              USER
                                │
                  ┌─────────────┴─────────────┐
                  │                           │
              LOCAL MODE                  AWS MODE
                  │                           │
                  ▼                           ▼
             Application                  CloudFront
                  │                           │
                  │                           ▼
                  │                           ALB
                  │                           │
                  │                           ▼
                  │                      ECS Fargate
                  │                       2–4 tasks
                  │                           │
          ┌───────┼───────┐          ┌───────┼────────┐
          │       │       │          │       │        │
          ▼       ▼       ▼          ▼       ▼        ▼
       FastAPI PostgreSQL Ollama    RDS    Valkey   Bedrock
                  │                   │
               pgvector            pgvector
          │                               │
          └──────────────┬────────────────┘
                         │
                         ▼
                AI / RAG Application
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
       Security     Observability     FinOps
          │              │              │
      WebAuthn        OTel / AMP      AWS Cost
      Touch ID        Prometheus      Visibility
      IAM             Grafana
      Secrets
          └──────────────┼──────────────┘
                         │
                         ▼
                PLATFORM CONTROL CENTER
```

---

# CURRENT CAPABILITY MAP

## Application Engineering

- Python / FastAPI ✅
- REST APIs ✅
- Swagger / OpenAPI ✅
- SQLAlchemy ✅
- Alembic ✅
- PostgreSQL ✅
- web application / UI ✅
- business KPIs ✅

## AI Engineering

- LLM integration ✅
- Ollama local inference ✅
- Amazon Bedrock cloud inference ✅
- structured retrieval ✅
- semantic RAG ✅
- pgvector ✅
- embeddings ✅
- AI telemetry ✅

## Platform Engineering

- Docker / Compose ✅
- Kubernetes concepts ✅
- Terraform ✅
- CI/CD ✅
- containerized runtime ✅
- cloud infrastructure ✅
- horizontal autoscaling ✅

## Security

- IAM ✅
- Secrets Manager ✅
- server-side sessions ✅
- WebAuthn / passkeys ✅
- Touch ID ✅
- authenticated cloud synchronization ✅

## Observability

- OpenTelemetry ✅
- Prometheus-compatible metrics ✅
- Amazon Managed Service for Prometheus ✅
- Grafana ✅
- traces ✅
- application health monitoring ✅
- RAG-specific telemetry ✅

## FinOps

- AWS cost visibility ✅
- FinOps dashboarding ✅
- architecture/cost awareness ✅

---

# PRODUCTION EVOLUTION ROADMAP

The following items are **not required for the current interview demonstrator**.

They represent possible evolution if the platform were taken toward a larger enterprise production environment.

## Evolution A — Advanced LLM Gateway

Potential capabilities:

- dynamic model routing;
- automatic provider fallback;
- token/context policy management;
- provider quotas;
- centralized model catalog;
- prompt/model version management.

Status: Future evolution.

---

## Evolution B — Automated LLM Evaluation

Potential capabilities:

- evaluation datasets;
- answer-quality scoring;
- hallucination/grounding checks;
- regression testing;
- prompt comparison;
- quality gates in CI/CD.

Status: Future evolution.

---

## Evolution C — MCP and Agent Tooling

Potential capabilities:

- MCP-compatible tools;
- controlled tool execution;
- specialized agents;
- agent orchestration;
- authorization boundaries for tools.

Status: Future evolution.

---

## Evolution D — Extended LLMOps / MLOps

Potential capabilities:

- MLflow or equivalent lifecycle tooling;
- model registry;
- training pipelines;
- retraining workflows;
- model promotion;
- drift monitoring.

Status: Future evolution.

---

## Evolution E — Advanced Kubernetes / GPU Platform

Potential capabilities:

- production Kubernetes operations;
- GPU node pools;
- NVIDIA/CUDA workloads;
- advanced scheduling;
- autoscaling policies;
- multi-cluster governance.

Status: Future evolution.

---

## Evolution F — Resilience and Disaster Recovery

Potential capabilities:

- multi-region architecture;
- automated recovery procedures;
- backup validation;
- restore testing;
- explicit RTO/RPO objectives;
- chaos/resilience testing.

Status: Future evolution.

---

## Evolution G — Enterprise Scale Validation

Potential capabilities:

- load testing;
- concurrency testing;
- failure injection;
- capacity modelling;
- performance baselines;
- SLO/SLA definition.

Status: Future evolution.

---

## Evolution H — Security Governance

Potential capabilities:

- formal threat modelling;
- automated policy enforcement;
- vulnerability-management workflow;
- security audit trails;
- compliance controls;
- penetration testing.

Status: Future evolution.

---

# WHAT IS DELIBERATELY NOT BEING ADDED BEFORE THE INTERVIEW

The project will not add technologies simply to match job-description keywords.

No last-minute implementation of:

- GPU/CUDA;
- MLflow;
- Jenkins;
- Ansible;
- advanced MCP;
- complex multi-agent orchestration;
- production EKS;
- dynamic multi-provider model routing;
- multi-region disaster recovery.

Reason:

A coherent platform that can be explained deeply is more valuable than a larger collection of technologies that cannot be demonstrated or defended technically.

---

# FINAL PROJECT STATE

The platform has progressed from:

```text
FastAPI + PostgreSQL
```

to:

```text
Business Application
        +
AI / RAG
        +
Hybrid LLM Inference
        +
Cloud Infrastructure
        +
Security
        +
Observability
        +
FinOps
        +
Operational Control
```

The implementation phase is now frozen.

The next phase is not feature development.

It is:

```text
Understand
    ↓
Validate
    ↓
Explain
    ↓
Demonstrate
```

**Status: INTERVIEW READY / FREEZE**
