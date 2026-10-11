export type RAGEvent = {
  event: string
  data: Record<string, unknown>
}

export async function streamRAG(
  apiUrl: string,
  question: string,
  onEvent: (event: RAGEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(`${apiUrl}/ai/ask/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
    },
    body: JSON.stringify({ question }),
    signal,
  })

  if (!response.ok) {
    throw new Error(`RAG streaming failed: HTTP ${response.status}`)
  }

  if (!response.body) {
    throw new Error('Streaming response body is unavailable')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()

  let buffer = ''

  const processFrame = (frame: string) => {
    let eventName = 'message'
    const dataLines: string[] = []

    for (const line of frame.split('\n')) {
      if (line.startsWith('event:')) {
        eventName = line.slice(6).trim()
      }

      if (line.startsWith('data:')) {
        dataLines.push(line.slice(5).trimStart())
      }
    }

    if (!dataLines.length) return

    const data = JSON.parse(dataLines.join('\n'))

    onEvent({
      event: eventName,
      data,
    })
  }

  const processBuffer = () => {
    buffer = buffer.replace(/\r\n/g, '\n')

    let boundary = buffer.indexOf('\n\n')

    while (boundary !== -1) {
      const frame = buffer.slice(0, boundary)
      buffer = buffer.slice(boundary + 2)

      processFrame(frame)

      boundary = buffer.indexOf('\n\n')
    }
  }

  try {
    while (true) {
      const { done, value } = await reader.read()

      if (done) break


      buffer += decoder.decode(value, { stream: true })
      processBuffer()
    }

    buffer += decoder.decode()
    processBuffer()

    if (buffer.trim()) {
      processFrame(buffer)
    }
  } finally {
    reader.releaseLock()
  }
}
