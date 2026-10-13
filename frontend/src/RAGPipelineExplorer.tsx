import { useMemo, useState } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  Handle,
  MarkerType,
  Position,
  type Edge,
  type Node,
  type NodeProps,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import './RAGPipelineExplorer.css'
import type { RAGEvent } from './ragStream'

type Stage = {
  id: string
  title: string
  subtitle: string
  description: string
  technical: string
}

const stages: Stage[] = [
  {
    id: 'question',
    title: 'User Question',
    subtitle: 'React → FastAPI',
    description: "User Question représente l'entrée du pipeline : React transmet la question à FastAPI, qui valide les données, mesure la préparation et lance le RAG. Les événements SSE rendent ensuite l'exécution observable en temps réel.",
    technical: "React transmet la question à FastAPI via l'API. Pydantic valide la requête, puis le backend lance le pipeline RAG avec ask_rag().",
  },
  {
    id: 'embedding',
    title: 'Embedding',
    subtitle: '384 dimensions',
    description: "Le modèle d'embedding transforme la question en vecteur de 384 dimensions grâce à la tokenisation, au Transformer, au pooling et à la normalisation. Cette représentation numérique permet ensuite la recherche sémantique.",
    technical: "La fonction generate_embedding(query) génère le vecteur de la question. Les documents de connaissance possèdent déjà leurs embeddings enregistrés dans la base de données.",
  },
  {
    id: 'pgvector',
    title: 'Semantic Search',
    subtitle: 'pgvector · Cosine',
    description: "Semantic Search utilise pgvector pour comparer l'embedding de la question aux vecteurs des documents. La similarité cosinus permet d'identifier les documents les plus proches du sens de la question.",
    technical: "La distance cosinus permet de classer les documents selon leur proximité sémantique avec la question. La configuration actuelle impose un score de similarité d'au moins 0,40 et retourne au maximum 3 documents.",
  },
  {
    id: 'structured',
    title: 'Structured Retrieval',
    subtitle: 'PostgreSQL',
    description: "Structured Retrieval interroge PostgreSQL via SQLAlchemy pour récupérer les données opérationnelles : fournisseurs, commandes, risques, retards et stocks bloqués. Les règles métier calculent les indicateurs utiles.",
    technical: "La fonction get_relevant_structured_context(query) s'exécute après semantic_search(). Les deux recherches sont donc réalisées successivement, et non en parallèle.",
  },
  {
    id: 'prompt',
    title: 'Prompt Builder',
    subtitle: 'Context assembly',
    description: "Prompt Builder rassemble les instructions du modèle, le glossaire métier, les données structurées, les documents retrouvés et la question utilisateur. Il construit un contexte destiné à guider le LLM et à limiter les hallucinations.",
    technical: "Le prompt intègre le BUSINESS_GLOSSARY, les données structurées, les documents de connaissance et des instructions destinées à limiter les réponses inventées (hallucinations).",
  },
  {
    id: 'llm',
    title: 'LLM Generation',
    subtitle: 'Ollama / Bedrock',
    description: "LLM Generation transmet le prompt au modèle de langage, exécuté avec Ollama en local ou Amazon Bedrock sur AWS. Le Transformer génère la réponse de manière autorégressive, token après token. Les métriques et les traces permettent de mesurer ses performances.",
    technical: "La fonction generate_answer(prompt) utilise le fournisseur LLM configuré, comme Ollama en local ou Amazon Bedrock sur AWS. Le modèle reçoit le contexte préparé, mais n'exécute pas lui-même les fonctions de recherche.",
  },
  {
    id: 'response',
    title: 'AI Response',
    subtitle: 'Total Execution Time',
    description: "AI Response clôture le pipeline RAG : FastAPI restitue la réponse générée à React. La plateforme mesure la durée totale du traitement et utilise OpenTelemetry pour analyser l'exécution de bout en bout dans Grafana.",
    technical: "La réponse JSON contient les champs answer, sources et data_sources. React affiche ensuite la réponse finale dans l'interface de l'assistant IA.",
  },
]

function formatDuration(ms: number): string {
  if (!Number.isFinite(ms) || ms < 0) return '—'

  if (ms >= 1000) {
    return `${(ms / 1000).toFixed(2)} s`
  }

  if (ms >= 1) {
    return `${ms.toFixed(2)} ms`
  }

  if (ms === 0) {
    return '0 µs'
  }

  const microseconds = ms * 1000

  return `${Number(microseconds.toFixed(2))} µs`
}

function StageNode({ data }: NodeProps) {
  const stage = data as {
    title: string
    subtitle: string
    status: string
    duration?: number
  }

  return (
    <div className={`rag-stage-node rag-stage-${stage.status}`}>
      {stage.title !== 'User Question' && (
        <Handle type="target" position={Position.Left} />
      )}
      <strong>{stage.title}</strong>
      <span>{stage.subtitle}</span>
      {typeof stage.duration === 'number' && (
        <small>{formatDuration(stage.duration)}</small>
      )}
      {stage.title !== 'AI Response' && (
        <Handle type="source" position={Position.Right} />
      )}
    </div>
  )
}

const nodeTypes = { stage: StageNode }

const initialNodes: Node[] = stages.map((stage, index) => ({
  id: stage.id,
  type: 'stage',
  position: { x: index * 235, y: 80 },
  data: {
    title: stage.title,
    subtitle: stage.subtitle,
  },
}))

const initialEdges: Edge[] = stages.slice(0, -1).map((stage, index) => ({
  id: `${stage.id}-${stages[index + 1].id}`,
  source: stage.id,
  target: stages[index + 1].id,
  type: 'straight',
  markerEnd: { type: MarkerType.ArrowClosed },
  style: { stroke: '#7286b0', strokeWidth: 2 },
}))

type Props = {
  events: RAGEvent[]
}

const eventStages: Record<string, string> = {
  request: 'question',
  embedding: 'embedding',
  pgvector: 'pgvector',
  structured: 'structured',
  prompt: 'prompt',
  llm: 'llm',
}

