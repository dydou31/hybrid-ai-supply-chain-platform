Hybrid AI Supply Chain Platform — Roadmap

Cette roadmap décrit l’évolution du projet depuis une API Supply Chain fonctionnelle vers une AI Platform industrialisée, observable, sécurisée et déployable dans le cloud.

L’objectif principal est de construire progressivement les compétences nécessaires pour des rôles :

* AI Platform Engineer
* AI Foundation Engineer
* AI Full Stack Engineer
* AI Engineer
* ML Platform Engineer
* Cloud / DevOps Engineer orienté IA

⸻

🟦 PHASE 0 — Positionnement

Objectif

Définir le projet comme une plateforme AI et non comme une simple application Supply Chain.

Cas d’usage

La Supply Chain constitue le domaine métier permettant de démontrer :

* gestion des fournisseurs ;
* gestion des commandes ;
* suivi des risques ;
* analyse des retards ;
* données structurées ;
* données documentaires ;
* prédiction ;
* interaction avec un LLM.

Documentation

* PROJECT_SCOPE.md
* README.md
* ROADMAP.md

⸻

🟩 PHASE 1 — Backend Foundation

Objectif

Construire une API backend professionnelle.

Python

* Python environment
* virtual environment
* requirements.txt

FastAPI

* FastAPI application
* OpenAPI
* Swagger
* health endpoint
* modular routers

Database

* PostgreSQL
* Docker PostgreSQL
* SQLAlchemy
* Alembic
* migrations
* foreign keys

Domain models

* Supplier
* Purchase Order
* Supplier risk
* Blocked stock
* PO status

Validation

* Pydantic schemas
* Enum validation
* Numeric validation
* Date validation
* Foreign key validation

API

* Supplier CRUD
* Purchase Order endpoints
* KPI endpoint

⸻

🟨 PHASE 2 — Backend Engineering

Objectif

Passer d’une API fonctionnelle à une API réellement industrialisable.

Architecture

* service layer
* repository pattern where useful
* centralized configuration
* dependency management
* error handling
* structured logging

API

* pagination
* filtering
* sorting
* API versioning
* consistent response models

Security

* JWT authentication
* RBAC
* protected endpoints
* secrets through environment variables

Tests

* pytest
* unit tests
* integration tests
* API tests
* database test environment

⸻

🐳 PHASE 3 — Containerization

Objectif

Faire fonctionner l’application comme une véritable application containerisée.

Docker

* Dockerfile
* optimized image
* non-root container
* environment configuration
* healthcheck

Docker Compose

* PostgreSQL container
* FastAPI container
* API + PostgreSQL networking
* persistent volumes
* environment configuration

Architecture

Docker Compose
│
├── FastAPI
│
├── PostgreSQL
│
└── future AI services

⸻

🔄 PHASE 4 — CI/CD

Objectif

Automatiser la validation et la livraison du projet.

GitHub Actions

* lint
* unit tests
* integration tests
* build Docker image
* security checks
* push image to registry

Pipeline

Git Push
   │
   ▼
GitHub Actions
   │
   ├── Lint
   ├── Tests
   ├── Security
   └── Docker Build
           │
           ▼
    Container Registry

Release

* versioning
* release tags
* image tags
* deployment workflow

⸻

🤖 PHASE 5 — AI Foundation

Objectif

Introduire une véritable couche AI dans la plateforme.

LLM Integration

* LLM API
* OpenAI-compatible API interface
* configuration through environment variables
* async requests
* error handling
* timeout management

AI Service

Créer un service indépendant :

app/
└── ai/
    ├── llm.py
    ├── routing.py
    ├── prompts.py
    └── evaluation.py

Supply Chain AI Assistant

Exemples :

"Quels fournisseurs présentent actuellement
un risque élevé ?"
"Quelles commandes présentent un retard ?"
"Quel fournisseur représente le plus gros
montant de commandes à risque ?"

⸻

📚 PHASE 6 — RAG & Vector Search

Objectif

Construire une architecture Retrieval-Augmented Generation.

Vector Database

* pgvector
* embeddings
* vector storage
* similarity search

Documents

Ingestion de :

* Supply Chain procedures
* supplier documentation
* business rules
* purchasing policies
* technical documentation

RAG Pipeline

Document
   │
   ▼
Chunking
   │
   ▼
Embedding
   │
   ▼
pgvector
   │
   ▼
User Question
   │
   ▼
Similarity Search
   │
   ▼
Relevant Context
   │
   ▼
LLM
   │
   ▼
