async function api(path, payload) {
  const opts = payload
    ? {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      }
    : {};
  const res = await fetch(path, opts);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || data.detail || ('HTTP ' + res.status));
  return data;
}

function byId(id) {
  return document.getElementById(id);
}

function escapeHtml(text) {
  return String(text || '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function formatErrorMessage(err) {
  const raw = err instanceof Error && err.message ? err.message : String(err || '');
  const oneLine = raw.replace(/[{}[\]"]/g, ' ').replace(/\s+/g, ' ').trim();
  const lower = oneLine.toLowerCase();
  const statusMatch = oneLine.match(/\b([1-5]\d{2})\b/);
  const statusCode = statusMatch ? statusMatch[1] : '';

  if (!oneLine) return 'Erreur serveur';
  if (lower.includes('failed to fetch') || lower.includes('networkerror')) return 'Serveur inaccessible';
  if (lower.includes('timeout')) return 'Délai dépassé';
  if (lower.includes('http 400') || lower.includes('unprocessable') || lower.includes('422') || statusCode === '400' || statusCode === '422') {
    return 'Requête invalide';
  }
  if (lower.includes('http 401') || lower.includes('http 403') || statusCode === '401' || statusCode === '403') return 'Accès refusé';
  if (lower.includes('http 402') || statusCode === '402') return 'Crédit API insuffisant';
  if (lower.includes('http 404') || statusCode === '404') return 'Ressource introuvable';
  if (lower.includes('http 409') || statusCode === '409') return 'Conflit de requête';
  if (lower.includes('http 429') || statusCode === '429') return 'Trop de requêtes';
  if (
    lower.includes('http 500') ||
    lower.includes('http 502') ||
    lower.includes('http 503') ||
    lower.includes('http 504') ||
    statusCode === '500' ||
    statusCode === '502' ||
    statusCode === '503' ||
    statusCode === '504'
  ) {
    return 'Erreur interne serveur';
  }
  if (lower.includes('qdrant')) return 'Service vectoriel indisponible';
  if (lower.includes('opensearch') || lower.includes('tantivy')) return 'Index de recherche indisponible';

  const concise = oneLine.split(':').pop().trim();
  return concise || 'Erreur serveur';
}

function showErrorToast(message) {
  const container = byId('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = [
    'pointer-events-auto',
    'max-w-sm',
    'bg-red-600/95',
    'text-red-50',
    'border',
    'border-red-300/40',
    'rounded-xl',
    'shadow-2xl',
    'px-4',
    'py-3',
    'text-sm',
    'font-medium',
    'translate-x-12',
    'opacity-0',
    'transition-all',
    'duration-300',
    'ease-out',
  ].join(' ');
  toast.innerHTML = `<div class="flex items-start gap-2">
    <i class="fas fa-triangle-exclamation mt-0.5"></i>
    <div>Erreur backend: ${message}</div>
  </div>`;
  container.appendChild(toast);

  requestAnimationFrame(() => {
    toast.classList.remove('translate-x-12', 'opacity-0');
    toast.classList.add('translate-x-0', 'opacity-100');
  });

  setTimeout(() => {
    toast.classList.remove('translate-x-0', 'opacity-100');
    toast.classList.add('-translate-x-3', 'opacity-0');
    setTimeout(() => toast.remove(), 320);
  }, 4200);
}

function setText(id, text) {
  const el = byId(id);
  if (el) el.textContent = text || '';
}

function sourceTypeLabel(sourceType) {
  if (sourceType === 'pdf') return 'PDF';
  if (sourceType === 'markdown') return 'MARKDOWN';
  return (sourceType || 'TEXT').toUpperCase();
}

function sourceTypeIcon(sourceType) {
  if (sourceType === 'pdf') return 'fa-file-pdf text-red-400';
  return 'fa-file-alt text-blue-400';
}

function openPanel() {
  const panel = byId('side-panel');
  const overlay = byId('panel-overlay');
  if (!panel || !overlay) return;
  panel.classList.remove('translate-x-full');
  overlay.classList.remove('hidden');
}

function closePanel() {
  const panel = byId('side-panel');
  const overlay = byId('panel-overlay');
  if (!panel || !overlay) return;
  panel.classList.add('translate-x-full');
  overlay.classList.add('hidden');
}

async function loadDocuments() {
  const list = byId('document-list');
  if (!list) return;

  try {
    const out = await api('/api/documents');
    const docs = out.documents || [];
    list.innerHTML = '';

    if (!docs.length) {
      const empty = document.createElement('div');
      empty.className = 'p-3 rounded-lg border border-slate-700 text-sm text-slate-500';
      empty.textContent = 'Aucun document indexé';
      list.appendChild(empty);
      setText('doc-count', '0 document indexé');
      return;
    }

    for (const doc of docs) {
      const row = document.createElement('div');
      row.className = 'p-3 rounded-lg hover:bg-slate-800 cursor-pointer transition-colors flex items-center gap-3 group';
      row.innerHTML = `
        <i class="far ${sourceTypeIcon(doc.source_type)}"></i>
        <span class="text-sm text-slate-300 group-hover:text-white truncate">${doc.title || '(untitled)'}</span>
      `;
      row.title = doc.path || '';
      row.onclick = () => openDocument(doc.doc_id, doc.title || '(untitled)');
      list.appendChild(row);
    }

    setText('doc-count', `${docs.length} document${docs.length > 1 ? 's' : ''} indexé${docs.length > 1 ? 's' : ''}`);
  } catch (err) {
    const msg = formatErrorMessage(err);
    showErrorToast(msg);
  }
}

async function openDocument(docId, fallbackTitle) {
  try {
    const out = await api('/api/documents/' + encodeURIComponent(docId));
    const title = out.title || fallbackTitle || 'Document';
    const panelType = byId('panel-type');
    const panelTitle = byId('panel-title');
    const panelContent = byId('panel-content');
    const panelOpenOriginal = byId('panel-open-original');

    const queryInput = byId('search-input');
    if (queryInput) queryInput.value = title;

    if (panelType) panelType.textContent = sourceTypeLabel(out.source_type || 'text');
    if (panelTitle) panelTitle.textContent = title;
    if (panelContent) {
      if (out.rendered_html) {
        panelContent.innerHTML = out.rendered_html;
      } else {
        panelContent.innerHTML = `<pre class="whitespace-pre-wrap break-words text-slate-300">${escapeHtml(out.content || '')}</pre>`;
      }
    }
    if (panelOpenOriginal) {
      const docPath = out.path || '';
      panelOpenOriginal.onclick = () => {
        if (!docPath) return;
        window.open(`file://${encodeURI(docPath)}`, '_blank', 'noopener');
      };
      panelOpenOriginal.disabled = !docPath;
      panelOpenOriginal.classList.toggle('opacity-50', !docPath);
      panelOpenOriginal.classList.toggle('cursor-not-allowed', !docPath);
    }

    openPanel();
  } catch (err) {
    const msg = formatErrorMessage(err);
    showErrorToast(msg);
  }
}

async function typeWriter(target, text) {
  target.classList.add('typing-cursor');
  target.textContent = '';
  for (let i = 0; i < text.length; i += 1) {
    target.textContent += text.charAt(i);
    await new Promise((r) => setTimeout(r, 8));
  }
  target.classList.remove('typing-cursor');
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function buildWordStreamsFromHtml(html) {
  const tpl = document.createElement('template');
  tpl.innerHTML = html;
  const streams = [];

  function cloneNode(node) {
    if (node.nodeType === Node.TEXT_NODE) {
      const textNode = document.createTextNode('');
      const tokens = (node.textContent || '').match(/\S+\s*/g) || [];
      if (tokens.length) streams.push({ target: textNode, tokens });
      return textNode;
    }
    if (node.nodeType === Node.ELEMENT_NODE) {
      const el = node.cloneNode(false);
      for (const child of node.childNodes) {
        el.appendChild(cloneNode(child));
      }
      return el;
    }
    return document.createTextNode('');
  }

  const fragment = document.createDocumentFragment();
  for (const child of tpl.content.childNodes) {
    fragment.appendChild(cloneNode(child));
  }
  return { fragment, streams };
}

async function renderSummaryHtmlWordByWord(target, html) {
  target.innerHTML = '';
  const { fragment, streams } = buildWordStreamsFromHtml(html);
  if (!streams.length) {
    target.innerHTML = html;
    return;
  }
  target.appendChild(fragment);
  target.classList.add('typing-cursor');

  let wordCount = streams.reduce((acc, s) => acc + s.tokens.length, 0);
  const delay = wordCount > 220 ? 18 : 42;
  for (const stream of streams) {
    for (const token of stream.tokens) {
      stream.target.textContent += token;
      await sleep(delay);
    }
  }
  target.classList.remove('typing-cursor');
}

function renderSources(results, sources) {
  const container = byId('sources-container');
  const grid = byId('sources-grid');
  if (!container || !grid) return;

  grid.innerHTML = '';
  const items = (sources && sources.length ? sources : []).slice(0, 8);

  if (!items.length) {
    container.classList.add('hidden');
    return;
  }

  for (const src of items) {
    const card = document.createElement('div');
    card.className = 'bg-slate-800/30 p-4 rounded-xl border border-slate-700 hover:border-indigo-500 transition-colors';
    card.innerHTML = `
      <div class="text-[10px] text-indigo-400 font-bold uppercase mb-1">SOURCE</div>
      <div class="text-sm font-medium text-slate-200 truncate">${src.doc_title || '(untitled)'}</div>
      <div class="text-xs text-slate-500 mt-2 truncate">${src.doc_path || ''}</div>
      <div class="text-xs text-slate-500 mt-1">chunk=${src.chunk_id || ''} [${src.start_char ?? '-'}:${src.end_char ?? '-'}]</div>
    `;
    grid.appendChild(card);
  }

  container.classList.remove('hidden');
}

async function runSearch() {
  const queryInput = byId('search-input');
  const query = queryInput ? queryInput.value.trim() : '';
  if (!query) return;

  const loader = byId('loader');
  const synthContainer = byId('synthesis-container');
  const synthText = byId('synthesis-text');
  const sourcesContainer = byId('sources-container');

  if (loader) loader.classList.remove('hidden');
  if (synthContainer) synthContainer.classList.add('hidden');
  if (sourcesContainer) sourcesContainer.classList.add('hidden');
  if (synthText) synthText.textContent = '';

  try {
    const out = await api('/api/search', {
      query,
      summarize: true,
      use_hybrid: false,
      summary_top_k: 8,
    });

    if (loader) loader.classList.add('hidden');
    if (synthContainer) synthContainer.classList.remove('hidden');

    const summaryRaw = out.summary || 'Aucune synthèse disponible.';
    if (synthText) {
      if (out.summary_html) {
        await renderSummaryHtmlWordByWord(synthText, out.summary_html);
      } else {
        await typeWriter(synthText, summaryRaw);
      }
    }

    renderSources(out.results || [], out.sources || []);
  } catch (err) {
    const msg = formatErrorMessage(err);
    if (loader) loader.classList.add('hidden');
    if (synthContainer) synthContainer.classList.add('hidden');
    if (sourcesContainer) sourcesContainer.classList.add('hidden');
    showErrorToast(msg);
  }
}

function init() {
  const searchBtn = byId('search-btn');
  const searchInput = byId('search-input');

  if (searchBtn) searchBtn.addEventListener('click', runSearch);
  if (searchInput) {
    searchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') runSearch();
    });
  }

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closePanel();
  });

  window.closePanel = closePanel;

  loadDocuments();
}

init();
