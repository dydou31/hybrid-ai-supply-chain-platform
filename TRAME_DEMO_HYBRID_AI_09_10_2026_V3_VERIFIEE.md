# HYBRID AI SUPPLY CHAIN PLATFORM
**Technical Demo | AUMOVIO | 09.10.2026**

**Statut : sections 00–08 mises à jour à partir des vérifications réalisées. Sections 09–14 : à vérifier avant utilisation.**


## 00 — Introduction | 1 min
**Repères** · Material Planning · Fournisseurs · Commandes · Retards · Risques · Stock bloqué · Aide à la décision · Plateforme Full Stack construite de bout en bout.

## 01 — Environnement local | 1 min
**Terminal**
```bash
demo
docker compose ps
api
```
**Repères** · Docker Compose · FastAPI · PostgreSQL/pgvector · Redis · Prometheus · Tempo · Grafana.

## 02 — Swagger | Gestion fournisseurs | 3 min
**Navigateur — Swagger UI**

| Ordre | Opération | Action |
|---|---|---|
| 1 | `GET /suppliers` | Consulter les fournisseurs |
| 2 | `POST /suppliers` | Créer un fournisseur de démonstration |
| 3 | `PUT /suppliers/{supplier_id}` | Passer le risque de `low` à `high` |
| 4 | `GET /suppliers` | Vérifier la modification |

**POST — Création**
```json
{
  "name": "AUMOVIO Interview Supplier",
  "country": "France",
  "risk_level": "low",
  "blocked_stock_eur": 15000
}
```
**ID retourné :** __________ (à conserver)

**PUT — Mise à jour** (reprendre cet ID)
```json
{
  "name": "AUMOVIO Interview Supplier",
  "country": "France",
  "risk_level": "high",
  "blocked_stock_eur": 25000
}
```
**Repères** · API REST · CRUD · HTTP · Validation · Risque fournisseur. **Ne pas supprimer le fournisseur.**

## 03 — PostgreSQL | Persistance | 1 min
**Terminal — vérification de la création et de la modification**
```bash
docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT id, name, country, risk_level, blocked_stock_eur FROM suppliers WHERE name = '\''AUMOVIO Interview Supplier'\'' ORDER BY id DESC LIMIT 3;"'
```
**Repères** · FastAPI → SQLAlchemy → PostgreSQL · Persistance · Risque `high` · Stock bloqué `25000`.

## 04 — Frontend LOCAL | React + TypeScript | 4 min
**Navigateur**
```bash
open http://localhost:5173/
```
docker compose stop redis

| Écran | Parcours / mots-clés |
|---|---|
| **Dashboard** | KPI · Fournisseurs actifs · Stock bloqué · Risques élevés · Documents IA · Santé des services |
| **Suppliers** | Recherche du fournisseur créé · Risque `high` · `25 000 €` · Connexion API / base |
| **AI Assistant** | Question métier · Réponse structurée · PostgreSQL (**structured**) · pgvector (**semantic**) · RAG · Ollama / Llama · Sources · Score de similarité sémantique |
| **Platform** | État des workloads · FastAPI · PostgreSQL · Redis · Prometheus · Grafana · Tempo · Ollama |

**Question IA de démonstration** : `Quel est le meilleur fournisseur et pourquoi ?`

**Repères IA** · Données structurées = indicateurs SQL · Documents sémantiques = textes retrouvés par embeddings · Similarité ≠ fiabilité de la réponse.

## 05 — Kubernetes | Orchestration et auto-healing | 3 min
**Terminal — démarrer Minikube si nécessaire**
```bash
minikube status
```
Si l'état est `Stopped` :
```bash
minikube start
```
**Terminal — pods du namespace de démonstration**
```bash
kubectl get pods -n hybrid-ai
```
**Terminal — auto-healing testé : suppression du Pod API uniquement**
```bash
kubectl delete pod -n hybrid-ai -l app=hybrid-ai-api
```
**Terminal — constater la recréation automatique**
```bash
kubectl get pods -n hybrid-ai -w
```
Arrêter l'observation avec `Ctrl+C` après avoir vu un **nouveau Pod API `1/1 Running`**. PostgreSQL et Redis ne sont pas supprimés.

**À dire** · « Je supprime volontairement mon Pod API. Kubernetes détecte sa disparition et en recrée automatiquement un pour maintenir l'état souhaité. »

**Helm — montrer les fichiers de configuration (lecture seule)**
```bash
find . -maxdepth 5 \( -name 'Chart.yaml' -o -name 'values.yaml' \) -not -path '*/node_modules/*'
```
**Repères** · Minikube · Kubernetes Deployment · Pod · Réconciliation automatique · Helm. **Une réplique ne garantit pas zéro interruption.**

