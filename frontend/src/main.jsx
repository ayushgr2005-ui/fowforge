import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_KEY = import.meta.env.VITE_API_KEY || '';

async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (API_KEY) headers.set('X-API-Key', API_KEY);
  const response = await fetch(API + path, { ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || data.detail || `Request failed (${response.status})`);
  return data;
}

function App() {
  const [docs, setDocs] = useState([]);
  const [q, setQ] = useState('');
  const [answer, setAnswer] = useState('');
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [apiStatus, setApiStatus] = useState('checking');

  const load = async () => {
    try { setDocs(await api('/api/documents')); } catch (e) { setError(e.message); }
  };

  useEffect(() => {
    api('/api/health').then(() => setApiStatus('connected')).catch(() => setApiStatus('offline'));
    load();
  }, []);

  async function upload(e) {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true); setError('');
    try {
      const fd = new FormData();
      fd.append('file', file);
      await api('/api/documents', { method: 'POST', body: fd });
      await load();
    } catch (err) { setError(err.message); }
    finally { setUploading(false); e.target.value = ''; }
  }

  async function remove(id) {
    try { await api(`/api/documents/${id}`, { method: 'DELETE' }); await load(); }
    catch (err) { setError(err.message); }
  }

  async function ask() {
    if (!q.trim() || loading) return;
    setLoading(true); setAnswer(''); setSources([]); setError('');
    try {
      const response = await fetch(API + '/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...(API_KEY ? { 'X-API-Key': API_KEY } : {}) },
        body: JSON.stringify({ question: q.trim() })
      });
      if (!response.ok) throw new Error(`Request failed (${response.status})`);
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split('\n\n');
        buffer = events.pop();
        for (const event of events) {
          const line = event.split('\n').find(x => x.startsWith('data: '));
          if (!line) continue;
          const payload = JSON.parse(line.slice(6));
          if (payload.type === 'sources') setSources(payload.sources || []);
          if (payload.type === 'token') setAnswer(prev => prev + payload.text);
        }
      }
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  }

  return <div className="shell">
    <aside>
      <div className="brand"><div className="logo">F</div><div><h1>FowForge</h1><p>AI knowledge platform</p></div></div>
      <label className="upload">{uploading ? 'Indexing…' : '+ Add knowledge'}<input type="file" accept=".txt,.md,.pdf" onChange={upload} disabled={uploading}/></label>
      <div className="section-title">Knowledge base <span>{docs.length}</span></div>
      <div className="docs">{docs.map(d => <div className="doc" key={d.id}><div title={d.name}>{d.name}</div><button onClick={() => remove(d.id)} title="Delete">×</button></div>)}</div>
      <div className="side-note">TXT · MD · PDF<br/>Embeddings · pgvector · RAG</div>
    </aside>
    <main>
      <div className="top"><span>AI Workspace</span><span className={`status ${apiStatus}`}>● {apiStatus === 'connected' ? 'API connected' : apiStatus}</span></div>
      <section className="hero"><div className="eyebrow">GROUNDED AI</div><h2>Ask your knowledge base.</h2><p>Answers are generated from indexed documents with traceable source references.</p></section>
      {error && <div className="error">{error}</div>}
      <div className="chat">
        {answer && <div className="answer"><div className="label">FowForge · grounded answer</div><div className="body">{answer}</div>{sources.length > 0 && <div className="sources"><b>Sources</b>{sources.map(s => <div key={s.chunk_id}><span>{s.source_id}</span> {s.document}</div>)}</div>}</div>}
        {loading && <div className="answer thinking"><div className="label">FowForge</div>Generating grounded response…</div>}
      </div>
      <div className="composer"><textarea value={q} onChange={e => setQ(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); ask(); } }} placeholder="Ask something about your knowledge base…"/><button onClick={ask} disabled={loading || !q.trim()}>Ask</button></div>
    </main>
  </div>;
}

createRoot(document.getElementById('root')).render(<App />);
