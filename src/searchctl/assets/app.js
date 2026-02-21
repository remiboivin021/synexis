async function api(path, payload) {
  const opts = payload ? { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload) } : {};
  const res = await fetch(path, opts);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || data.detail || ('HTTP ' + res.status));
  return data;
}

function setText(id, text) { document.getElementById(id).textContent = text || ''; }

async function runSearch() {
  const query = document.getElementById('query').value.trim();
  if (!query) return;
  const summarize = document.getElementById('summarize').checked;
  const use_hybrid = document.getElementById('useHybrid').checked;
  try {
    const out = await api('/api/search', {query, summarize, use_hybrid});
    const summaryTarget = document.getElementById('summary');
    if (summarize && out.summary_html) {
      summaryTarget.innerHTML = out.summary_html;
    } else {
      summaryTarget.textContent = summarize ? (out.summary || '') : '';
    }
    const root = document.getElementById('results');
    root.innerHTML = '';
    for (const row of out.results || []) {
      const li = document.createElement('li');
      li.innerHTML = '<strong>#' + row.rank + ' ' + (row.doc_title || '(untitled)') + '</strong><br>' +
        '<span class="muted">' + (row.doc_path || '') + '</span><br>' +
        (row.snippet || '') + '<br>' +
        '<span class="muted">chunk=' + (row.citation?.chunk_id || '') + '</span>';
      root.appendChild(li);
    }
  } catch (err) {
    setText('summary', String(err));
  }
}

async function loadDocs() {
  try {
    const out = await api('/api/documents');
    const root = document.getElementById('docs');
    root.innerHTML = '';
    for (const doc of out.documents || []) {
      const li = document.createElement('li');
      li.textContent = (doc.title || '(untitled)') + ' [' + (doc.source_type || '?') + ']';
      li.title = doc.path || '';
      li.onclick = () => openDoc(doc.doc_id);
      root.appendChild(li);
    }
  } catch (err) {
    setText('docContent', String(err));
  }
}

async function openDoc(docId) {
  try {
    const out = await api('/api/documents/' + encodeURIComponent(docId));
    const target = document.getElementById('docContent');
    if (out.source_type === 'markdown' && out.rendered_html) {
      target.innerHTML = out.rendered_html;
    } else {
      target.textContent = out.content || '';
    }
  } catch (err) {
    setText('docContent', String(err));
  }
}

document.getElementById('searchBtn').onclick = runSearch;
document.getElementById('refreshBtn').onclick = loadDocs;
document.getElementById('query').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') runSearch();
});
loadDocs();