## 06 — Terraform | Infrastructure as Code | 1 min
**Terminal — ressources AWS réellement gérées (commande testée)**
```bash
terraform -chdir=terraform/aws state list
```
**À dire** · « Terraform me permet de définir et de gérer mon infrastructure AWS directement dans du code. »

**Repères** · ECS · RDS · ALB · CloudFront · Réseau · IAM · Auto Scaling · Infrastructure as Code. **Ne pas lancer `terraform apply` pendant l'entretien.**

## 07 — Résilience locale | Redis DOWN / UP | 2 min
**Navigateur LOCAL — Dashboard / Control Center**

**Terminal — simuler la panne (testé)**
```bash
docker compose stop redis
```
**À montrer** · Redis **Unavailable** et Platform Health **Degraded** sur le Dashboard local.

**Control Center LOCAL — restauration manuelle testée** · Redémarrer Redis depuis le contrôle de service de l'interface, puis constater **Redis Running** et **Platform Health Healthy**.

**Commande de secours également testée**
```bash
docker compose start redis
```
**À dire** · « Ma plateforme détecte la panne de Redis et permet de redémarrer le service directement depuis l'interface. »

**Repères** · Détection · Pilotage · Rétablissement manuel. **Ce n'est pas l'auto-healing Kubernetes montré à l'étape 05.**

## 08 — AWS | Connexion, frontend et synchronisation | 4 min
**Terminal — service ECS Fargate (commande et sortie vérifiées)**
```bash
AWS_PROFILE=hybrid-ai-terraform aws ecs describe-services --cluster hybrid-ai-cluster --services hybrid-ai-api-service --region eu-west-3 --query 'services[].{Service:serviceName,Desired:desiredCount,Running:runningCount,Pending:pendingCount}' --output table
```
**Sortie constatée à la répétition** · `Desired 2` · `Running 2` · `Pending 0`. **Cette commande vérifie l'accès AWS et l'état ECS ; elle ne teste pas la réponse HTTP de l'API.**

**À dire** · « Jusqu'ici, je vous ai montré ma plateforme en local. Elle est également déployée sur AWS avec ECS Fargate. Deux tâches sont actuellement en fonctionnement. »

**Navigateur — frontend CLOUD** · `https://dw3e18cneqohd.cloudfront.net/` → **Suppliers**.

**Fil rouge — synchronisation depuis l'interface (sans commande Terminal)**
1. **LOCAL Swagger** · Le fournisseur `AUMOVIO Interview Supplier` est créé (`low`, `15 000 €`), puis modifié (`high`, `25 000 €`) à l'étape 02.
2. **LOCAL Frontend** · Vérifier sa présence et ses nouvelles valeurs.
3. **CLOUD Frontend / Suppliers** · Vérifier son absence avant synchronisation.
4. **Control Center** · Déclencher la synchronisation **LOCAL → AWS** depuis l'interface prévue à cet effet.
5. **CLOUD Frontend / Suppliers** · Actualiser et retrouver le fournisseur avec `high` et `25 000 €`.

**Préparation effectuée** · Le fournisseur de test précédent a été supprimé côté AWS (ID `168`, vérifié avant suppression), puis côté local via Swagger. **Les ID changent lors des créations : ne pas réutiliser 168 pendant l'entretien.**

**À dire** · « Je crée et modifie mes données en local, puis je les synchronise vers AWS depuis mon interface. Je vérifie ensuite le résultat sur le frontend cloud. »

**Statut de validation** · La présence du fournisseur AWS et la suppression ciblée ont été contrôlées ; **le nouveau cycle complet de synchronisation depuis l'interface reste à revérifier avant l'entretien**. Ne pas le présenter comme déjà testé de bout en bout.

---

**SUITE — étapes 09–14 conservées de la version précédente, non revérifiées dans cette session.**

## 09 — Auto-healing AWS ECS | 3 min

### Objectif
Démontrer qu'AWS ECS Fargate remplace automatiquement une tâche arrêtée afin de maintenir la haute disponibilité de l'application.

### 1. Vérifier l'état initial
```bash
healcheck
```
**Résultat attendu :** Desired = 2 | Running = 2 | Pending = 0.

### 2. Arrêter volontairement une tâche ECS
```bash
healstop
```
**Action :** Arrête automatiquement une tâche AWS sans avoir à rechercher son identifiant.

### 3. Observer le remplacement automatique
```bash
healcheck
```
**Résultat possible :** Desired = 2 | Running = 1 | Pending = 1.

