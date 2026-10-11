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
    description: "L'utilisateur pose une question depuis l'interface AI Assistant.",
    technical: "React transmet la question à FastAPI via l'API. Pydantic valide la requête, puis le backend lance le pipeline RAG avec ask_rag().",
  },
  {
    id: 'embedding',
    title: 'Embedding',
    subtitle: '384 dimensions',
    description: "La question est transformée en vecteur numérique de 384 dimensions afin de représenter son sens et de permettre une recherche sémantique.",
    technical: "La fonction generate_embedding(query) génère le vecteur de la question. Les documents de connaissance possèdent déjà leurs embeddings enregistrés dans la base de données.",
  },
  {
    id: 'pgvector',
    title: 'Semantic Search',
    subtitle: 'pgvector · Cosine',
    description: "PostgreSQL, grâce à pgvector, compare le vecteur de la question avec ceux des documents pour identifier les informations les plus pertinentes.",
    technical: "La distance cosinus permet de classer les documents selon leur proximité sémantique avec la question. La configuration actuelle impose un score de similarité d'au moins 0,40 et retourne au maximum 3 documents.",
  },
  {
    id: 'structured',
    title: 'Structured Retrieval',
    subtitle: 'PostgreSQL',
    description: "Le backend récupère les données métier pertinentes de la Supply Chain, notamment les informations structurées disponibles dans PostgreSQL.",
    technical: "La fonction get_relevant_structured_context(query) s'exécute après semantic_search(). Les deux recherches sont donc réalisées successivement, et non en parallèle.",
  },
  {
    id: 'prompt',
    title: 'Prompt Builder',
    subtitle: 'Context assembly',
    description: "L'application rassemble la question, les documents retrouvés, les données métier et les règles de gestion afin de construire un contexte complet pour le modèle IA.",
    technical: "Le prompt intègre le BUSINESS_GLOSSARY, les données structurées, les documents de connaissance et des instructions destinées à limiter les réponses inventées (hallucinations).",
  },
  {
    id: 'llm',
    title: 'LLM Generation',
    subtitle: 'Ollama / Bedrock',
    description: "Le modèle de langage génère une réponse à partir de la question et des informations récupérées dans les étapes précédentes.",
    technical: "La fonction generate_answer(prompt) utilise le fournisseur LLM configuré, comme Ollama en local ou Amazon Bedrock sur AWS. Le modèle reçoit le contexte préparé, mais n'exécute pas lui-même les fonctions de recherche.",
  },
  {
    id: 'response',
    title: 'AI Response',
    subtitle: 'Total Execution Time',
    description: "FastAPI transmet la réponse générée à React, accompagnée des informations permettant d'identifier les sources utilisées.",
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

  const metrics = completedEvent?.data ?? latestEvent?.data ?? {}

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
        <span className="rag-explorer-badge">{executionStatus}</span>
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
        <div className="rag-technical">
          <strong>Technical implementation</strong>
          <p>{selectedStage.technical}</p>
        </div>

        {selectedId === 'pgvector' && (
          <div className="rag-cosine">
            <strong>Cosine Similarity</strong>
            <p>Similarity = (A · B) / (‖A‖ × ‖B‖)</p>
            <p>
              1 = même direction · 0 = vecteurs orthogonaux · −1 = directions opposées.
              Cette mesure compare l'orientation des vecteurs, et non le nombre de mots identiques.
            </p>
            <small>
              Le seuil de similarité actuel est fixé à 0,40.
              Cette explication présente le fonctionnement de l'algorithme,
              et non une mesure de similarité calculée en temps réel.
            </small>
          </div>
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
