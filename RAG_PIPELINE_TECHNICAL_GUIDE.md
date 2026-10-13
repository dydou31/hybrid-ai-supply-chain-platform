# RAG Pipeline Explorer — Guide technique et préparation à l'entretien

**Projet :** Hybrid AI Supply Chain Platform  
**Contexte :** démonstration technique locale pour AUMOVIO  
**Portée :** fonctionnement observé et vérifié du RAG, plus points à confirmer dans le code.

## 1. Objectif du RAG

**RAG** signifie *Retrieval-Augmented Generation* : on recherche d'abord du contexte pertinent, puis on le fournit à un modèle de langage pour générer une réponse. Ce mécanisme ne réentraîne pas le LLM et ne garantit pas, à lui seul, l'exactitude des réponses.

**Composants identifiés dans le projet :** FastAPI (backend), React/TypeScript (interface), PostgreSQL + pgvector (documents et recherche vectorielle), Sentence Transformers `all-MiniLM-L6-v2` (embeddings de 384 dimensions), Ollama avec `llama3.2:3b` (génération locale) et SSE (*Server-Sent Events*, télémétrie du pipeline).

## 2. Les sept étapes visibles

```text
User Question
    ↓
Embedding
    ↓
Semantic Search
    ↓
Structured Retrieval
    ↓
Prompt Builder
    ↓
LLM Generation
    ↓
AI Response
```

Ce diagramme décrit les **étapes présentées par l'explorateur**. Le détail précis des requêtes de récupération structurée et du prompt doit être confirmé dans les fichiers backend avant d'en faire une affirmation technique exhaustive.

### 2.1 User Question

L'utilisateur soumet une question, par exemple : **« Quels sont les fournisseurs les plus à risque ? »**. La question est reçue par l'API et sert d'entrée à la recherche.

### 2.2 Embedding

Le modèle `all-MiniLM-L6-v2` transforme la question en un vecteur numérique de **384 composantes** :

```text
Q = [q₁, q₂, …, q₃₈₄]
```

L'explorateur peut afficher les 384 valeurs réelles. Les dimensions sont imposées par le modèle choisi, pas par le concept d'embedding en général. Les embeddings rendent possible une comparaison de proximité sémantique entre question et documents, sans se limiter à la présence des mêmes mots.

**Fichier identifié :** `app/ai/embeddings.py` (`generate_embedding`).

### 2.3 Semantic Search — PostgreSQL + pgvector

Chaque document indexé possède lui aussi un embedding de 384 dimensions. pgvector compare l'embedding de la question aux embeddings des documents au moyen de la **distance cosinus** (`<=>`).

**Similarité cosinus :**

```text
                  Σᵢ (Qᵢ × Dᵢ)
cos(Q,D) = ──────────────────────────
           √Σᵢ(Qᵢ²) × √Σᵢ(Dᵢ²)

Distance cosinus = 1 − similarité cosinus
```

Pour deux vecteurs non nuls, la similarité cosinus est comprise entre −1 et 1. Elle mesure l'orientation relative des vecteurs, pas une probabilité de pertinence.

**Étapes du calcul détaillé :**

1. Multiplier chaque composante de la question par la composante correspondante du document : `Qᵢ × Dᵢ` (384 produits).
2. Additionner ces produits : c'est le **produit scalaire**.
3. Calculer les normes euclidiennes `||Q||` et `||D||`.
4. Diviser le produit scalaire par le produit des normes.
5. Comparer le score au seuil de sélection.

**Paramètres de la recherche testée :** `min_similarity=0.40`, `limit=3` (Top K). La requête principale filtre les documents dont la distance est supérieure à `1 − 0.40 = 0.60`, classe les résultats par distance croissante et conserve au maximum trois documents.

**Exemple réel validé localement :**

| Document | Similarité cosinus approximative | Distance approximative | Décision |
|---|---:|---:|---|
| Supplier Beta performance | 0,417316 | 0,582684 | **Sélectionné** |
| Supplier Alpha delay | 0,285973 | 0,714027 | Rejeté (sous le seuil) |
| Blocked stock | 0,253815 | 0,746185 | Rejeté (sous le seuil) |

