# Hybrid AI Supply Chain Platform

Plateforme backend modulaire conçue comme un **démonstrateur professionnel** pour un portfolio AI Platform Engineer / Full Stack.  
Ce projet illustre ma capacité à concevoir une architecture backend moderne, extensible, documentée, cloud-ready et orientée Intelligence Artificielle.

---

## 🌐 Objectifs du projet

- Démontrer ma maîtrise de **FastAPI** et des architectures backend professionnelles  
- Construire une base technique **scalable** et **cloud-ready**  
- Intégrer des briques IA dans un backend moderne  
- Mettre en place une structure industrialisable (Docker, CI/CD, DB, monitoring)  
- Documenter le projet comme dans un contexte entreprise  
- Illustrer mes compétences pour des candidatures AI Platform Engineer / Full Stack  

---

## 🧱 Architecture du projet

hybrid-ai-supply-chain-platform/
│
├── app/
│   ├── main.py
│   ├── routers/
│   ├── services/
│   ├── models/
│   └── utils/
│
├── tests/
│
├── requirements.txt
├── Dockerfile
├── PROJECT_SCOPE.md
├── ROADMAP.md
└── README.md


---

## 🚀 Installation & Lancement

1. Cloner le projet

```bash
git clone https://github.com/dydou31/hybrid-ai-supply-chain-platform.git
cd hybrid-ai-supply-chain-platform

2. Créer l’environnement Python
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

3. Lancer l'API
uvicorn app.main:app --reload

Swagger UI :
👉 http://127.0.0.1:8000/docs

🐳 Docker
Build de l’image
docker build -t hybrid-ai-platform .

Lancer le container
docker build -t hybrid-ai-platform .

📦 Fonctionnalités actuelles
• API FastAPI fonctionnelle
• Endpoints de base : /health, /docs
• Architecture modulaire prête pour l’extension
• Documentation professionnelle (Scope + Roadmap)
• Dockerisation complète
---
🔮 Fonctionnalités à venir (Roadmap résumée)
• PostgreSQL + migrations
• Authentification JWT + RBAC
• CI/CD GitHub Actions
• Modules IA (prévisions, scoring, optimisation)
• Frontend React/Next.js
• Déploiement cloud (Azure / AWS)
• Kubernetes + Helm
• Pipelines MLOps
👉 La roadmap complète est disponible dans ROADMAP.md.
---
👤 Auteur
Dylan Taibi
AI Platform Engineering — Portfolio Project
Lamasquère, Occitanie, France