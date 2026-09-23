Hybrid AI Supply Chain Platform — Project Scope

🎯 Vision du projet

Hybrid AI Supply Chain Platform est une plateforme technique de démonstration conçue pour reproduire les problématiques rencontrées dans une équipe AI Foundation / AI Platform Engineering.

Le projet combine :

* Backend Engineering
* AI Engineering
* LLM / RAG
* Platform Engineering
* Cloud & Infrastructure
* Kubernetes
* Infrastructure as Code
* CI/CD
* Observability
* LLMOps
* Supply Chain domain knowledge

L’objectif n’est pas de construire un simple outil métier ou un dashboard, mais de démontrer la capacité à concevoir, développer, déployer, sécuriser, observer et faire évoluer une plateforme AI complète.

⸻

🧭 Objectifs principaux

1. Backend Engineering

Construire une API backend professionnelle et extensible avec :

* Python
* FastAPI
* Pydantic
* SQLAlchemy
* PostgreSQL
* Alembic
* REST API
* OpenAPI / Swagger
* validation des données
* architecture modulaire
* gestion des erreurs
* tests automatisés

L’API constitue la couche applicative de la plateforme.

⸻

2. AI Engineering

Intégrer une couche Intelligence Artificielle capable de travailler avec les données Supply Chain.

Les fonctionnalités prévues incluent :

* LLM integration
* RAG (Retrieval-Augmented Generation)
* embeddings
* vector search
* pgvector
* AI Supply Chain Assistant
* classification
* anomaly detection
* forecasting
* supplier risk scoring
* AI-assisted decision support

L’objectif est de démontrer comment une application métier peut exploiter des modèles IA au sein d’une architecture backend industrialisable.

⸻

3. AI Platform Engineering

Construire l’infrastructure permettant d’exécuter et d’exposer les services IA.

La plateforme devra progressivement intégrer :

* Docker
* Docker Compose
* Kubernetes
* Helm
* Terraform
* CI/CD
* container registry
* secrets management
* health checks
* readiness / liveness probes
* autoscaling
* configuration par environnement
* networking
* ingress
* TLS
* observabilité

L’objectif est de pouvoir déployer les composants de manière reproductible et indépendante de l’environnement.

⸻

4. LLMOps

Mettre en place les mécanismes nécessaires à l’exploitation de modèles LLM en environnement industrialisé.

Le projet pourra intégrer :

* model routing
* model fallback
* prompt management
* model evaluation
* latency monitoring
* token usage
* cost tracking
* error tracking
* AI request tracing
* model performance monitoring
* guardrails
* versioning

L’objectif est de démontrer que l’IA n’est pas uniquement appelée depuis une API, mais qu’elle peut être opérée comme un véritable composant de plateforme.

⸻

5. Cloud & Infrastructure

Construire une architecture cloud-ready et portable.

Technologies envisagées :

* AWS
* Azure
* OVHcloud
* Terraform
* Kubernetes
* Docker
* object storage compatible S3
* PostgreSQL
* networking cloud
* IAM
* secrets
* monitoring

Le projet sera développé localement puis préparé pour un déploiement cloud.

⸻

6. Observability

Mettre en place une observabilité permettant de comprendre le comportement de la plateforme.

Technologies :

* OpenTelemetry
* Prometheus
* Grafana
* structured logging
* metrics
* traces
* health checks
* application monitoring
* AI/LLM monitoring

Les métriques pourront notamment couvrir :

* API latency
* HTTP errors
* request throughput
* database performance
* LLM latency
* token consumption
* model errors
* infrastructure health

⸻

7. Security

La plateforme intégrera progressivement des mécanismes de sécurité adaptés à une architecture cloud / AI.

Prévisions :

* JWT authentication
* RBAC
* secrets management
* environment variables
* TLS
* API security
* container security
* dependency scanning
* image scanning
* IAM
* least privilege
* network isolation

⸻

🧪 Nature du projet

Ce projet est un portfolio engineering project et non un produit commercial.

Il constitue :

* une expérimentation professionnelle ;
* un démonstrateur technique ;
* une preuve de compétences ;
* une architecture de référence ;
* une plateforme AI simplifiée ;
* un support de démonstration pour des entretiens techniques.

Le domaine Supply Chain est utilisé comme cas d’usage concret afin de donner un contexte métier aux composants techniques.

⸻