Answer

RAG Quality

* retrieval evaluation
* relevance evaluation
* hallucination checks
* prompt versioning

⸻

📈 PHASE 7 — Supply Chain AI

Objectif

Ajouter des modèles ML/AI ayant une vraie utilité métier.

Forecasting

* demand forecasting
* order forecasting
* delay forecasting

Risk Scoring

* supplier risk score
* PO risk score
* blocked-stock risk

Anomaly Detection

* abnormal order quantity
* abnormal delay
* supplier anomalies
* stock anomalies

ML Pipeline

Data
 │
 ▼
Feature Engineering
 │
 ▼
Training
 │
 ▼
Validation
 │
 ▼
Model Registry
 │
 ▼
Deployment
 │
 ▼
Inference

⸻

👁️ PHASE 8 — Observability

Objectif

Observer la plateforme et ses composants AI.

OpenTelemetry

* application traces
* request tracing
* database traces
* AI request traces

Metrics

* API latency
* request rate
* HTTP errors
* database latency
* container health

AI Metrics

* LLM latency
* token usage
* model errors
* request volume
* estimated AI cost

Prometheus

* Prometheus deployment
* application metrics
* infrastructure metrics

Grafana

* infrastructure dashboard
* API dashboard
* AI dashboard

Le dashboard ici est un outil d’observabilité technique, pas un dashboard BI métier.

⸻

☸️ PHASE 9 — Kubernetes

Objectif

Déployer la plateforme dans un environnement orchestré.

Kubernetes fundamentals

* Pods
* Deployments
* Services
* ConfigMaps
* Secrets
* Namespaces
* Ingress
* Persistent Volumes

Application

Kubernetes Cluster
│
├── FastAPI
│
├── AI Service
│
├── PostgreSQL
│
├── Redis
│
└── Observability
    ├── Prometheus
    └── Grafana

Reliability

* liveness probes
* readiness probes
* resource requests
* resource limits
* horizontal scaling

Advanced

* Horizontal Pod Autoscaler
* rolling deployments
* zero-downtime deployment
* configuration management

⸻

⛵ PHASE 10 — Helm

Objectif

Transformer les manifests Kubernetes en package déployable.

* Helm chart
* values.yaml
* environment-specific values
* configurable replicas
* configurable resources
* configurable image versions

Architecture :

Helm
 │
 ├── Development
 ├── Staging
 └── Production

⸻

🏗️ PHASE 11 — Terraform / Infrastructure as Code

Objectif

Provisionner l’infrastructure de manière reproductible.

Terraform

* provider configuration
* variables
* outputs
* modules
* state management

Infrastructure

Selon l’environnement choisi :

* networking
* compute
* Kubernetes cluster
* PostgreSQL
* object storage
* IAM
* security groups

Architecture

Terraform
   │
   ├── Network
   ├── Compute
   ├── Kubernetes
   ├── Database
   ├── Storage
   └── IAM

⸻

☁️ PHASE 12 — Cloud Deployment

Objectif

Déployer réellement la plateforme dans le cloud.

Environnement possible :

* AWS
* Azure
* OVHcloud

Cloud components

* Kubernetes
* PostgreSQL
* Object Storage
* Container Registry
* IAM
* Networking
* Secrets
* Monitoring

Environnement

Local
  │
  ▼
Docker Compose
  │
  ▼
Kubernetes
  │
  ▼
Cloud

⸻

🔐 PHASE 13 — Security Engineering

Objectif

Ajouter les mécanismes de sécurité nécessaires à une plateforme AI.

Application Security

* JWT
* RBAC
* API authentication
* authorization
* input validation
* rate limiting

Container Security

* non-root containers
* dependency scanning
* image scanning
* vulnerability management

Infrastructure Security

* secrets management
* IAM
* least privilege
* network isolation
* TLS
* private networking

⸻

🧠 PHASE 14 — LLMOps

Objectif

Passer d’une simple intégration LLM à une plateforme capable d’opérer plusieurs modèles.

Model Routing

                 AI REQUEST
                     │
                     ▼
                LLM Router
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
        Model A    Model B    Model C
          │          │          │
          └──────────┼──────────┘
                     ▼
                  Response

Routing

* model selection
* fallback
* retry
* timeout
* provider abstraction

Evaluation

* prompt evaluation
* response evaluation
* RAG evaluation
* regression tests

Monitoring

* latency
* token usage
* cost
* errors
* model performance

⸻

🔁 PHASE 15 — MLOps

Objectif

Industrialiser les modèles Machine Learning.

