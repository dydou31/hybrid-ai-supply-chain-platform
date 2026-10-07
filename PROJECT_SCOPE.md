# PROJECT SCOPE — Hybrid AI Supply Chain Platform

## 1. Purpose

The Hybrid AI Supply Chain Platform is a production-oriented engineering demonstrator built around a concrete Supply Chain use case.

Its purpose is to demonstrate how a business application can evolve into a coherent AI platform covering:

- backend and API engineering;
- relational and vector data;
- AI and Retrieval-Augmented Generation;
- local and cloud inference;
- containerization and orchestration;
- infrastructure as code;
- cloud deployment and autoscaling;
- security and strong authentication;
- observability and AI telemetry;
- cloud cost visibility;
- CI/CD and operational control.

The project deliberately connects application engineering and platform engineering instead of treating AI as an isolated feature.

---

## 2. Scope Philosophy

The project follows four principles.

### Business first

Technology is introduced to solve a concrete problem rather than to create an artificial technology showcase.

The domain is Supply Chain because it provides realistic operational entities, KPIs and decision-support scenarios.

### End-to-end engineering

The scope extends beyond an AI proof of concept.

The system includes the layers required to build, run, secure, observe and operate the application.

### Hybrid by design

Local development and AWS deployment are intentionally separated while sharing the same application concepts.

Local inference uses Ollama. Cloud inference uses Amazon Bedrock.

### Honest production orientation

The project implements and demonstrates production-oriented patterns, but does not claim to reproduce the scale, organizational processes or operational history of a large enterprise production platform.

---

## 3. Functional Scope

### Supply Chain Domain

The business layer covers operational Supply Chain information such as:

- suppliers;
- deliveries / purchasing-related operational data;
- supplier risk;
- delivery performance;
- delayed deliveries;
- average delay;
- delay rate;
- blocked stock;
- supplier prioritization;
- operational KPIs.

The domain exists to provide realistic data and decisions for the platform.

The project is not intended to become an ERP, SAP replacement or BI suite.

---

## 4. Backend and API Scope

The backend is implemented in Python with FastAPI.

In scope:

- REST endpoints;
- CRUD operations;
- request/response validation;
- Supply Chain business logic;
- KPI computation;
- database access;
- AI query endpoints;
- platform health endpoints;
- authentication integration;
- observability instrumentation;
- Swagger / OpenAPI documentation.

The backend is intended to remain modular so business logic, data access and AI orchestration can evolve independently.

---

## 5. Data Scope

### PostgreSQL

PostgreSQL is the primary persistence technology.

It stores structured operational data and supports the AI knowledge layer.

### SQLAlchemy and Alembic

SQLAlchemy provides database access and Alembic manages schema migrations.

### pgvector

pgvector provides vector storage and similarity search inside PostgreSQL.

Current semantic embeddings use 384 dimensions.

This is a deliberate architectural choice: the current project does not require a separate dedicated vector database.

---

## 6. AI Scope

The AI layer is focused on decision support rather than autonomous business execution.

### Structured Retrieval

Operational facts and KPIs are retrieved deterministically from the application/database layer.

Examples include:

- supplier risk;
- delivery delays;
- blocked stock;
- performance indicators;
- supplier prioritization.

The LLM is not expected to calculate authoritative business data from memory.

### Semantic Retrieval

Unstructured knowledge is embedded and retrieved using pgvector similarity search.

This enables retrieval of relevant documentation or knowledge for a natural-language question.

### Combined RAG

The RAG pipeline can combine:

1. the user question;
2. structured Supply Chain facts;
3. semantically retrieved knowledge;
4. LLM reasoning.

The intended result is an explainable decision-support response grounded in platform data.

---

## 7. LLM Inference Scope

Two inference environments are supported.

### Local

Ollama is used for local inference and development.

Current local model:

`llama3.2:3b`

### AWS

Amazon Bedrock is used for managed cloud inference.