Ces valeurs correspondent **à cette question et à cet état des données** ; elles ne sont pas universelles. Un seul document passe le seuil. Les calculs Python du diagnostic ont été comparés aux scores pgvector avec une différence inférieure à la tolérance de test de `0.0001`.

**Cosine Similarity Explorer :** la brique Semantic Search affiche aussi, en mode diagnostic local, les documents rejetés, leur classement, les deux vecteurs, les 384 produits, le produit scalaire, les normes, la similarité Python et la distance pgvector. **La requête de diagnostic est distincte : elle n'ajoute pas les documents rejetés au contexte transmis au LLM.**

**Fichier identifié :** `app/ai/retrieval.py` (`semantic_search`). Le diagnostic inspecte au plus **20 documents** dans la version implémentée : ce n'est donc pas nécessairement une vue exhaustive si la base grandit.

### 2.4 Structured Retrieval

Cette étape est distincte de la recherche de documents par embeddings. Son objectif architectural est d'apporter, lorsque le pipeline le prévoit, des données structurées issues des tables métier (par exemple des informations fournisseurs). **Les tables, champs, requêtes et conditions effectivement utilisés restent à confirmer dans le code** : ne pas présenter un exemple hypothétique comme une requête déjà vérifiée.

### 2.5 Prompt Builder

Le constructeur de prompt assemble les instructions, la question et les éléments de contexte disponibles pour le LLM. Schéma conceptuel :

```text
Instructions + question + documents récupérés
             + éventuelles données structurées
                         ↓
                   Prompt du LLM
```

La formulation exacte des instructions et l'ordre réel des sections du prompt doivent être lus dans le code source pour une explication fidèle.

### 2.6 LLM Generation

Ollama exécute localement **Llama 3.2 3B** pour produire la réponse à partir du prompt. Dans l'implémentation observée, l'appel Ollama utilise **`stream=False`** : le flux SSE du pipeline **n'est pas** un flux de tokens générés un par un par le modèle.

**Différence importante :** le modèle d'embedding encode du texte en nombres ; le LLM produit du texte. Les deux rôles sont complémentaires.

### 2.7 AI Response

La réponse est présentée à l'utilisateur. Sa qualité dépend notamment de la pertinence du contexte, de la qualité des données, des instructions et du comportement du modèle. Une réponse générée peut encore contenir des erreurs : il faut prévoir des évaluations.

## 3. SSE et observabilité du pipeline

Le backend émet des événements **Server-Sent Events** que React exploite pour animer les étapes et afficher les métriques. Événements observés :

- `embedding.completed` : durée, modèle, nombre de dimensions ; vecteur complet uniquement lorsque le diagnostic est autorisé.
- `pgvector.completed` : métriques de recherche (notamment documents retrouvés et similarités).
- `pgvector.diagnostics` : en mode diagnostic, détail des candidats examinés et des calculs cosinus.

**Données diagnostiques par document :** `id`, `title`, `rank`, `selected`, `query_vector`, `document_vector`, `products`, `dot_product`, `query_norm`, `document_norm`, `similarity`, `pgvector_similarity`, `distance`.

**Fichiers identifiés :** `app/ai/router.py` (endpoint `POST /ai/ask/stream`) et `frontend/src/RAGPipelineExplorer.tsx` (visualisation des événements).

L'interface affiche les calculs fournis par le backend ; elle n'a pas besoin de recalculer le classement pour montrer les résultats.

## 4. Sécurité du diagnostic

Les vecteurs détaillés ne sont émis que si les **deux** conditions suivantes sont vraies :

```text
RAG_VECTOR_DEBUG=true
APP_ENV=local
```

Sur le Mac de développement, elles sont définies dans `docker-compose.override.yml`, **exclu de Git localement** via `.git/info/exclude`. Il ne faut pas le committer ni le distribuer avec des valeurs de debug actives.

**Test exécuté :** avec `APP_ENV=production` et `RAG_VECTOR_DEBUG=true`, aucun événement `pgvector.diagnostics` ni vecteur complet dans `embedding.completed` n'a été transmis, et la recherche sémantique continuait de fonctionner.

**Limite de sécurité :** ce test prouve le comportement du garde-fou pour cette configuration ; il ne constitue **pas** un contrôle d'accès. Si l'environnement local est accessible à des tiers, les vecteurs et les informations de documents peuvent être exposés. Avant tout déploiement public : authentification/autorisation, configuration d'environnement contrôlée, revue des journaux et tests de sécurité supplémentaires.

