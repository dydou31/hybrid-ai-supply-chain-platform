# Hybrid AI Supply Chain Platform — Roadmap

Cette roadmap présente **toutes les étapes du projet**, depuis la création initiale jusqu’aux fonctionnalités avancées (cloud, Kubernetes, MLOps).  
Elle sert de guide d’évolution et de démonstrateur pour un portfolio AI Platform Engineer / Full Stack.

---

## 🟦 1. Initialisation du projet

### 1.1 Définition du positionnement
- Définir le projet comme démonstrateur professionnel
- Définir les objectifs : architecture, IA, cloud, industrialisation
- Rédiger le fichier `PROJECT_SCOPE.md`

### 1.2 Création du dépôt GitHub
- Création du repo public
- Ajout du README minimal
- Configuration du remote
- Premier push du projet

---

## 🟩 2. Mise en place de l’environnement

### 2.1 Environnement Python
- Création du dossier projet
- Création de l’environnement `.venv`
- Installation de FastAPI + Uvicorn
- Création du fichier `requirements.txt`

### 2.2 Structure initiale du backend
- Création du dossier `app/`
- Création de `main.py`
- Création des dossiers : `routers/`, `services/`, `models/`, `utils/`
- Ajout des endpoints de base : `/health`, `/docs`

---

## 🟧 3. Documentation professionnelle

### 3.1 README professionnel
- Présentation du projet
- Architecture
- Installation
- Lancement
- Docker
- Roadmap résumée
- Auteur

### 3.2 Documentation API
- OpenAPI automatique via FastAPI
- Organisation claire des modules

---

## 🟨 4. Modules métier (Supply Chain)

### 4.1 CRUD Fournisseurs
### 4.2 CRUD Produits
### 4.3 CRUD Commandes
### 4.4 Module Monitoring
- Logs
- Metrics
- Health-checks avancés

---

## 🟪 5. Intégration IA (démonstrateur)

### 5.1 Prévisions
- Endpoint de prévision simple (mock ou modèle léger)

### 5.2 Scoring
- Endpoint de scoring (mock ou modèle léger)

### 5.3 Classification
- Endpoint de classification (mock ou modèle léger)

---

## 🟥 6. Dockerisation complète

### 6.1 Dockerfile
### 6.2 .dockerignore
### 6.3 Build de l’image
### 6.4 Run du container
### 6.5 Tests de l’API dans Docker

---

## 🟫 7. Industrialisation (CI/CD)

### 7.1 GitHub Actions
- Build automatique
- Tests automatiques
- Linting
- Analyse de sécurité

### 7.2 Docker Hub (optionnel)
- Push automatique de l’image

---

## 🟦 8. Base de données (PostgreSQL)

### 8.1 Ajout SQLAlchemy
### 8.2 Ajout Alembic (migrations)
### 8.3 docker-compose
### 8.4 Connexion FastAPI ↔ PostgreSQL
### 8.5 Tests des endpoints

---

## 🟩 9. Authentification & Sécurité

### 9.1 JWT
### 9.2 RBAC (rôles)
### 9.3 Gestion des utilisateurs
### 9.4 Sécurisation des endpoints

---

## 🟧 10. Frontend (optionnel mais puissant pour portfolio)

### 10.1 Création d’un frontend React/Next.js
### 10.2 Dashboard
### 10.3 Pages fournisseurs / IA / monitoring
### 10.4 Connexion à l’API FastAPI

---

## 🟨 11. Déploiement cloud

### 11.1 Choix du cloud (Azure / AWS)
### 11.2 Déploiement Docker
### 11.3 Load balancer
### 11.4 Monitoring cloud
### 11.5 Secret manager

---

## 🟪 12. Kubernetes (niveau avancé)

### 12.1 Manifests Kubernetes
### 12.2 Charts Helm
### 12.3 Déploiement sur AKS / EKS
### 12.4 Autoscaling
### 12.5 Monitoring Prometheus + Grafana

---

## 🟥 13. MLOps (niveau expert)

### 13.1 Pipelines de training
### 13.2 Pipelines de retraining
### 13.3 Monitoring des modèles
### 13.4 Versioning des modèles
### 13.5 Déploiement des modèles

---

## 🟫 14. Vision long terme

- Plateforme complète IA + Supply Chain
- Architecture cloud-native
- Microservices
- Observabilité avancée
- Automatisation des flux Supply Chain
- Intégration ERP/WMS