The provider is selected through configuration, keeping inference infrastructure separated from core business logic.

### Explicit limitation

The project does not claim to implement a complete enterprise model gateway with advanced dynamic routing, automatic multi-provider fallback, quota arbitration or a full model catalog.

Those are production evolution topics.

---

## 8. Full-Stack Scope

The project includes a web application layer and a platform Control Center.

In scope:

- interaction with backend APIs;
- Supply Chain information;
- AI interaction;
- platform status;
- local/cloud operational visibility;
- authentication flows;
- cloud synchronization controls;
- observability and FinOps visibility.

The frontend is intentionally functional and engineering-oriented.

It is not intended to become a Power BI replacement or a design-heavy consumer product.

---

## 9. Local Platform Scope

The local environment uses Docker and Docker Compose.

In scope:

- reproducible service startup;
- PostgreSQL;
- pgvector;
- application services;
- Ollama;
- local observability components;
- platform health inspection;
- Control Center integration.

The local environment is optimized for development, experimentation and demonstration.

---

## 10. Kubernetes Scope

Kubernetes is included to demonstrate container orchestration concepts and platform portability.

Relevant concepts include:

- deployments;
- services;
- container scheduling;
- workload isolation;
- horizontal scaling concepts;
- declarative deployment.

The project does not claim:

- operation of a large production Kubernetes estate;
- GPU/CUDA scheduling;
- multi-cluster management;
- enterprise Kubernetes governance;
- long-term production SRE experience.

The deployed AWS architecture currently uses ECS Fargate rather than EKS.

This is intentional.

---

## 11. AWS Scope

The AWS environment demonstrates a production-oriented cloud architecture.

In scope:

- CloudFront;
- Application Load Balancer;
- ECS Fargate;
- RDS PostgreSQL;
- pgvector;
- Valkey;
- Amazon Bedrock;
- AWS Secrets Manager;
- IAM;
- networking and service isolation;
- managed observability components;
- autoscaling.

### ECS scaling

Current application scaling configuration:

- minimum tasks: 2;
- maximum tasks: 4;
- target CPU utilization: 60%;
- task CPU: 512;
- task memory: 2048 MB.

This demonstrates redundancy and horizontal autoscaling without claiming enterprise-scale traffic validation.

---

## 12. Hybrid Local-to-AWS Scope

The project explicitly demonstrates a hybrid workflow.

Local:

- FastAPI;
- PostgreSQL / pgvector;
- Ollama;
- Docker;
- local observability;
- Control Center.

AWS:

- ECS Fargate;
- RDS PostgreSQL / pgvector;
- Valkey;
- Bedrock;
- cloud observability.

Local-to-cloud synchronization is protected rather than exposed as an unrestricted operation.

This architecture demonstrates how local AI development can coexist with a controlled cloud runtime.

---

## 13. Security Scope

Security is part of the architecture.

Implemented or demonstrated controls include:

- AWS IAM;
- AWS Secrets Manager;
- server-side sessions;
- WebAuthn;
- passkeys;
- Touch ID on supported Apple devices;
- authenticated cloud operations;
- protected local-to-AWS synchronization;
- cloud network separation and access controls.

The project does not claim formal certification, penetration testing or enterprise security accreditation.

---

## 14. Observability Scope

Observability covers both conventional application telemetry and AI-specific execution.

In scope:

- OpenTelemetry;
- Prometheus-compatible metrics;
- Amazon Managed Service for Prometheus;
- Grafana;
- tracing;
- health checks;
- RAG metrics;
- AI pipeline spans.

Examples of AI metrics include:

- `rag_requests_total`;
- `rag_errors_total`;
- `rag_request_duration_seconds`.

Relevant trace operations include semantic search, embedding generation, pgvector search and LLM inference.

The objective is to avoid treating the AI pipeline as a black box.

---

## 15. FinOps Scope

Cloud cost awareness is included as an operational concern.

The project includes FinOps visibility intended to connect:

- AWS services;
- resource usage;
- infrastructure architecture;
- AI/cloud consumption;
- operational cost.

The goal is visibility and engineering awareness, not a complete enterprise financial-management platform.

---

## 16. Infrastructure as Code

Terraform manages the AWS infrastructure.

In scope:

- version-controlled infrastructure;
- reproducible provisioning;
- explicit dependencies;
- reviewable cloud changes;
- AWS application infrastructure;
- observability infrastructure.

Terraform definitions are stored under `terraform/aws/`.

---

## 17. CI/CD Scope

GitHub Actions provides CI/CD automation.

The pipeline complements:

- application development;
- automated validation;
- container workflows;
- infrastructure delivery practices.

The project demonstrates the delivery lifecycle without claiming to reproduce a large organization's approval, release-management or change-management processes.

---

## 18. Platform Control Center

The Control Center is the operational convergence point of the project.

It exposes or consolidates visibility into multiple layers:

- application;
- database;
- vector capabilities;
- LLM services;
- containers;
- authentication;
- observability;
- cloud synchronization;
- AWS services;
- FinOps.

Its role is to make the platform understandable and operable from a coherent interface.

---

## 19. Explicitly Out of Scope

The current project does not claim to provide:

- a full ERP or SAP replacement;
- a complete BI platform;
- large-scale production Kubernetes operations;
- NVIDIA GPU / CUDA workload scheduling;
- enterprise multi-cloud orchestration;
- MLflow-based model lifecycle management;
- complete ML training and automated retraining pipelines;
- a complete enterprise prompt/model registry;
- advanced dynamic model routing and automatic provider fallback;
- a complete MCP / multi-agent ecosystem;
- autonomous execution of critical Supply Chain decisions;
- complete multi-region disaster recovery;
- enterprise-scale load validation;
- formal security certification;
- years of production operational history.

These limitations are deliberate and should not be represented as implemented functionality.

---

## 20. Production Evolution

Natural next steps for a larger production platform include:

- advanced model routing and fallback;
- prompt and model version management;
- automated LLM evaluation;
- MCP and agent tooling;
- deeper LLMOps / MLOps capabilities;
- GPU-enabled workloads where justified;
- advanced Kubernetes operations;
- multi-region resilience;
- disaster recovery automation;
- enterprise load and resilience testing;
- expanded security governance;
- richer cost optimization.

These are extensions of the current architecture, not requirements for the interview demonstrator.

---

## 21. Current Project State

**Status: INTERVIEW FREEZE**

The implementation is frozen.

Allowed work during the freeze:

- documentation;
- architecture review;
- demo preparation;
- validation of existing functionality;
- interview preparation.

Not planned during the freeze:

- new infrastructure;
- new platform features;
- speculative technologies added only to match job-description keywords;
- risky refactoring.

The objective is now to demonstrate and explain the existing platform clearly and accurately.

---

## 22. Professional Positioning

The platform deliberately crosses several engineering domains:

- backend engineering;
- full-stack AI application engineering;
- AI / RAG engineering;
- AI platform engineering;
- cloud/platform engineering;
- DevOps / infrastructure as code;
- observability;
- security;
- FinOps.

The project does not attempt to claim expert-level production experience in every one of these areas.

Its value is the ability to connect them into one working, understandable system around a real business use case.

---

## 23. Definition of Success

The project is successful if it demonstrates the ability to explain and operate the complete path:

```text
Business problem
      ↓
Operational data
      ↓
FastAPI / APIs
      ↓
PostgreSQL
      ↓
Docker
      ↓
Full-stack application
      ↓
RAG / pgvector
      ↓
Local and cloud LLM inference
      ↓
Cloud infrastructure
      ↓
Security
      ↓
Observability
      ↓
FinOps
      ↓
Operational Control Center
```

The key outcome is not the number of technologies used.

It is the coherence between the business problem, the AI application and the platform required to operate it.