### 4. Consulter les événements ECS
```bash
AWS_PROFILE=hybrid-ai-terraform aws ecs describe-services --cluster hybrid-ai-cluster --services hybrid-ai-api-service --region eu-west-3 --query 'services[0].events[:10].[createdAt,message]' --output table
```
**À montrer :** Démarrage d'une nouvelle tâche et enregistrement auprès du Load Balancer.

### 5. Confirmer le retour à deux tâches
```bash
healcheck
```
**Résultat attendu :** Desired = 2 | Running = 2 | Pending = 0.

### Présentation orale
> « Je viens de simuler une panne en arrêtant volontairement une tâche ECS. AWS détecte sa disparition et lance automatiquement une nouvelle instance pour maintenir les deux tâches configurées, sans intervention manuelle. »

**Repères :** AWS ECS Fargate · Auto-healing · Application Load Balancer · Health Checks · Haute disponibilité.

---

## 10 — Autoscaling AWS ECS | 4–6 min

### Objectif
Démontrer qu'AWS adapte automatiquement le nombre de tâches ECS en fonction de la charge CPU.

**Configuration :** Minimum 2 tâches · Maximum 4 tâches · CPU cible 60 %.

### 1. Vérifier l'état initial
```bash
scalecheck
```
**Résultat attendu :** Desired = 2 | Running = 2 | CPU Target = 60 %.

### 2. Activer le mode démonstration
```bash
scaledemo
```
**Action :** Active temporairement un seuil CPU de démonstration à 2 %.

### 3. Générer une charge sur l'API AWS (Terminal 2)
```bash
scaleload
```
**Action :** Génère du trafic pendant 120 secondes avec une concurrence de 50 requêtes.

### 4. Surveiller l'autoscaling (Terminal 1)
```bash
scalewatch
```
**À observer :** Augmentation éventuelle du nombre de tâches de 2 à 3, puis éventuellement 4.

**Arrêter la surveillance :** `Ctrl+C`.

### 5. Consulter l'historique d'autoscaling
```bash
scalehistory
```
**À montrer :** Les activités réelles de changement de capacité enregistrées par AWS.

### 6. Vérifier les alarmes CloudWatch
```bash
scalealarm
```
**À montrer :** L'état des alarmes associées à l'autoscaling.

### 7. Restaurer la configuration normale
```bash
scalerestore
```
**Résultat attendu :**
- Suppression de l'alarme temporaire.
- Suppression de la politique de démonstration.
- Restauration de la cible CPU à 60 %.
- Retour à une capacité désirée de 2 tâches.
- Conservation des limites min. 2 / max. 4.

### 8. Confirmer le retour à deux tâches
```bash
scalecheck
```
**Résultat attendu :** Desired = 2 | Running = 2 | Pending = 0 | CPU Target = 60 %.

### Présentation orale
> « Mon infrastructure AWS utilise une politique d'autoscaling basée sur le CPU. Elle maintient au minimum deux tâches et peut monter jusqu'à quatre en fonction de la charge. Je génère du trafic pour démontrer cette élasticité, puis je restaure la configuration normale à 60 % CPU. »

**Repères :** AWS ECS Fargate · Service Auto Scaling · CloudWatch · Target Tracking · Scale-out · Scale-in · Élasticité · Haute disponibilité.

**Important :** Toujours exécuter `scalerestore` après `scaledemo`, même si aucune augmentation de capacité n'a été observée.

## 11 — Observabilité | Grafana / Prometheus / Tempo | 2 min
**Navigateur — Grafana cloud**
```bash
open https://dw3e18cneqohd.cloudfront.net/grafana/dashboards
```
**Repères** · Grafana : tableaux de bord · Prometheus : métriques · Tempo : traces · OpenTelemetry : instrumentation · Latence · Erreurs · Santé de l'API · RAG.

**Terminal — Prometheus local, si utile**
```bash
curl -sS http://localhost:9090/-/healthy
```

## 12 — FinOps | Coûts AWS | 2 min
**Navigateur — AWS Billing / Cost Management**

**Repères** · Coût de l'infrastructure · ECS / Fargate · RDS · Réseau / ALB · CloudFront · Bedrock · Arbitrages coût / disponibilité · Budgets / surveillance.

**Démonstration** · Afficher les coûts réellement visibles dans la console ; distinguer coût constaté, estimation et prévision. **Ne pas annoncer un coût non vérifié.**

## 13 — Sécurité | Dernière couche technique | 2 min
**Terminal — contrôle d'accès cloud**

**Repères** · Session / authentification · HTTP 401 sans session si configuration inchangée · IAM · Security Groups · Accès réseau restreints · Secrets Manager · Séparation des rôles.