## 5. Scénario de démonstration (5 minutes)

1. Poser : **« Quels sont les fournisseurs les plus à risque ? »**
2. Cliquer sur **Embedding** : expliquer `all-MiniLM-L6-v2` et afficher les **384 dimensions**.
3. Cliquer sur **Semantic Search** : expliquer la formule cosinus, le seuil **0,40** et le **Top K = 3**.
4. Montrer **Supplier Beta performance**, score **≈ 0,417316**, seul document retenu.
5. Déplier les **384 multiplications** et montrer produit scalaire, normes et score final.
6. Montrer les deux documents rejetés et expliquer **pourquoi ils n'entrent pas dans le contexte du LLM**.
7. Parcourir Structured Retrieval, Prompt Builder, LLM Generation et AI Response, en distinguant clairement ce qui est vérifié de ce qui reste à documenter.
8. Conclure sur l'observabilité, la séparation du diagnostic et du chemin fonctionnel, et les garde-fous de sécurité.

**Phrase de présentation :**

> « J'ai rendu la recherche sémantique observable : on peut inspecter les embeddings réels, reproduire mathématiquement le score de pgvector et comprendre pourquoi un document est retenu ou rejeté, sans modifier les documents utilisés pour générer la réponse. »

## 6. Questions d'entretien et réponses

**Pourquoi pgvector plutôt qu'une base vectorielle séparée ?**  
Pour conserver la recherche vectorielle dans PostgreSQL, à proximité des données relationnelles. Le bon choix dépend aussi du volume, des performances attendues et des besoins d'exploitation.

**Pourquoi 384 dimensions ?**  
Parce que le modèle `all-MiniLM-L6-v2` produit des vecteurs de 384 dimensions.

**Pourquoi la similarité cosinus ?**  
Elle compare la direction des vecteurs et convient fréquemment aux embeddings textuels. Le score n'est pas une probabilité.

**Pourquoi un seuil de 0,40 ?**  
C'est le seuil configuré pour cette démonstration. Il filtre les candidats jugés trop éloignés selon cette métrique. Il faudrait l'ajuster à l'aide d'évaluations sur un jeu de questions représentatif.

**Que signifie Top K = 3 ?**  
Au maximum trois documents admissibles sont renvoyés, ordonnés par distance croissante. S'il n'y en a qu'un au-dessus du seuil, un seul est retenu.

**Les documents rejetés sont-ils envoyés au LLM ?**  
Non : leur affichage provient d'une requête diagnostique distincte de la récupération utilisée pour le contexte.

**Le RAG entraîne-t-il le modèle ?**  
Non. Il ajoute du contexte à l'inférence, sans mettre à jour automatiquement les poids du LLM.

**Les valeurs affichées sont-elles simulées ?**  
Non. Les vecteurs et les scores sont issus de la base et du modèle d'embedding, et le calcul Python a été confronté au résultat pgvector.

**SSE signifie-t-il que le LLM génère token par token ?**  
Non. Ici, les SSE signalent les étapes du pipeline ; l'appel Ollama observé utilise `stream=False`.

**Quels sont les points de vigilance ?**  
Pertinence des résultats, évaluation du seuil, coût du diagnostic, confidentialité des vecteurs, authentification et robustesse de la génération.

## 7. Points à vérifier et améliorations

- Lire l'implémentation de **Structured Retrieval** pour documenter ses tables et requêtes réelles.
- Lire le **Prompt Builder** pour reproduire la structure exacte du prompt.
- Ajouter des tests automatisés de non-régression sur le contexte réellement transmis au LLM.
- Mesurer précision/rappel de récupération sur un jeu d'évaluation métier.
- Prévoir authentification et autorisation pour tout diagnostic exposé hors machine de développement.
- Mesurer les performances sur un corpus plus volumineux ; le diagnostic actuel est limité à 20 candidats.
- Améliorer la présentation des tableaux de 384 dimensions sans dégrader les performances du navigateur.

---

**Statut :** guide créé à partir des éléments du projet et des tests rapportés dans la conversation. Les parties non inspectées directement sont explicitement signalées. Ce document ne constitue ni un audit de sécurité ni une preuve de déploiement cloud.