🏗️ Architecture cible

                         USER / CLIENT
                              │
                              ▼
                    ┌───────────────────┐
                    │    API Gateway    │
                    │   Ingress / TLS   │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │   FastAPI API     │
                    │ Backend Services  │
                    └─────────┬─────────┘
                              │
             ┌────────────────┼────────────────┐
             │                │                │
             ▼                ▼                ▼
       PostgreSQL         AI ENGINE        Cache / Queue
       SQLAlchemy         LLM / RAG        Redis
       Alembic            pgvector
                           Forecast
                           Scoring
                           Agents
             │                │
             └────────────────┼────────────────┐
                              ▼
                    ┌───────────────────┐
                    │   Observability   │
                    │ OpenTelemetry     │
                    │ Prometheus        │
                    │ Grafana            │
                    └───────────────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │      Docker       │
                    │  Container Images │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │     CI / CD       │
                    │ GitHub Actions    │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │ Container Registry│
                    └─────────┬─────────┘
                              │
                     ┌────────┴────────┐
                     ▼                 ▼
                Kubernetes           Cloud
                     │             AWS / Azure
                     │             / OVHcloud
                     ▼
                   Helm
                     │
                     ▼
                 Terraform

⸻

🧩 Architecture applicative

app/
│
├── main.py
│
├── core/
│   ├── config.py
│   ├── security.py
│   └── logging.py
│
├── database/
│   ├── connection.py
│   └── dependencies.py
│
├── models/
│   ├── supplier.py
│   └── purchase_order.py
│
├── schemas/
│   ├── supplier.py
│   └── purchase_order.py
│
├── routers/
│   ├── suppliers.py
│   ├── purchase_orders.py
│   ├── kpis.py
│   └── ai.py
│
├── services/
│   ├── supplier_service.py
│   ├── purchase_order_service.py
│   ├── forecast_service.py
│   ├── rag_service.py
│   └── llm_service.py
│
└── ai/
    ├── embeddings.py
    ├── vector_store.py
    ├── models.py
    ├── routing.py
    └── evaluation.py

⸻

📦 Supply Chain Domain

Le domaine métier sert de cas d’usage à la plateforme.

La plateforme pourra gérer :

Suppliers

* supplier
* country
* risk level
* blocked stock
* supplier performance

Purchase Orders

* PO number
* supplier
* order date
* requested date
* confirmed date
* quantity
* unit price
* status

Supply Chain KPIs

* purchase order volume
* purchase order value
* confirmation delay
* supplier risk
* blocked stock
* supplier performance

Ces données constituent la base utilisée ensuite par les composants AI.

⸻

🤖 AI Use Cases

Les fonctionnalités IA seront progressivement construites autour de cas d’usage réalistes :

Forecasting

Prévision :

* demand
* purchase orders
* supply risk
* potential delays

Risk scoring

Calcul d’un score fournisseur basé sur :

* historical delays
* blocked stock
* order volume
* performance indicators

Anomaly detection

Détection :

* abnormal delays
* unusual order quantities
* unusual supplier behaviour
* abnormal stock situations

RAG

Permettre au LLM d’interroger :

* supplier information
* purchase orders
* Supply Chain documentation
* internal procedures
* business rules

AI Assistant

Exemple :

“Quels fournisseurs présentent actuellement le plus de risques et pourquoi ?”

Le LLM pourra récupérer les données pertinentes via les services de la plateforme avant de générer une réponse.

⸻

🌐 Frontend

Un frontend peut être ajouté afin de démontrer la dimension AI Full Stack.

Il restera volontairement secondaire par rapport à la plateforme.

Objectifs :

* interaction avec l’API
* AI assistant
* visualisation de quelques résultats
* démonstration RAG
* affichage des informations Supply Chain

Le frontend n’a pas pour objectif de devenir un projet BI ou Power BI.

⸻

🚀 Résultat attendu

À terme, le projet devra démontrer la capacité à :

* développer une API Python moderne ;
* connecter une base PostgreSQL ;
* intégrer des modèles IA ;
* construire une architecture RAG ;
* déployer des applications conteneurisées ;
* automatiser les déploiements ;
* provisionner l’infrastructure avec Terraform ;
* orchestrer les workloads avec Kubernetes ;
* observer une plateforme avec OpenTelemetry ;
* monitorer les modèles IA ;
* sécuriser les services ;
* préparer une architecture cloud ;
* faire fonctionner l’ensemble comme une plateforme cohérente.

⸻

🎯 Positionnement professionnel

Le projet est principalement orienté vers :

* AI Platform Engineer
* AI Foundation Engineer
* AI Full Stack Engineer
* AI Engineer
* ML Platform Engineer
* Cloud / DevOps Engineer orienté AI

Le projet permet également de valoriser les compétences Backend, Python, Data et Supply Chain.

⸻

🚫 Ce que le projet n’est pas

Le projet n’a pas pour objectif principal de devenir :

* un dashboard Power BI ;
* un ERP ;
* un outil SAP ;
* une simple API CRUD ;
* un notebook Machine Learning ;
* une simple application ChatGPT ;
* une infrastructure Kubernetes sans application réelle.

L’objectif est de construire une plateforme technique complète avec un cas d’usage métier concret.