import { useState } from 'react'
import type { FormEvent } from 'react'

type Source = {
  id: number
  title: string
  source: string
  similarity: number
}

type DataSource = {
  type: 'postgresql' | 'pgvector'
  label: string
}

type AIResponse = {
  answer: string
  sources: Source[]
  data_sources: DataSource[]
}

function AIAssistant() {
  const [question, setQuestion] = useState('')
  const [response, setResponse] = useState<AIResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const askAI = async (event: FormEvent) => {
    event.preventDefault()

    if (!question.trim()) {
      return
    }

    setLoading(true)
    setError('')
    setResponse(null)

    try {
      const apiResponse = await fetch('http://localhost:8000/ai/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: question.trim(),
        }),
      })

      if (!apiResponse.ok) {
        throw new Error('AI request failed')
      }

      const data: AIResponse = await apiResponse.json()
      setResponse(data)
    } catch {
      setError(
        'Unable to contact the AI service. Check FastAPI and Ollama.',
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="ai-assistant-page">
      <div className="section-heading">
        <div>
          <p className="eyebrow">POSTGRESQL / RAG / PGVECTOR / LLAMA</p>
          <h3>AI Supply Chain Assistant</h3>
          <p>
            Ask operational questions using structured supply chain data,
            semantic retrieval and local Llama inference.
          </p>
        </div>

        <div className="ai-stack-badge">
          <span className="status-dot"></span>
          RAG Pipeline Ready
        </div>
      </div>

      <div className="ai-layout">
        <div className="card ai-query-card">
          <p className="eyebrow">ASK THE KNOWLEDGE BASE</p>

          <form onSubmit={askAI}>
            <textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Ask a supply chain question..."
              rows={5}
            />

            <div className="ai-query-footer">
              <span>PostgreSQL + MiniLM → pgvector → Llama</span>

              <button
                type="submit"
                disabled={loading || !question.trim()}
              >
                {loading ? 'Analyzing...' : 'Ask AI →'}
              </button>
            </div>
          </form>

          <div className="suggested-question">
            <span>Try an example</span>

            <button
              type="button"
              onClick={() =>
                setQuestion(
                  'Which supplier has recurring delivery delays?',
                )
              }
            >
              Which supplier has recurring delivery delays?
            </button>
          </div>
        </div>

        <div className="card ai-response-card">
          <p className="eyebrow">AI RESPONSE</p>

          {!response && !loading && !error && (
            <div className="empty-response">
              <div className="ai-symbol">✦</div>

              <h3>Ready for analysis</h3>

              <p>
                Ask a question to retrieve relevant knowledge and generate
                a grounded answer.
              </p>
            </div>
          )}

          {loading && (
            <div className="empty-response">
              <div className="ai-symbol loading-symbol">✦</div>

              <h3>Analyzing knowledge...</h3>

              <p>
                Analyzing PostgreSQL and pgvector context with Llama.
              </p>
            </div>
          )}

          {error && (
            <div className="ai-error">
              <strong>AI service unavailable</strong>
              <p>{error}</p>
            </div>
          )}

          {response && (
            <>
              <div className="answer-block">
                <span>Answer</span>
                <p>{response.answer}</p>
              </div>

              <div className="sources-header">
                <span>Data Sources</span>
                <small>{response.data_sources.length} active</small>
              </div>

              <div className="source-list">
                {response.data_sources.map((source) => (
                  <div
                    className="source-item"
                    key={source.type}
                  >
                    <div>
                      <strong>
                        {source.type === 'postgresql'
                          ? 'PostgreSQL'
                          : 'pgvector'}
                      </strong>
                      <small>{source.label}</small>
                    </div>

                    <div className="similarity">
                      {source.type === 'postgresql'
                        ? 'STRUCTURED'
                        : 'SEMANTIC'}
                    </div>
                  </div>
                ))}
              </div>

              {response.sources.length > 0 && (
                <>
                  <div className="sources-header">
                    <span>Retrieved Knowledge</span>
                    <small>
                      {response.sources.length} results
                    </small>
                  </div>

                  <div className="source-list">
                    {response.sources.map((source) => (
                      <div
                        className="source-item"
                        key={source.id}
                      >
                        <div>
                          <strong>{source.title}</strong>
                          <small>{source.source}</small>
                        </div>

                        <div className="similarity">
                          {(source.similarity * 100).toFixed(1)}%
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </>
          )}
        </div>
      </div>
    </section>
  )
}

export default AIAssistant
