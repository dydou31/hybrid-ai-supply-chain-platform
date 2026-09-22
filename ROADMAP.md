# Hybrid AI Supply Chain Platform — Roadmap

Cette roadmap présente l'évolution complète du projet **Hybrid AI Supply Chain Platform**,
depuis la construction du backend jusqu'à une plateforme AI industrialisée et déployable
dans le cloud.

L'objectif est de construire un projet portfolio démontrant des compétences en :

- Python
- FastAPI
- Backend Engineering
- PostgreSQL
- SQLAlchemy
- Docker
- CI/CD
- Cloud
- Infrastructure as Code
- Kubernetes
- Machine Learning
- MLOps
- AI Engineering
- Full Stack Development

---

# 🟦 PHASE 0 — Positionnement du projet

## 0.1 Objectif professionnel

Positionner le projet comme démonstrateur professionnel pour les métiers :

- AI Platform Engineer
- AI Full Stack Engineer
- AI Engineer
- ML Platform Engineer
- Cloud / DevOps orienté IA

## 0.2 Définition du cas métier

Créer une plateforme de gestion Supply Chain capable de :

- gérer les fournisseurs
- gérer les produits
- gérer les commandes
- suivre les données Supply Chain
- effectuer des prévisions
- produire des scores
- classifier des données
- exposer les fonctionnalités via une API
- visualiser les données via un frontend
- industrialiser les modèles IA

## 0.3 Documentation initiale

- [x] `PROJECT_SCOPE.md`
- [x] `README.md`
- [x] `ROADMAP.md`

---

# 🟩 PHASE 1 — Fondations du projet

## 1.1 Repository

- [x] Création du repository GitHub
- [x] Configuration Git
- [x] `.gitignore`
- [x] Premier push

## 1.2 Environnement Python

- [x] Création de `.venv`
- [x] Installation de FastAPI
- [x] Installation de Uvicorn
- [x] `requirements.txt`

## 1.3 Structure du projet

Structure cible :

```text
hybrid-ai-supply-chain-platform/
│
├── app/
│   ├── core/
│   │   └── database.py
│   │
│   ├── models/
│   │   └── supplier.py
│   │
│   ├── routers/
│   │   └── suppliers.py
│   │
│   ├── schemas/
│   │   └── supplier.py
│   │
│   ├── services/
│   │   └── supplier_service.py
│   │
│   └── main.py
│
├── data/
├── docker/
├── docs/
├── kubernetes/
├── terraform/
├── tests/
│
├── alembic/
├── alembic.ini
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
├── PROJECT_SCOPE.md
└── ROADMAP.md


                    UTILISATEUR / FRONTEND
                             │
                             ▼
                  ┌──────────────────────┐
                  │   Supply Chain API   │
                  │       FastAPI        │
                  └──────────┬───────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
            ▼                ▼                ▼
       PostgreSQL        AI Engine        Monitoring
       SQLAlchemy        ML / LLM         Logs / Metrics
       Alembic           Forecast          OpenTelemetry
                          Scoring
                          Classification
            │                │
            └────────────────┼────────────────┐
                             ▼
                       Docker / Compose
                             │
                             ▼
                       GitHub Actions
                             │
                             ▼
                    Container Registry
                             │
                    ┌────────┴────────┐
                    ▼                 ▼
                  Cloud          Kubernetes
                    │                 │
                Terraform          Helm
                    │                 │
                    └────────┬────────┘
                             ▼
                           MLOps
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
          Training       Deployment      Monitoring
                                            │
                                            ▼
                                         Retraining