**Sécurité réseau** · ALB public · API accessible depuis l'ALB · RDS accessible depuis l'API · Cache accessible depuis l'API. **Ne pas présenter l'architecture 
comme entièrement privée ou zéro-trust.**

Premièrement, l’authentification. L’accès aux fonctionnalités de mon application est protégé. Par exemple, si quelqu’un essaie d’appeler directement l’API sans être authentifié, le serveur refuse l’accès avec une erreur HTTP 401.

```bash
curl -sS -o /dev/null -w 'API sans session : HTTP %{http_code}\n' https://dw3e18cneqohd.cloudfront.net/api/suppliers
```

Deuxièmement, la sécurité réseau. Sur AWS, j’utilise des Security Groups pour contrôler les communications autorisées entre les composants de l’infrastructure.
Ce sont des pare-feu virtuels qui contrôlent les communications autorisées entre les composants de mon infrastructure.
Par exemple, l’objectif est de limiter les accès à la base de données aux services qui en ont réellement besoin, plutôt que de l’exposer directement sur Internet.
Cela permet de réduire la surface d’attaque de l’application. 

```bash

AWS_PROFILE=hybrid-ai-terraform aws ec2 describe-security-groups --region eu-west-3 --query 'SecurityGroups[].{Name:GroupName,ID:GroupId,Description:Description}' --output table

```

### 3. AWS IAM — Gestion des rôles et permissions

**Objectif :** Montrer comment AWS gère les autorisations des services.

**Terminal — Afficher les rôles IAM du projet**
```bash
AWS_PROFILE=hybrid-ai-terraform aws iam list-roles --query 'Roles[?contains(RoleName, `hybrid-ai`)].{Role:RoleName,ARN:Arn}' --output table
```
L’Execution Role sert à ECS pour lancer le conteneur. Le Task Role sert à l’application pendant son fonctionnement. 

**À dire :**

> « Pour la gestion des permissions, j'utilise AWS IAM.
>
> IAM permet d'attribuer des rôles aux différents services AWS et de contrôler les actions qu'ils sont autorisés à effectuer.
>
> Par exemple, une tâche ECS peut avoir besoin d'accéder à certains services AWS, mais elle ne doit pas disposer de droits administrateur sur l'ensemble du compte.
>
> L'objectif est d'appliquer le principe du moindre privilège : donner uniquement les autorisations nécessaires au fonctionnement de chaque composant. »

**Repères techniques :** AWS IAM · Roles · Policies · Permissions · Least Privilege.

## 14 — CI/CD et conclusion | 1 min
**Terminal — GitHub Actions**
```bash
ls .github/workflows/
```
**Repères** · `ci.yml` · Contrôles automatisés · Docker · Évolutivité · Maintenance · De la Supply Chain à une plateforme Full Stack et cloud.

**Conclusion** · Retour rapide sur le **Control Center cloud** : métier + IA + infrastructure + exploitation dans une même plateforme.

Pour la partie DevOps, j’ai mis en place un pipeline d’intégration continue avec GitHub Actions.

À chaque push ou pull request sur la branche principale, GitHub déclenche automatiquement un workflow.

Ce workflow prépare un environnement Ubuntu avec Python 3.12, PostgreSQL avec pgvector et Redis.

Ensuite, il installe les dépendances, applique les migrations de base de données avec Alembic et exécute les tests automatisés avec Pytest.

L’objectif est de détecter les erreurs et les régressions avant qu’elles n’arrivent en production.

Pour la partie déploiement, mon infrastructure AWS est gérée séparément avec Terraform et ECS Fargate.

---

## MÉMO — PARCOURS
**Docker → Swagger (création / modification) → PostgreSQL → Frontend LOCAL → Kubernetes (auto-healing) / Helm → Terraform → Redis DOWN / UP local → AWS ECS → Sync fournisseur via interface → Auto-healing AWS → Autoscaling AWS → Grafana → FinOps → Sécurité → CI/CD → Conclusion.**

## CONTRÔLES AVANT ENTRETIEN
- Docker, Swagger, frontend local et IA disponibles.
- Fournisseur de démo : noter son ID ; ne pas le supprimer.
- Redis local : arrêt par Terminal, redémarrage via Control Center **testés** ; état final **Healthy**.
- Kubernetes : `minikube status` ; `minikube start` si nécessaire ; auto-healing API **testé**.
- Sync local → AWS : mécanisme testé et effets connus ; sinon pas d'écriture.
- AWS : ECS, ALB, autoscaling, Grafana, FinOps et authentification accessibles.
- Aucun `terraform apply`, aucune suppression de tâche ECS ou test de charge non validés.