Training

* training pipeline
* dataset versioning
* feature engineering
* experiment tracking

Model lifecycle

Data
 │
 ▼
Training
 │
 ▼
Validation
 │
 ▼
Model Registry
 │
 ▼
Deployment
 │
 ▼
Monitoring
 │
 ▼
Retraining

Monitoring

* model performance
* data drift
* prediction drift
* retraining triggers

⸻

🖥️ PHASE 16 — AI Full Stack Layer

Objectif

Ajouter une interface légère permettant de démontrer la partie Full Stack du projet.

Le frontend ne constitue pas le cœur de la plateforme.

Fonctionnalités

* API integration
* Supply Chain overview
* AI assistant
* RAG interaction
* supplier information
* PO information
* AI results

Architecture

Frontend
   │
   ▼
FastAPI
   │
   ├── PostgreSQL
   ├── AI Engine
   └── RAG

⸻

🧪 PHASE 17 — Testing & Quality

Objectif

Garantir la fiabilité de la plateforme.

Tests

* unit tests
* integration tests
* API tests
* database tests
* AI evaluation tests
* RAG tests

Quality

* linting
* formatting
* type checking
* dependency checks
* security scanning

CI

Commit
 │
 ▼
Lint
 │
 ▼
Type Check
 │
 ▼
Tests
 │
 ▼
Security Scan
 │
 ▼
Docker Build
 │
 ▼
Registry

⸻

📖 PHASE 18 — Documentation

Objectif

Documenter le projet comme un projet d’entreprise.

Documentation

* README
* PROJECT_SCOPE
* ROADMAP
* Architecture documentation
* API documentation
* Deployment documentation
* Kubernetes documentation
* Terraform documentation
* AI architecture documentation
* RAG documentation
* LLMOps documentation

Architecture Decision Records

* ADR — FastAPI
* ADR — PostgreSQL
* ADR — Kubernetes
* ADR — Terraform
* ADR — Vector database
* ADR — LLM architecture

⸻

🏁 FINAL TARGET ARCHITECTURE

                              USER
                               │
                               ▼
                         API Gateway
                         Ingress / TLS
                               │
                               ▼
                    ┌────────────────────┐
                    │      FastAPI       │
                    │    Application     │
                    └─────────┬──────────┘
                              │
             ┌────────────────┼────────────────┐
             │                │                │
             ▼                ▼                ▼
        PostgreSQL        AI Platform       Redis
             │                │
             │          ┌─────┼─────┐
             │          │     │     │
             │         LLM   RAG  ML/AI
             │          │     │     │
             │          └─────┼─────┘
             │                │
             └────────────────┘
                              │
                       Observability
                              │
               ┌──────────────┼──────────────┐
               ▼              ▼              ▼
          OpenTelemetry   Prometheus       Grafana
                             
                              │
                       Kubernetes
                              │
                         Helm Charts
                              │
                         Terraform
                              │
                         Cloud Provider
                              │
                     AWS / Azure / OVHcloud

⸻

🎯 Final Portfolio Outcome

À la fin de la roadmap, le projet devra permettre de démontrer :

Backend

* Python
* FastAPI
* PostgreSQL
* SQLAlchemy
* REST
* API architecture

AI

* LLM
* RAG
* vector search
* embeddings
* ML
* forecasting
* anomaly detection
* AI agents

Platform

* Docker
* Kubernetes
* Helm
* Terraform
* CI/CD
* container registry

Cloud

* networking
* IAM
* storage
* compute
* managed services

LLMOps / MLOps

* model routing
* evaluation
* monitoring
* model lifecycle
* retraining

Observability

* OpenTelemetry
* Prometheus
* Grafana
* logs
* metrics
* traces

Security

* authentication
* authorization
* secrets
* TLS
* IAM
* container security

⸻

🚀 Priorité d’exécution

Pour éviter de construire 50 choses en même temps, l’ordre réel d’implémentation sera :

1. Backend API                 ✅
2. PostgreSQL / Alembic       ✅
3. Supply Chain models        ✅
4. KPI API                    ✅
5. Docker API                 ← NEXT
6. Tests
7. CI/CD
8. AI / LLM
9. RAG / pgvector
10. Observability
11. Kubernetes
12. Helm
13. Terraform
14. Cloud
15. LLMOps
16. Security hardening
17. Full Stack demo

L’objectif est d’obtenir progressivement une plateforme fonctionnelle → containerisée → automatisée → AI-enabled → observable → orchestrée → cloud-ready.