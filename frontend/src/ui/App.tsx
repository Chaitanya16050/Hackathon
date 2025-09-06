import { useEffect, useMemo, useState } from 'react'

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const API_BASE = (import.meta as any).env?.VITE_API_BASE || 'http://localhost:8000'

type Citation = { doc_id: string; fragment?: string; score?: number }

type Snippet = { language: string; code: string }

type QA = {
  id: string
  question: string
  answer: string
  citations: Citation[]
  snippets: Snippet[]
}

function UploadDocs({ onDone }: { onDone: () => void }) {
  const [files, setFiles] = useState<FileList | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const submit = async () => {
    if (!files || files.length === 0) return
    setLoading(true)
    setError(null)
    const form = new FormData()
  Array.from(files).forEach((f: File) => form.append('files', f))
    const res = await fetch(`${API_BASE}/ingest`, { method: 'POST', body: form })
    if (!res.ok) {
      setError(`Ingest failed: ${res.status}`)
    }
    setLoading(false)
    onDone()
  }

  return (
    <div style={{ border: '1px solid #ddd', padding: 12, borderRadius: 8 }}>
      <h3>Ingest Docs</h3>
      <input type="file" multiple onChange={e => setFiles(e.target.files)} />
      <button onClick={submit} disabled={loading}>{loading ? 'Ingesting…' : 'Upload & Index'}</button>
      {error && <div style={{ color: 'red' }}>{error}</div>}
    </div>
  )
}

function Ask() {
  const [question, setQuestion] = useState('How do I create an invoice?')
  const [loading, setLoading] = useState(false)
  const [qa, setQa] = useState<QA | null>(null)

  const ask = async () => {
    if (!question.trim()) return
    setLoading(true)
    const res = await fetch(`${API_BASE}/qa`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question }) })
    setLoading(false)
    if (res.ok) setQa(await res.json())
  }

  return (
    <div style={{ border: '1px solid #ddd', padding: 12, borderRadius: 8, marginTop: 12 }}>
      <h3>Ask</h3>
      <input value={question} onChange={e => setQuestion(e.target.value)} style={{ width: '80%' }} />
      <button onClick={ask} disabled={loading}>{loading ? 'Thinking…' : 'Ask'}</button>
      {qa && <QAView qa={qa} />}
    </div>
  )
}

function CodeTabs({ snippets }: { snippets: Snippet[] }) {
  const [active, setActive] = useState(0)
  return (
    <div>
      <div style={{ display: 'flex', gap: 8 }}>
        {snippets.map((s, i) => (
          <button key={i} onClick={() => setActive(i)} style={{ fontWeight: i === active ? 700 : 400 }}>{s.language}</button>
        ))}
        <button onClick={() => navigator.clipboard.writeText(snippets[active]?.code || '')}>Copy</button>
      </div>
      <pre style={{ background: '#f7f7f7', padding: 12, overflow: 'auto' }}><code>{snippets[active]?.code}</code></pre>
    </div>
  )
}

function QAView({ qa }: { qa: QA }) {
  return (
    <div style={{ marginTop: 12 }}>
      <h4>Answer</h4>
      <p style={{ whiteSpace: 'pre-wrap' }}>{qa.answer}</p>
      <h4>Citations</h4>
      <ul>
        {qa.citations.map((c, i) => (
          <li key={i}>
            <span>Doc {c.doc_id}</span>{c.fragment ? ` — ${c.fragment}` : ''}
          </li>
        ))}
      </ul>
      <h4>Code</h4>
      <CodeTabs snippets={qa.snippets} />
    </div>
  )
}

function History() {
  const [items, setItems] = useState<{ id: string; question: string; created_at: string }[]>([])
  const [selected, setSelected] = useState<QA | null>(null)

  useEffect(() => {
    (async () => {
      const res = await fetch(`${API_BASE}/history`)
      if (res.ok) setItems(await res.json())
    })()
  }, [])

  const open = async (id: string) => {
    const res = await fetch(`${API_BASE}/history/${id}`)
    if (res.ok) setSelected(await res.json())
  }

  return (
    <div style={{ border: '1px solid #ddd', padding: 12, borderRadius: 8, marginTop: 12 }}>
      <h3>History</h3>
      <ul>
        {items.map(i => (
          <li key={i.id}>
            <button onClick={() => open(i.id)}>{i.question}</button>
          </li>
        ))}
      </ul>
      {selected && <QAView qa={selected} />}
    </div>
  )
}

export default function App() {
  const [refreshKey, setRefreshKey] = useState(0)
  return (
    <div style={{ fontFamily: 'system-ui, sans-serif', padding: 16, maxWidth: 900, margin: '0 auto' }}>
      <h2>API Doc Answerer + Snippet Generator</h2>
      <UploadDocs onDone={() => setRefreshKey(k => k + 1)} />
      <Ask />
      <History key={refreshKey} />
    </div>
  )
}