export default function RAGPipelineExplorer({ events }: Props) {
  const [selectedId, setSelectedId] = useState('pgvector')

  const liveNodes = useMemo(() => {
    const status: Record<string, string> = {}
    const durations: Record<string, number> = {}

    for (const item of events) {
      const [prefix, action] = item.event.split('.')
      const stageId = eventStages[prefix]

      if (!stageId) continue

      if (action === 'started') {
        status[stageId] = stageId === 'question' ? 'completed' : 'running'
      }
      if (action === 'completed') status[stageId] = 'completed'
      if (action === 'failed') status[stageId] = 'failed'

      if (typeof item.data.duration_ms === 'number') {
        if (item.event === 'request.completed') {
          durations.response = item.data.duration_ms
        } else if (item.event === 'request.prepared') {
          durations.question = item.data.duration_ms
        } else {
          durations[stageId] = item.data.duration_ms
        }
      }

      if (item.event === 'request.completed') {
        status.response = 'completed'
      }
      if (item.event === 'request.failed') {
        status.response = 'failed'
      }
    }


    return initialNodes.map((node) => ({
      ...node,
      data: {
        ...node.data,
        status: status[node.id] ?? 'idle',
        duration: durations[node.id],
      },
    }))
  }, [events])


  const executionStatus = useMemo(() => {
    if (events.some((item) => item.event === 'request.failed')) return 'FAILED'
    if (events.some((item) => item.event === 'request.completed')) return 'COMPLETED'
    if (events.some((item) => item.event === 'request.started')) return 'LIVE EXECUTION'
    return 'ARCHITECTURE VIEW'
  }, [events])

  const selectedEvents = useMemo(() => {
    const prefix = Object.entries(eventStages)
      .find(([, stageId]) => stageId === selectedId)?.[0]

    if (selectedId === 'response') {
      return events.filter((item) => item.event.startsWith('request.'))
    }

    if (!prefix) return []

    return events.filter((item) => item.event.startsWith(`${prefix}.`))
  }, [events, selectedId])

  const latestEvent = selectedEvents[selectedEvents.length - 1]

  const diagnosticsEvent = selectedId === 'pgvector'
    ? [...selectedEvents].reverse().find(
        (item) => item.event === 'pgvector.diagnostics'
      )
    : undefined

  const vectorDiagnostics = diagnosticsEvent?.data

  const completedEvent = [...selectedEvents]
    .reverse()
    .find((item) => item.event.endsWith('.completed'))

  const startedEvent = [...selectedEvents]
    .reverse()
    .find((item) => item.event.endsWith('.started'))

  const failedEvent = [...selectedEvents]
    .reverse()
    .find((item) => item.event.endsWith('.failed'))

  const stageStatus = failedEvent
    ? 'FAILED'
    : completedEvent
      ? 'COMPLETED'
      : startedEvent
        ? 'RUNNING'
        : 'WAITING'

  const metrics = selectedId === 'question'
    ? [...selectedEvents].reverse().find(
        (item) => item.event === 'request.prepared'
      )?.data ?? {}
    : selectedId === 'response'
      ? [...selectedEvents].reverse().find(
          (item) => item.event === 'request.completed'
        )?.data ?? {}
      : completedEvent?.data ?? latestEvent?.data ?? {}

  const traceId = events
    .map((item) => item.data.trace_id)
    .find((value): value is string =>
      typeof value === 'string' && /^[a-f0-9]{32}$/i.test(value),
    )

  const grafanaTraceUrl = traceId
    ? (() => {
        const url = new URL(
          '/a/grafana-exploretraces-app/explore',
          'http://localhost:3000',
        )

        url.searchParams.set('var-ds', 'afzhwousowfswc')
        url.searchParams.set('actionView', 'traceList')
        url.searchParams.set('from', 'now-1h')
        url.searchParams.set('to', 'now')
        url.searchParams.set('timezone', 'browser')
        url.searchParams.set('traceId', traceId)

        return url.toString()
      })()
    : null

  const formatMetric = (value: unknown): string => {
    if (typeof value === 'number') {
      return Number.isInteger(value) ? String(value) : value.toFixed(2)
    }
    if (typeof value === 'string') return value
    if (typeof value === 'boolean') return value ? 'Yes' : 'No'
    return '—'
  }

  const selectedStage = useMemo(
    () => stages.find((stage) => stage.id === selectedId) ?? stages[0],
    [selectedId],
  )

  return (
    <section className="rag-explorer">
      <div className="rag-explorer-header">
        <div>
          <span className="rag-explorer-eyebrow">ARCHITECTURE EXPLORER</span>
          <h2>RAG Pipeline Explorer</h2>
          <p>Explore the actual execution order of your retrieval-augmented generation pipeline.</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          {(() => {
            const completed = [...events].reverse().find(
              (item) => item.event === 'request.completed'
            )

            const totalDuration = completed?.data.duration_ms

            return typeof totalDuration === 'number' ? (
              <span className="rag-explorer-badge">
                Total Pipeline: {formatDuration(totalDuration)}
              </span>
            ) : null
          })()}

          <span className="rag-explorer-badge">{executionStatus}</span>
        </div>
      </div>

      <div className="rag-flow">
        <ReactFlow
          defaultEdgeOptions={{ type: 'straight' }}
          nodes={liveNodes}
          edges={initialEdges}
          nodeTypes={nodeTypes}
          onNodeClick={(_, node) => setSelectedId(node.id)}
          nodesDraggable={false}
          nodesConnectable={false}
          zoomOnScroll={false}
          zoomOnPinch={false}
          panOnDrag={true}
          elementsSelectable
          fitView
          fitViewOptions={{ padding: 0.15 }}
          minZoom={0.1}
          maxZoom={1.5}
        >
          <Background color="#26364c" gap={22} />
          <Controls />
        </ReactFlow>
      </div>

      <div className="rag-details-layout">
      <div className="rag-stage-details rag-stage-explanation">
        <span className="rag-explorer-eyebrow">SELECTED COMPONENT</span>
        <h3>{selectedStage.title}</h3>
        <p>{selectedStage.description}</p>

        {selectedId === 'question' && (
          <details style={{
            marginTop: 18,
            padding: 20,
            border: '1px solid rgba(96,165,250,0.3)',
            borderRadius: 12,
            background: 'linear-gradient(135deg, rgba(59,130,246,0.07), rgba(15,23,42,0.2))',
          }}>
            <summary style={{
              cursor: 'pointer',
              fontWeight: 700,
              fontSize: 15,
              color: '#93c5fd',
            }}>
              Comprendre User Question — Du navigateur au backend
            </summary>

            <div style={{ marginTop: 20, fontSize: 13, lineHeight: 1.85 }}>

              <h4>1. Saisie de la question</h4>
              <p>
                L'utilisateur pose une question en langage naturel
                depuis l'interface React. À ce stade, aucun embedding
                n'a encore été calculé.
              </p>

              <h4>2. Envoi au backend FastAPI</h4>
              <p>
                Le frontend transmet la question à l'API avec une
                requête HTTP POST vers /ai/ask/stream.
                Le corps de la requête contient du JSON.
              </p>

              <div style={{
                padding: 16,
                margin: '16px 0',
                borderRadius: 10,
                background: 'rgba(0,0,0,0.3)',
                fontFamily: 'monospace',
                color: '#93c5fd',
                overflowX: 'auto',
              }}>
                {'POST /ai/ask/stream'}
                <br />
                {'Content-Type: application/json'}
                <br />
                {'{"question": "Quels fournisseurs présentent un risque ?"}'}
              </div>

              <h4>3. Validation avec Pydantic</h4>
              <p>
                FastAPI utilise le modèle AskRequest pour vérifier
                que la requête contient un champ question de type
                chaîne de caractères. Une requête invalide est
                rejetée avant l'exécution du pipeline.
              </p>

              <h4>4. Préparation et mesure du temps</h4>
              <p>
                Le backend mesure la durée entre l'entrée dans
                l'application ASGI et l'arrivée dans l'endpoint
                FastAPI. Cette mesure est publiée dans l'événement
                request.prepared.
              </p>

              <div style={{
                padding: 14,
                margin: '16px 0',
                borderLeft: '3px solid #60a5fa',
                borderRadius: 6,
                background: 'rgba(59,130,246,0.08)',
              }}>
                <strong>À ne pas confondre</strong>
                <p style={{ marginBottom: 0 }}>
                  La durée de User Question mesure la préparation
                  initiale côté serveur. Elle ne correspond pas
                  au temps total du RAG, qui inclut notamment
                  la recherche documentaire et la génération LLM.
                </p>
              </div>

              <h4>5. Démarrage du pipeline RAG</h4>
              <p>
                Le backend lance ask_rag() dans un thread dédié.
                La question est ensuite utilisée pour produire
                son embedding et rechercher les documents pertinents.
              </p>

              <h4>6. Streaming SSE et observabilité</h4>
              <p>
                Le backend transmet les événements d'exécution
                progressivement grâce à StreamingResponse et au
                format Server-Sent Events (SSE).
                Une trace OpenTelemetry permet de relier
                les opérations à une même exécution.
              </p>

              <div style={{
                padding: 16,
                margin: '18px 0',
                background: 'rgba(0,0,0,0.25)',
                borderRadius: 10,
                textAlign: 'center',
              }}>
                <div style={{ color: '#93c5fd', fontWeight: 700 }}>
                  UTILISATEUR
                </div>
                <div style={{ margin: '8px 0' }}>↓</div>
                <div>Interface React</div>
                <div style={{ margin: '8px 0', color: '#93c5fd' }}>
                  ↓ HTTP POST /ai/ask/stream
                </div>
                <div style={{ fontFamily: 'monospace', fontSize: 12 }}>
                  {'JSON : {"question": "..."}'}
                </div>
                <div style={{ margin: '8px 0' }}>↓</div>
                <div>API FastAPI</div>
                <div style={{ margin: '8px 0' }}>↓</div>
                <div>Validation Pydantic</div>
                <div style={{ margin: '8px 0' }}>↓</div>
                <div>ask_rag()</div>
                <div style={{ margin: '8px 0' }}>↓</div>
                <div style={{ color: '#4ade80', fontWeight: 700 }}>
                  EMBEDDING
                </div>
              </div>

              <div style={{
                padding: 14,
                marginTop: 14,
                borderRadius: 10,
                background: 'rgba(59,130,246,0.08)',
                border: '1px solid rgba(96,165,250,0.2)',
              }}>
                <strong style={{ color: '#93c5fd' }}>
                  Observabilité — En parallèle du traitement
                </strong>
                <p style={{ marginBottom: 0, marginTop: 8 }}>
                  request.started → request.prepared → événements du pipeline
                  → request.completed
                </p>
              </div>

              

            </div>
          </details>
        )}

        {selectedId === 'structured' && (
          <details style={{
            marginTop: 18,
            padding: 20,
            border: '1px solid rgba(96,165,250,0.3)',
            borderRadius: 12,
            background: 'linear-gradient(135deg, rgba(59,130,246,0.07), rgba(15,23,42,0.2))',
          }}>
            <summary style={{
              cursor: 'pointer',
              fontWeight: 700,
              fontSize: 15,
              color: '#93c5fd',
            }}>
              Comprendre Structured Retrieval — Des données SQL au contexte métier
            </summary>

            <div style={{ marginTop: 20, fontSize: 13, lineHeight: 1.85 }}>

              <h4>1. Quel est le rôle du Structured Retrieval ?</h4>
              <p>
                Cette étape récupère des informations métier structurées
                dans PostgreSQL afin d'apporter au modèle IA des faits
                et des indicateurs Supply Chain calculés par le backend.
              </p>

              <h4>2. Différence avec Semantic Search</h4>
              <p>
                Semantic Search utilise les embeddings et pgvector
                pour retrouver des documents proches du sens de la question.
              </p>
              <p>
                Structured Retrieval exploite des données organisées
                en tables relationnelles pour produire des indicateurs
                précis : nombre de commandes en retard, niveaux de risque,
                stocks bloqués ou performances fournisseurs.
              </p>

              <div style={{
                padding: 15,
                background: 'rgba(59,130,246,0.08)',
                borderLeft: '3px solid #60a5fa',
                borderRadius: 8,
                margin: '16px 0',
              }}>
                <strong>Deux approches complémentaires</strong>
                <p style={{ marginBottom: 0 }}>
                  Semantic Search retrouve des connaissances documentaires.
                  Structured Retrieval apporte des données opérationnelles
                  et des KPI calculés à partir de la base métier.
                </p>
              </div>

              <h4>3. Compréhension de la question</h4>
              <p>
                La fonction get_relevant_structured_context(question)
                commence par normaliser certains termes.
                Par exemple, supplier devient fournisseur,
                et PO, CDE ou CMD deviennent commande.
              </p>
              <p>
                Des règles Python analysent ensuite les mots présents
                dans la question pour déterminer les informations
                métier à restituer.
              </p>

              <h4>4. Accès à PostgreSQL avec SQLAlchemy</h4>
              <p>
                Le backend ouvre une session de base de données
                avec SessionLocal(), puis récupère les enregistrements
                des modèles Supplier et PurchaseOrder.
              </p>

              <div style={{
                padding: 16,
                background: 'rgba(0,0,0,0.3)',
                borderRadius: 10,
                margin: '16px 0',
                fontFamily: 'monospace',
                fontSize: 12,
                color: '#93c5fd',
                overflowX: 'auto',
              }}>
                <div>suppliers = db.query(Supplier).all()</div>
                <div>purchase_orders = db.query(PurchaseOrder).all()</div>
              </div>

              <p>
                Ces requêtes récupèrent les données nécessaires
                aux calculs. Le modèle IA ne génère pas lui-même
                des requêtes SQL arbitraires.
              </p>

              <h4>5. Calcul des indicateurs Supply Chain</h4>
              <p>
                Le backend calcule notamment le nombre de fournisseurs,
                leur répartition par niveau de risque, le stock bloqué
                total et les indicateurs de retard des commandes.
              </p>

              <div style={{
                padding: 18,
                margin: '16px 0',
                background: 'rgba(0,0,0,0.3)',
                border: '1px solid rgba(96,165,250,0.2)',
                borderRadius: 10,
                textAlign: 'center',
              }}>
                <div style={{ color: '#93c5fd', fontWeight: 700 }}>
                  Taux de retard fournisseur
                </div>
                <div style={{
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  gap: 10,
                  marginTop: 14,
                  fontFamily: 'Georgia, serif',
                  fontSize: 16,
                }}>
                  <span>Taux =</span>
                  <span style={{
                    display: 'inline-flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    lineHeight: 1.5,
                  }}>
                    <span style={{
                      borderBottom: '2px solid #93c5fd',
                      padding: '0 10px 5px',
                    }}>
                      Commandes en retard
                    </span>
                    <span style={{ paddingTop: 5 }}>
                      Total des commandes
                    </span>
                  </span>
                  <span>× 100</span>
                </div>
              </div>

              <p>
                Une commande est considérée en retard lorsque
                sa date confirmée est postérieure à sa date demandée,
                si les deux dates sont disponibles.
              </p>
              <p>
                Le retard moyen est calculé à partir du nombre
                de jours séparant ces deux dates, pour les commandes
                identifiées comme étant en retard.
              </p>

              <h4>6. Construction du contexte structuré</h4>
              <p>
                Les résultats sont convertis en lignes de texte,
                commençant par RELEVANT STRUCTURED DATA.
                Ce contexte est ensuite transmis à l'étape
                Prompt Builder.
              </p>

              <h4>7. Schéma du traitement</h4>

              <div style={{
                padding: 18,
                margin: '16px 0',
                background: 'rgba(0,0,0,0.25)',
                borderRadius: 10,
                textAlign: 'center',
              }}>
                <div style={{ color: '#93c5fd', fontWeight: 700 }}>
                  QUESTION UTILISATEUR
                </div>
                <div style={{ margin: '8px 0' }}>↓</div>
                <div>Normalisation des termes</div>
                <div style={{ margin: '8px 0' }}>↓</div>
                <div>SQLAlchemy + PostgreSQL</div>
                <div style={{ margin: '8px 0' }}>↓</div>
                <div>Supplier + PurchaseOrder</div>
                <div style={{ margin: '8px 0' }}>↓</div>
                <div>Calcul des KPI Supply Chain</div>
                <div style={{ margin: '8px 0' }}>↓</div>
                <div>Sélection des informations pertinentes</div>
                <div style={{ margin: '8px 0' }}>↓</div>
                <div>Contexte textuel structuré</div>
                <div style={{ margin: '8px 0' }}>↓</div>
                <div style={{ color: '#4ade80', fontWeight: 700 }}>
                  PROMPT BUILDER
                </div>
              </div>

              <h4>8. Observabilité</h4>
              <p>
                Les événements structured.started,
                structured.completed et structured.failed
                permettent de suivre l'exécution de cette étape.
                La durée de récupération est mesurée séparément
                des autres composants du pipeline.
              </p>

              

            </div>
          </details>
        )}

        {selectedId === 'prompt' && (
          <details style={{
            marginTop: 18,
            padding: 20,
            border: '1px solid rgba(96,165,250,0.3)',
            borderRadius: 12,
            background: 'linear-gradient(135deg, rgba(59,130,246,0.07), rgba(15,23,42,0.2))',
          }}>
            <summary style={{
              cursor: 'pointer',
              fontWeight: 700,
              fontSize: 15,
              color: '#93c5fd',
            }}>
              Comprendre Prompt Builder — Comment le contexte du LLM est construit
            </summary>

            <div style={{ marginTop: 20, fontSize: 13, lineHeight: 1.85 }}>

              <h4>1. À quoi sert le Prompt Builder ?</h4>
              <p>
                Le Prompt Builder prépare le texte transmis au modèle
                de langage. Il rassemble les instructions, les données
                métier, les documents retrouvés et la question utilisateur.
              </p>
              <p>
                Son objectif est de fournir au LLM un contexte exploitable
                pour produire une réponse fondée sur les informations
                disponibles dans notre plateforme Supply Chain.
              </p>

              <h4>2. Les quatre éléments du contexte</h4>

              <div style={{
                padding: 15,
                background: 'rgba(59,130,246,0.08)',
                borderLeft: '3px solid #60a5fa',
                borderRadius: 8,
                margin: '16px 0',
              }}>
                <strong style={{ color: '#93c5fd' }}>
                  BUSINESS GLOSSARY
                </strong>
                <p>
                  Le glossaire métier aide le LLM à interpréter
                  correctement le vocabulaire Supply Chain.
                </p>

                <strong style={{ color: '#93c5fd' }}>
                  STRUCTURED DATA
                </strong>
                <p>
                  Données opérationnelles issues de PostgreSQL :
                  fournisseurs, risques, stocks bloqués, commandes
                  et indicateurs de performance.
                </p>

                <strong style={{ color: '#93c5fd' }}>
                  KNOWLEDGE DOCUMENTS
                </strong>
                <p>
                  Documents retrouvés par Semantic Search grâce
                  aux embeddings et à pgvector.
                </p>

                <strong style={{ color: '#93c5fd' }}>
                  QUESTION
                </strong>
                <p style={{ marginBottom: 0 }}>
                  La question originale de l'utilisateur,
                  conservée pour guider la génération.
                </p>
              </div>

              <h4>3. Les instructions du modèle</h4>
              <p>
                Le backend construit un prompt qui commence par
                définir le rôle du modèle : assistant IA Supply Chain.
                Il lui demande de répondre uniquement à partir
                des données fournies.
              </p>
              <p>
                Les règles imposent notamment de préserver les
                valeurs numériques, de respecter les classements
                fournisseurs et de ne pas inventer d'informations.
              </p>

              <h4>4. Réduction des hallucinations</h4>
              <p>
                Une hallucination se produit lorsqu'un LLM génère
                une information qui n'est pas étayée par les données.
                Notre prompt demande explicitement au modèle de
                signaler lorsqu'il manque des informations.
              </p>

              <div style={{
                padding: 14,
                background: 'rgba(59,130,246,0.08)',
                borderLeft: '3px solid #60a5fa',
                borderRadius: 6,
                margin: '16px 0',
              }}>
                <strong>Point important</strong>
                <p style={{ marginBottom: 0 }}>
                  Ces instructions réduisent le risque d'hallucination,
                  mais ne garantissent pas mathématiquement que le
                  modèle respectera toutes les règles.
                  Les données structurées restent la référence
                  pour les chiffres et les KPI.
                </p>
              </div>

              <h4>5. Format des réponses</h4>
              <p>
                Le prompt demande au modèle de répondre dans
                la langue de l'utilisateur.
              </p>
              <p>
                Pour les analyses fournisseurs en français,
                il prévoit quatre sections :
              </p>

              <div style={{
                padding: 16,
                background: 'rgba(0,0,0,0.3)',
                borderRadius: 10,
                margin: '16px 0',
                fontFamily: 'monospace',
                color: '#93c5fd',
              }}>
                <div>### SYNTHÈSE</div>
                <div>### INDICATEURS CLÉS</div>
                <div>### ANALYSE</div>
                <div>### RECOMMANDATION</div>
              </div>

              <p>
                Le modèle doit également éviter les répétitions,
                conserver les classements et proposer des actions
                opérationnelles fondées sur les données disponibles.
              </p>

              <h4>6. Construction du prompt final</h4>
              <p>
                Dans app/ai/service.py, Python assemble le prompt
                avec une chaîne de caractères formatée.
                Les différents contextes sont insérés dans
                les sections prévues.
              </p>

              <div style={{
                padding: 16,
                background: 'rgba(0,0,0,0.3)',
                borderRadius: 10,
                margin: '16px 0',
                fontFamily: 'monospace',
                fontSize: 12,
                color: '#93c5fd',
                overflowX: 'auto',
              }}>
                <div>BUSINESS GLOSSARY:</div>
                <div>{'{BUSINESS_GLOSSARY}'}</div>
                <br />
                <div>STRUCTURED DATA:</div>
                <div>{'{structured_context}'}</div>
                <br />
                <div>KNOWLEDGE DOCUMENTS:</div>
                <div>{'{rag_context}'}</div>
                <br />
                <div>QUESTION:</div>
                <div>{'{query}'}</div>
                <br />
                <div>ANSWER:</div>
              </div>

              <h4>7. Schéma du traitement</h4>

              <div style={{
                padding: 18,
                margin: '16px 0',
                background: 'rgba(0,0,0,0.25)',
                borderRadius: 10,
                textAlign: 'center',
              }}>
                <div style={{ color: '#93c5fd', fontWeight: 700 }}>
                  PROMPT BUILDER
                </div>
                <div style={{ margin: '8px 0' }}>↓</div>
                <div>Instructions du modèle</div>
                <div style={{ margin: '8px 0' }}>+</div>
                <div>Business Glossary</div>
                <div style={{ margin: '8px 0' }}>+</div>
                <div>Structured Data — PostgreSQL</div>
                <div style={{ margin: '8px 0' }}>+</div>
                <div>Knowledge Documents — pgvector</div>
                <div style={{ margin: '8px 0' }}>+</div>
                <div>Question utilisateur</div>
                <div style={{ margin: '8px 0' }}>↓</div>
                <div>Prompt final assemblé par Python</div>
                <div style={{ margin: '8px 0' }}>↓</div>
                <div style={{ color: '#4ade80', fontWeight: 700 }}>
                  LLM GENERATION
                </div>
              </div>

              <h4>8. Observabilité</h4>
              <p>
                Le backend émet les événements prompt.started
                et prompt.completed. La durée de construction
                du prompt est mesurée séparément de la génération LLM.
              </p>

              

            </div>
          </details>
        )}

        {selectedId === 'llm' && (
          <details style={{
            marginTop: 18,
            padding: 20,
            border: '1px solid rgba(96,165,250,0.3)',
            borderRadius: 12,
            background: 'linear-gradient(135deg, rgba(59,130,246,0.07), rgba(15,23,42,0.2))',
          }}>
            <summary style={{
              cursor: 'pointer',
              fontWeight: 700,
              fontSize: 15,
              color: '#93c5fd',
            }}>
              Comprendre LLM Generation — Du prompt à la réponse
            </summary>

            <div style={{ marginTop: 20, fontSize: 13, lineHeight: 1.85 }}>

              <h4>1. Quel est le rôle du LLM ?</h4>
              <p>
                Le Large Language Model reçoit le prompt construit
                à l'étape précédente. Il utilise les instructions,
                les données métier et les documents pour générer
                une réponse en langage naturel.
              </p>
              <p>
                Le LLM ne réalise pas lui-même les recherches SQL
                ou vectorielles : ces opérations ont déjà été
                effectuées par les composants précédents.
              </p>

              <h4>2. Ollama et Llama 3.2 : quelle différence ?</h4>
              <p>
                Ollama est le moteur qui permet d'exécuter
                des modèles de langage localement.
                Llama 3.2:3B est le modèle IA utilisé par défaut
                dans notre plateforme.
              </p>
              <p>
                Le suffixe 3B indique environ trois milliards
                de paramètres appris pendant l'entraînement.
                Ces paramètres servent à calculer les prédictions
                du modèle.
              </p>

              <h4>3. Deux fournisseurs : Ollama et Bedrock</h4>
              <p>
                Notre backend utilise la variable LLM_PROVIDER
                pour sélectionner le fournisseur.
              </p>

              <div style={{
                padding: 15,
                background: 'rgba(59,130,246,0.08)',
                borderLeft: '3px solid #60a5fa',
                borderRadius: 8,
                margin: '16px 0',
              }}>
                <strong style={{ color: '#93c5fd' }}>
                  Ollama — Exécution locale
                </strong>
                <p>
                  Le backend appelle l'API Ollama avec le modèle
                  llama3.2:3b. Le paramètre stream est fixé à false :
                  Ollama renvoie la réponse complète après génération.
                </p>

                <strong style={{ color: '#93c5fd' }}>
                  Amazon Bedrock — Exécution sur AWS
                </strong>
                <p style={{ marginBottom: 0 }}>
                  Le backend utilise l'API Converse de Bedrock.
                  Le modèle configuré par défaut est
                  eu.amazon.nova-micro-v1:0.
                  La configuration prévoit au maximum 1 000 tokens
                  générés et une température de 0.
                </p>
              </div>

              <h4>4. Tokenisation du prompt</h4>
              <p>
                Avant la génération, le modèle découpe le prompt
                en tokens. Un token peut représenter un mot,
                une partie de mot ou un signe de ponctuation.
                Ces tokens sont convertis en identifiants numériques.
              </p>

              <h4>5. Transformer autorégressif</h4>
              <p>
                Llama 3.2 utilise une architecture Transformer
                de type décodeur. Le mécanisme d'attention permet
                au modèle de tenir compte des tokens précédents
                pour calculer une distribution de probabilités
                sur les tokens suivants.
              </p>
              <p>
                La génération est autorégressive : chaque nouveau
                token est ajouté à la séquence, puis utilisé
                pour prédire le suivant.
              </p>

              <div style={{
                padding: 18,
                margin: '16px 0',
                borderRadius: 10,
                background: 'rgba(0,0,0,0.3)',
                border: '1px solid rgba(96,165,250,0.2)',
                textAlign: 'center',
              }}>
                <div style={{
                  color: '#93c5fd',
                  fontWeight: 700,
                  marginBottom: 12,
                }}>
                  Probabilité du prochain token
                </div>

                <div style={{
                  fontFamily: 'Georgia, serif',
                  fontSize: 20,
                  overflowX: 'auto',
                }}>
                  P(xₜ | x₁, x₂, …, xₜ₋₁)
                </div>

                <p style={{ marginBottom: 0, marginTop: 12 }}>
                  Le modèle estime la probabilité du token xₜ
                  à partir de la séquence de tokens précédente.
                </p>
              </div>

              <h4>6. Comment le prochain token est-il choisi ?</h4>
              <p>
                Le Transformer produit des scores pour les tokens
                possibles. Une fonction softmax les transforme
                en distribution de probabilités.
              </p>
              <p>
                Une stratégie de décodage sélectionne ensuite
                le token suivant. La température et d'autres
                paramètres peuvent influencer cette sélection.
              </p>
              <p>
                Dans notre configuration Bedrock, la température
                est fixée à 0. Pour Ollama, notre fonction
                n'impose pas explicitement de température.
              </p>

              <h4>7. Comprendre les métriques</h4>
              <p>
                La plateforme récupère les statistiques renvoyées
                par le fournisseur pour mesurer les performances
                de génération.
              </p>

              <div style={{
                padding: 15,
                background: 'rgba(0,0,0,0.3)',
                borderRadius: 10,
                margin: '16px 0',
              }}>
                <p>
                  <strong>Input Tokens :</strong> nombre de tokens
                  utilisés pour représenter le prompt.
                </p>
                <p>
                  <strong>Output Tokens :</strong> nombre de tokens
                  générés dans la réponse.
                </p>
                <p>
                  <strong>Total Tokens :</strong> somme des tokens
                  d'entrée et de sortie.
                </p>
                <p style={{ marginBottom: 0 }}>
                  <strong>Generation Speed :</strong> vitesse de
                  génération mesurée en tokens par seconde.
                </p>
              </div>

              <div style={{
                padding: 18,
                margin: '16px 0',
                borderRadius: 10,
                background: 'rgba(0,0,0,0.3)',
                border: '1px solid rgba(96,165,250,0.2)',
                textAlign: 'center',
              }}>
                <div style={{
                  color: '#93c5fd',
                  fontWeight: 700,
                  marginBottom: 12,
                }}>
                  Calcul de la vitesse de génération
                </div>

                <div style={{
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  gap: 10,
                  fontFamily: 'Georgia, serif',
                  fontSize: 17,
                }}>
                  <span>Vitesse =</span>
                  <span style={{
                    display: 'inline-flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    lineHeight: 1.5,
                  }}>
                    <span style={{
                      borderBottom: '2px solid #93c5fd',
                      padding: '0 10px 5px',
                    }}>
                      Tokens générés
                    </span>
                    <span style={{ paddingTop: 5 }}>
                      Durée de génération (s)
                    </span>
                  </span>
                </div>

                <p style={{ marginBottom: 0, marginTop: 12 }}>
                  Pour Ollama, le backend utilise eval_count
                  et eval_duration, exprimée en nanosecondes.
                </p>
              </div>

              <h4>8. Streaming : une distinction importante</h4>
              <p>
                Notre API FastAPI utilise des événements SSE pour
                afficher progressivement les étapes du pipeline.
                Cependant, l'appel actuel à Ollama utilise
                stream: false.
              </p>
              <p>
                Cela signifie que le suivi du pipeline est
                progressif, mais que les tokens du LLM ne sont
                pas envoyés individuellement au navigateur
                par cet appel.
              </p>

              <h4>9. Schéma du processus</h4>

              <div style={{
                padding: 18,
                margin: '16px 0',
                background: 'rgba(0,0,0,0.25)',
                borderRadius: 10,
                textAlign: 'center',
              }}>
                <div style={{ color: '#93c5fd', fontWeight: 700 }}>
                  PROMPT FINAL
                </div>
                <div style={{ margin: '8px 0' }}>↓</div>
                <div>generate_answer(prompt)</div>
                <div style={{ margin: '8px 0' }}>↓</div>
                <div>Ollama ou Amazon Bedrock</div>
                <div style={{ margin: '8px 0' }}>↓</div>
                <div>Tokenisation</div>
                <div style={{ margin: '8px 0' }}>↓</div>
                <div>Transformer décodeur</div>
                <div style={{ margin: '8px 0' }}>↓</div>
                <div>Prédiction du prochain token</div>
                <div style={{ margin: '8px 0' }}>↓</div>
                <div>Génération autorégressive</div>
                <div style={{ margin: '8px 0' }}>↓</div>
                <div style={{ color: '#4ade80', fontWeight: 700 }}>
                  AI RESPONSE
                </div>
              </div>

              <h4>10. Observabilité</h4>
              <p>
                Les appels aux fournisseurs sont instrumentés
                avec OpenTelemetry. Les traces portent les noms
                llm.ollama.generate et llm.bedrock.converse.
              </p>
              <p>
                Cela permet d'identifier le fournisseur et le modèle
                utilisés, puis d'analyser leur exécution dans
                notre système d'observabilité.
              </p>

              

            </div>
          </details>
        )}

        {selectedId === 'response' && (
          <details style={{
            marginTop: 18,
            padding: 20,
            border: '1px solid rgba(96,165,250,0.3)',
            borderRadius: 12,
            background: 'linear-gradient(135deg, rgba(59,130,246,0.07), rgba(15,23,42,0.2))',
          }}>
            <summary style={{
              cursor: 'pointer',
              fontWeight: 700,
              fontSize: 15,
              color: '#93c5fd',
            }}>
              Comprendre AI Response — Du LLM à l'utilisateur
            </summary>

            <div style={{ marginTop: 20, fontSize: 13, lineHeight: 1.85 }}>

              <h4>1. Le rôle de AI Response</h4>
              <p>
                AI Response représente la dernière étape du pipeline RAG.
                Elle correspond à la restitution du résultat généré
                par le modèle de langage à l'utilisateur.
              </p>
              <p>
                Contrairement aux étapes précédentes, ce composant
                ne réalise ni recherche vectorielle, ni requête SQL,
                ni génération supplémentaire.
              </p>

              <h4>2. Du LLM au backend FastAPI</h4>
              <p>
                Le backend appelle generate_answer(prompt).
                Cette fonction retourne le texte produit par
                Ollama ou Amazon Bedrock.
              </p>
              <p>
                Le résultat revient ensuite au traitement RAG,
                qui peut le transmettre à la couche API
                avec les informations associées à la requête.
              </p>

              <h4>3. Communication avec React</h4>
              <p>
                Notre plateforme utilise FastAPI côté serveur
                et React côté navigateur.
              </p>
              <p>
                Le frontend déclenche la requête et reçoit
                les informations permettant d'afficher
                la réponse et les différentes étapes d'exécution.
              </p>

              <h4>4. Les événements SSE</h4>
              <p>
                Server-Sent Events (SSE) est un mécanisme HTTP
                permettant au serveur d'envoyer progressivement
                des événements au navigateur.
              </p>

              <div style={{
                padding: 15,
                background: 'rgba(59,130,246,0.08)',
                borderLeft: '3px solid #60a5fa',
                borderRadius: 8,
                margin: '16px 0',
              }}>
                <strong style={{ color: '#93c5fd' }}>
                  Dans notre RAG Pipeline Explorer
                </strong>
                <p>
                  Les événements de progression permettent
                  de visualiser l'exécution des composants :
                  préparation, embedding, recherche,
                  récupération structurée, construction
                  du prompt et génération.
                </p>
                <p style={{ marginBottom: 0 }}>
                  Le résultat final permet ensuite au frontend
                  de présenter la réponse générée.
                </p>
              </div>

              <h4>5. Durée totale du pipeline</h4>
              <p>
                Le temps total représente la durée globale
                mesurée pour le traitement de la requête.
                Il ne correspond pas uniquement au temps
                passé dans le modèle de langage.
              </p>

              <div style={{
                padding: 18,
                margin: '16px 0',
                borderRadius: 10,
                background: 'rgba(0,0,0,0.3)',
                border: '1px solid rgba(96,165,250,0.2)',
                textAlign: 'center',
              }}>
                <div style={{
                  color: '#93c5fd',
                  fontWeight: 700,
                  marginBottom: 12,
                }}>
                  Temps total d'exécution
                </div>

                <div style={{
                  fontFamily: 'Georgia, serif',
                  fontSize: 16,
                  lineHeight: 1.8,
                }}>
                  T total = T fin − T début
                </div>

                <p style={{ marginBottom: 0, marginTop: 12 }}>
                  La mesure globale englobe les opérations
                  nécessaires au traitement de la requête RAG.
                </p>
              </div>

              <h4>6. Pourquoi le LLM prend-il le plus de temps ?</h4>
              <p>
                Les opérations de préparation et de recherche
                peuvent être très rapides. En revanche,
                le modèle de langage doit effectuer de nombreux
                calculs pour générer successivement les tokens.
              </p>
              <p>
                Sur l'exécution affichée dans notre interface,
                LLM Generation dure environ 10,38 secondes,
                contre 10,43 secondes pour le pipeline complet.
                Le LLM représente donc la majeure partie
                du temps de traitement.
              </p>

              <h4>7. Les sources et la fiabilité</h4>
              <p>
                La réponse est construite à partir du contexte
                préparé précédemment : données structurées
                et documents retrouvés par recherche sémantique.
              </p>
              <p>
                Le prompt demande au modèle de ne pas inventer
                d'informations et de conserver les chiffres
                issus des données métier.
              </p>
              <p>
                Ces consignes améliorent l'ancrage de la réponse
                dans les données disponibles, sans constituer
                une garantie absolue d'exactitude.
              </p>

              <h4>8. Observabilité de bout en bout</h4>
              <p>
                Les traces OpenTelemetry permettent de relier
                les différentes opérations techniques d'une
                même requête et de les analyser dans Grafana.
              </p>
              <p>
                Le Trace ID sert à retrouver l'exécution
                correspondante dans le système d'observabilité.
              </p>

              <h4>9. Schéma du retour de la réponse</h4>

              <div style={{
                padding: 18,
                margin: '16px 0',
                background: 'rgba(0,0,0,0.25)',
                borderRadius: 10,
                textAlign: 'center',
              }}>
                <div style={{ color: '#93c5fd', fontWeight: 700 }}>
                  LLM GENERATION
                </div>
                <div style={{ margin: '8px 0' }}>↓</div>
                <div>Texte généré par le modèle</div>
                <div style={{ margin: '8px 0' }}>↓</div>
                <div>Backend Python — FastAPI</div>
                <div style={{ margin: '8px 0' }}>↓</div>
                <div>Résultat et événements SSE</div>
                <div style={{ margin: '8px 0' }}>↓</div>
                <div>Frontend React</div>
                <div style={{ margin: '8px 0' }}>↓</div>
                <div>Affichage de la réponse</div>
                <div style={{ margin: '8px 0' }}>↓</div>
                <div style={{ color: '#4ade80', fontWeight: 700 }}>
                  PIPELINE COMPLETED
                </div>
              </div>

              <h4>10. AI Response et LLM Generation : la différence</h4>

              <div style={{
                padding: 15,
                background: 'rgba(0,0,0,0.3)',
                borderRadius: 10,
                margin: '16px 0',
              }}>
                <p>
                  <strong>LLM Generation :</strong> mesure
                  le travail de génération du modèle.
                </p>
                <p style={{ marginBottom: 0 }}>
                  <strong>AI Response :</strong> présente
                  la durée globale du pipeline RAG.
                </p>
              </div>

              

            </div>
          </details>
        )}

        {selectedId === 'embedding' && (
          <details style={{
            marginTop: 18,
            padding: 20,
            border: '1px solid rgba(96,165,250,0.3)',
            borderRadius: 12,
            background: 'linear-gradient(135deg, rgba(59,130,246,0.07), rgba(15,23,42,0.2))',
          }}>
            <summary style={{
              cursor: 'pointer',
              fontWeight: 700,
              fontSize: 15,
              color: '#93c5fd',
            }}>
              Comprendre les embeddings — Du texte aux 384 dimensions
            </summary>

            <div style={{ marginTop: 20, fontSize: 13, lineHeight: 1.85 }}>

              <h4>1. Qu'est-ce qu'un embedding ?</h4>
              <p>
                Un embedding est une représentation numérique d'un texte.
                Dans notre plateforme, le modèle all-MiniLM-L6-v2 transforme
                chaque question et chaque document en un vecteur de 384 dimensions.
              </p>

              <div style={{
                padding: 16,
                background: 'rgba(0,0,0,0.25)',
                borderRadius: 10,
                textAlign: 'center',
                margin: '16px 0',
              }}>
                <div style={{ color: '#93c5fd', fontWeight: 700 }}>
                  Question en langage naturel
                </div>
                <div style={{ margin: '10px 0', fontSize: 20 }}>↓</div>
                <div>Modèle Transformer : all-MiniLM-L6-v2</div>
                <div style={{ margin: '10px 0', fontSize: 20 }}>↓</div>
                <div style={{ color: '#4ade80', fontWeight: 700 }}>
                  Vecteur numérique de 384 dimensions
                </div>
              </div>

              <h4>2. Tokenisation</h4>
              <p>
                Le texte est découpé en tokens : des mots ou des morceaux
                de mots. Chaque token est associé à un identifiant numérique.
              </p>

              <h4>3. Représentation numérique initiale</h4>
              <p>
                Chaque identifiant est transformé en représentation numérique
                grâce aux paramètres appris pendant l'entraînement.
                Le modèle tient également compte de la position des tokens.
              </p>

              <h4>4. Transformer et mécanisme d'attention</h4>
              <p>
                Le Transformer contextualise les tokens : leur représentation
                dépend des autres tokens de la phrase.
                Le mécanisme d'attention calcule quelles informations
                doivent contribuer à cette contextualisation.
              </p>

              <div style={{
                padding: 18,
                margin: '16px 0',
                borderRadius: 10,
                background: 'rgba(0,0,0,0.3)',
                border: '1px solid rgba(96,165,250,0.2)',
                textAlign: 'center',
                overflowX: 'auto',
              }}>
                <div style={{ marginBottom: 12, color: '#93c5fd', fontWeight: 700 }}>
                  Formule de l'attention
                </div>

                <div style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 10,
                  fontFamily: 'Georgia, serif',
                  fontSize: 17,
                  whiteSpace: 'nowrap',
                }}>
                  <span>Attention(Q,K,V) = softmax(</span>
                  <span style={{
                    display: 'inline-flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    lineHeight: 1.5,
                  }}>
                    <span style={{
                      borderBottom: '2px solid #93c5fd',
                      padding: '0 12px 5px',
                    }}>
                      QKᵀ
                    </span>
                    <span style={{ paddingTop: 5 }}>√dₖ</span>
                  </span>
                  <span>) V</span>
                </div>
              </div>

              <p>
                Ici, Q, K et V désignent les matrices Query, Key et Value
                du mécanisme d'attention. Elles ne correspondent pas aux
                vecteurs Question et Document du Semantic Search.
              </p>

              <h4>5. Mean Pooling : obtenir un seul vecteur</h4>
              <p>
                Le Transformer produit une représentation contextualisée
                pour chaque token. Le Mean Pooling calcule la moyenne
                des représentations des tokens valides pour obtenir
                un seul vecteur de 384 dimensions.
              </p>

              <div style={{
                padding: 18,
                margin: '16px 0',
                borderRadius: 10,
                background: 'rgba(0,0,0,0.3)',
                border: '1px solid rgba(96,165,250,0.2)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 12,
                fontFamily: 'Georgia, serif',
                fontSize: 22,
              }}>
                <span>E =</span>
                <span style={{
                  display: 'inline-flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  lineHeight: 1.5,
                }}>
                  <span style={{
                    borderBottom: '2px solid #93c5fd',
                    padding: '0 18px 6px',
                  }}>
                    Σ hᵢ
                  </span>
                  <span style={{ paddingTop: 6 }}>N</span>
                </span>
              </div>

              <p>
                hᵢ représente le vecteur contextualisé du token i.
                N est le nombre de tokens pris en compte.
                La moyenne est calculée dimension par dimension.
              </p>

              <h4>6. Normalisation</h4>
              <p>
                Dans notre pipeline, les embeddings sont normalisés
                pour obtenir une norme proche de 1.
                Cela facilite leur comparaison par similarité cosinus.
              </p>

              <div style={{
                padding: 14,
                background: 'rgba(59,130,246,0.08)',
                borderLeft: '3px solid #60a5fa',
                borderRadius: 6,
                margin: '16px 0',
              }}>
                <strong>Pourquoi 384 dimensions ?</strong>
                <p style={{ marginBottom: 0 }}>
                  C'est une caractéristique de l'architecture
                  all-MiniLM-L6-v2. Chaque dimension est une composante
                  numérique apprise. Elle ne correspond pas nécessairement
                  à un concept identifiable comme le risque ou le retard.
                  L'information sémantique est répartie dans le vecteur.
                </p>
              </div>

              <h4>7. Application à notre RAG</h4>
              <p>
                La question est transformée en embedding.
                Les documents possèdent déjà leurs embeddings
                enregistrés dans PostgreSQL avec pgvector.
                L'étape Semantic Search compare ensuite ces vecteurs
                pour identifier les documents les plus proches.
              </p>

              

            </div>
          </details>
        )}


        {selectedId === 'pgvector' && (
                    <details style={{
                      marginBottom: 20,
                      padding: 20,
                      border: '1px solid rgba(96,165,250,0.3)',
                      borderRadius: 12,
                      background: 'linear-gradient(135deg, rgba(59,130,246,0.07), rgba(15,23,42,0.2))',
                    }}>
                      <summary style={{
                        cursor: 'pointer',
                        fontWeight: 700,
                        fontSize: 15,
                        color: '#93c5fd',
                      }}>
                        Comprendre la similarité cosinus — Explication mathématique
                      </summary>

                      <div style={{ marginTop: 22, fontSize: 13, lineHeight: 1.85 }}>

                        <h4>1. À quoi sert la similarité cosinus ?</h4>
                        <p>
                          Elle mesure à quel point deux vecteurs sont orientés
                          dans la même direction, indépendamment de leur longueur.
                          Dans notre RAG, nous comparons le vecteur de la question
                          avec celui de chaque document.
                        </p>

                        <div style={{
                          padding: '24px 12px',
                          margin: '20px 0',
                          borderRadius: 12,
                          background: 'rgba(0,0,0,0.3)',
                          border: '1px solid rgba(96,165,250,0.2)',
                          display: 'flex',
                          justifyContent: 'center',
                          alignItems: 'center',
                          gap: 12,
                          flexWrap: 'wrap',
                          fontFamily: 'Georgia, serif',
                          fontSize: 22,
                          color: '#f8fafc',
                        }}>
                          <span>cos(θ) =</span>

                          <span style={{
                            display: 'inline-flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            lineHeight: 1.5,
                          }}>
                            <span style={{
                              borderBottom: '2px solid #93c5fd',
                              padding: '0 14px 6px',
                            }}>
                              A · B
                            </span>
                            <span style={{ paddingTop: 6 }}>
                              ‖A‖ × ‖B‖
                            </span>
                          </span>
                        </div>

                        <h4>2. Comment lire cette formule ?</h4>

                        <p><strong>A :</strong> vecteur de la question (384 dimensions).</p>
                        <p><strong>B :</strong> vecteur du document (384 dimensions).</p>

                        <p>
                          <strong>A · B — Produit scalaire :</strong>
                          {' '}on multiplie chaque composante de A par
                          la composante correspondante de B, puis on additionne
                          les 384 résultats.
                        </p>

                        <p>
                          <strong>‖A‖ et ‖B‖ — Normes :</strong>
                          {' '}elles représentent les longueurs des deux vecteurs.
                        </p>

                        <div style={{
                          padding: 14,
                          borderLeft: '3px solid #60a5fa',
                          background: 'rgba(59,130,246,0.08)',
                          borderRadius: 6,
                          margin: '16px 0',
                        }}>
                          <strong>Pourquoi diviser par les normes ?</strong>
                          <p style={{ marginBottom: 0 }}>
                            Pour supprimer l'influence de la longueur des vecteurs.
                            Nous comparons uniquement leurs directions.
                            Deux vecteurs de tailles différentes peuvent donc
                            obtenir une similarité de 1.
                          </p>
                        </div>

                        <h4>3. Comment interpréter les résultats ?</h4>

                        <div style={{
                          display: 'grid',
                          gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
                          gap: 12,
                          margin: '16px 0',
                        }}>
                          {[
                            { score: '+1', angle: '0°', arrows: '→ →', color: '#4ade80', label: 'Même direction' },
                            { score: '0', angle: '90°', arrows: '→ ↑', color: '#facc15', label: 'Perpendiculaires' },
                            { score: '-1', angle: '180°', arrows: '→ ←', color: '#f87171', label: 'Directions opposées' },
                          ].map((item) => (
                            <div key={item.score} style={{
                              padding: 14,
                              textAlign: 'center',
                              border: '1px solid rgba(255,255,255,0.12)',
                              borderRadius: 10,
                              background: 'rgba(0,0,0,0.2)',
                            }}>
                              <div style={{ fontSize: 24, color: item.color, fontWeight: 700 }}>
                                {item.score}
                              </div>
                              <div style={{ fontSize: 26, margin: '8px 0', color: item.color }}>
                                {item.arrows}
                              </div>
                              <div style={{ fontWeight: 600 }}>{item.label}</div>
                              <div style={{ opacity: 0.7 }}>Angle : {item.angle}</div>
                            </div>
                          ))}
                        </div>

                        <p style={{ opacity: 0.8 }}>
                          Attention : un score de -1 ne signifie pas nécessairement
                          que deux phrases ont des sens opposés. Il décrit une
                          opposition géométrique entre les vecteurs.
                        </p>

                        <h4>4. Exemple de calcul simple</h4>

                        <div style={{
                          padding: 18,
                          background: 'rgba(0,0,0,0.25)',
                          borderRadius: 10,
                          fontFamily: 'monospace',
                          lineHeight: 2,
                        }}>
                          <div>A = [1, 2]</div>
                          <div>B = [2, 4]</div>
                          <br />
                          <div>Produit scalaire = (1 × 2) + (2 × 4) = 10</div>
                          <div>‖A‖ = √(1² + 2²) = √5</div>
                          <div>‖B‖ = √(2² + 4²) = √20</div>
                          <br />
                          <div style={{ color: '#4ade80', fontWeight: 700 }}>
                            Similarité = 10 / (√5 × √20) = 1
                          </div>
                        </div>

                        <p>
                          Les deux vecteurs ont des longueurs différentes,
                          mais pointent exactement dans la même direction.
                        </p>

                        <h4>5. Application à notre plateforme RAG</h4>

                        <p>
                          Le modèle all-MiniLM-L6-v2 transforme chaque question
                          et chaque document en un vecteur de 384 dimensions.
                        </p>

                        <p>
                          PostgreSQL et pgvector comparent ces vecteurs.
                          Les documents sont classés par proximité et sélectionnés
                          selon le seuil minimum de similarité et la limite Top K.
                        </p>

                        

                        <p style={{ marginTop: 16 }}>
                          L'explorateur ci-dessous affiche les véritables calculs :
                          produit scalaire, normes, similarité, distance pgvector
                          et les 384 multiplications composante par composante.
                        </p>

                      </div>
                    </details>

        )}
      </div>

        <div className="rag-stage-details rag-execution-metrics">
          <span className="rag-explorer-eyebrow">LIVE EXECUTION METRICS</span>

          <div className="rag-metrics-heading">
            <h3>{selectedStage.title}</h3>
            <span className={`rag-metric-status rag-metric-${stageStatus.toLowerCase()}`}>
              {stageStatus}
            </span>
          </div>

          {selectedEvents.length === 0 ? (
            <p className="rag-metrics-empty">
              No execution data yet. Ask the AI Assistant a question to inspect this stage.
            </p>
          ) : (
            <div className="rag-metrics-grid">
              {typeof metrics.duration_ms === 'number' && (
                <div className="rag-metric-item">
                  <span>Duration</span>
                  <strong>{formatDuration(metrics.duration_ms)}</strong>
                </div>
              )}

              {selectedId === 'llm' && typeof metrics.provider === 'string' && (
                <div className="rag-metric-item">
                  <span>Provider</span>
                  <strong>{metrics.provider}</strong>
                </div>
              )}

              {selectedId === 'llm' && typeof metrics.model === 'string' && (
                <div className="rag-metric-item">
                  <span>Model</span>
                  <strong>{metrics.model}</strong>
                </div>
              )}

              {selectedId === 'llm' && typeof metrics.input_tokens === 'number' && (
                <div className="rag-metric-item">
                  <span>Input Tokens</span>
                  <strong>{metrics.input_tokens.toLocaleString('en-US')}</strong>
                </div>
              )}

              {selectedId === 'llm' && typeof metrics.output_tokens === 'number' && (
                <div className="rag-metric-item">
                  <span>Output Tokens</span>
                  <strong>{metrics.output_tokens.toLocaleString('en-US')}</strong>
                </div>
              )}

              {selectedId === 'llm' && typeof metrics.total_tokens === 'number' && (
                <div className="rag-metric-item">
                  <span>Total Tokens</span>
                  <strong>{metrics.total_tokens.toLocaleString('en-US')}</strong>
                </div>
              )}

              {selectedId === 'llm' && typeof metrics.tokens_per_second === 'number' && (
                <div className="rag-metric-item">
                  <span>Generation Speed</span>
                  <strong>{metrics.tokens_per_second.toFixed(2)} tokens/s</strong>
                </div>
              )}

              {typeof metrics.dimensions === 'number' && (
                <div className="rag-metric-item">
                  <span>Vector dimensions</span>
                  <strong>{metrics.dimensions}</strong>
                </div>
              )}

              {selectedId === 'embedding' && typeof metrics.model === 'string' && (
                <div className="rag-metric-item">
                  <span>Embedding Model</span>
                  <strong>{metrics.model}</strong>
                </div>
              )}

              {selectedId === 'embedding' && Array.isArray(metrics.vector) && (
                <details style={{ gridColumn: '1 / -1', marginTop: 12 }}>
                  <summary style={{ cursor: 'pointer', fontWeight: 600 }}>
                    Show all {metrics.vector.length} vector dimensions
                  </summary>

                  <div style={{
                    maxHeight: 320,
                    overflowY: 'auto',
                    marginTop: 12,
                    padding: 16,
                    borderRadius: 8,
                    background: 'rgba(0,0,0,0.25)',
                    fontFamily: 'monospace',
                    fontSize: 12
                  }}>
                    {(metrics.vector as number[]).map((value, index) => (
                      <div key={index} style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        padding: '3px 0'
                      }}>
                        <span>Dimension {String(index + 1).padStart(3, '0')}</span>
                        <span>{value.toFixed(8)}</span>
                      </div>
                    ))}
                  </div>
                </details>
              )}

              {selectedId === 'pgvector' && vectorDiagnostics && (
                <div className="rag-metric-item">
                  <span>Cosine diagnostics</span>
                  <strong>
                    {Array.isArray(vectorDiagnostics.documents)
                      ? `${vectorDiagnostics.documents.length} documents analysés`
                      : 'Aucun document'}
                  </strong>
                </div>
              )}

              {selectedId === 'pgvector' &&
                vectorDiagnostics &&
                Array.isArray(vectorDiagnostics.documents) && (
                  <div style={{ gridColumn: '1 / -1', marginTop: 16 }}>
                    <h3 style={{ marginBottom: 12 }}>
                      Explorateur de similarité cosinus
                    </h3>

                    <div style={{ marginBottom: 12, fontSize: 13 }}>
                      Similarité minimale : {String(vectorDiagnostics.min_similarity)}
                      {' | '}
                      Top K : {String(vectorDiagnostics.limit)}
                    </div>

                    {(vectorDiagnostics.documents as Array<Record<string, unknown>>)
                      .map((doc, index) => {
                        const query = doc.query_vector as number[]
                        const document = doc.document_vector as number[]
                        const products = doc.products as number[]

                        return (
                          <details
                            key={String(doc.id ?? index)}
                            style={{
                              marginBottom: 12,
                              padding: 14,
                              border: '1px solid rgba(255,255,255,0.15)',
                              borderRadius: 8,
                            }}
                          >
                            <summary
                              style={{
                                cursor: 'pointer',
                                fontWeight: 600,
                              }}
                            >
                              #{String(doc.rank)} — {String(doc.title)}
                              {' — '}
                              {doc.selected ? 'SÉLECTIONNÉ' : 'REJETÉ'}
                              {' — '}
                              Similarité : {Number(doc.pgvector_similarity).toFixed(6)}
                            </summary>

                            <div style={{ marginTop: 14, fontSize: 13 }}>
                              <div>Produit scalaire : {Number(doc.dot_product).toFixed(8)}</div>
                              <div>Norme de la question : {Number(doc.query_norm).toFixed(8)}</div>
                              <div>Norme du document : {Number(doc.document_norm).toFixed(8)}</div>
                              <div>Similarité cosinus (Python) : {Number(doc.similarity).toFixed(8)}</div>
                              <div>Similarité (pgvector) : {Number(doc.pgvector_similarity).toFixed(8)}</div>
                              <div>Distance cosinus : {Number(doc.distance).toFixed(8)}</div>
                              <div>
                                Décision : {doc.selected
                                  ? 'Similarité supérieure ou égale au seuil et rang dans le Top K'
                                  : 'Similarité inférieure au seuil ou rang hors du Top K'}
                              </div>
                            </div>

                            <details style={{ marginTop: 14 }}>
                              <summary style={{ cursor: 'pointer' }}>
                                Afficher les {products.length} multiplications vectorielles
                              </summary>

                              <div
                                style={{
                                  maxHeight: 360,
                                  overflow: 'auto',
                                  marginTop: 12,
                                  fontFamily: 'monospace',
                                  fontSize: 12,
                                }}
                              >
                                <table style={{ width: '100%', textAlign: 'right' }}>
                                  <thead>
                                    <tr>
                                      <th>Dimension</th>
                                      <th>Question (Q)</th>
                                      <th>Document (D)</th>
                                      <th>Q × D</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {products.map((product, dimension) => (
                                      <tr key={dimension}>
                                        <td>{dimension + 1}</td>
                                        <td>{query[dimension].toFixed(8)}</td>
                                        <td>{document[dimension].toFixed(8)}</td>
                                        <td>{product.toFixed(10)}</td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              </div>
                            </details>
                          </details>
                        )
                      })}
                  </div>
                )}

              {typeof metrics.documents_count === 'number' && (
                <div className="rag-metric-item">
                  <span>Documents retrieved</span>
                  <strong>{metrics.documents_count}</strong>
                </div>
              )}

              {typeof metrics.min_similarity === 'number' && (
                <div className="rag-metric-item">
                  <span>Similarity threshold</span>
                  <strong>{metrics.min_similarity.toFixed(2)}</strong>
                </div>
              )}

              {typeof metrics.limit === 'number' && (
                <div className="rag-metric-item">
                  <span>Top K</span>
                  <strong>{metrics.limit}</strong>
                </div>
              )}
            </div>
          )}

          {Array.isArray(metrics.scores) && metrics.scores.length > 0 && (
            <div className="rag-metric-scores">
              <strong>Retrieved documents</strong>
              {metrics.scores.map((score, index) => {
                const entry = score as Record<string, unknown>
                return (
                  <div className="rag-score-row" key={index}>
                    <span>{formatMetric(entry.title)}</span>
                    <strong>
                      {typeof entry.similarity === 'number'
                        ? entry.similarity.toFixed(4)
                        : '—'}
                    </strong>
                  </div>
                )
              })}
            </div>
          )}

          <div className="rag-trace-section">
            <span className="rag-explorer-eyebrow">TRACE & OBSERVABILITY</span>
            <p>
              Trace ID:{' '}
              <code>{traceId ?? 'Not available'}</code>
            </p>
            {grafanaTraceUrl && (
              <a
                className="rag-grafana-link"
                href={grafanaTraceUrl}
                target="_blank"
                rel="noopener noreferrer"
              >
                View Trace in Grafana ↗
              </a>
            )}
          </div>
        </div>
      </div>
    </section>
  )
}
