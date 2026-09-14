// ═══════════════════════════════════════════════════════════════
// Music Streaming Data Explorer — Chat Logic
// ═══════════════════════════════════════════════════════════════

const chatArea = document.getElementById('chat-area');
const messagesEl = document.getElementById('messages');
const welcome = document.getElementById('welcome');
const userInput = document.getElementById('user-input');
const btnSend = document.getElementById('btn-send');
const btnClear = document.getElementById('btn-clear');
const modelSelect = document.getElementById('model-select');

let conversationHistory = [];
let isLoading = false;

// ── Auto-resize textarea ───────────────────────────────────
userInput.addEventListener('input', () => {
  userInput.style.height = 'auto';
  userInput.style.height = Math.min(userInput.scrollHeight, 150) + 'px';
  btnSend.disabled = !userInput.value.trim() || isLoading;
});

// ── Send on Enter (Shift+Enter for newline) ────────────────
userInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    if (!btnSend.disabled) sendMessage();
  }
});

btnSend.addEventListener('click', sendMessage);
btnClear.addEventListener('click', clearChat);

// ── Suggestion buttons ─────────────────────────────────────
document.querySelectorAll('.suggestion').forEach(btn => {
  btn.addEventListener('click', () => {
    userInput.value = btn.dataset.q;
    userInput.dispatchEvent(new Event('input'));
    sendMessage();
  });
});

// ── Send message ───────────────────────────────────────────
async function sendMessage() {
  const text = userInput.value.trim();
  if (!text || isLoading) return;

  isLoading = true;
  btnSend.disabled = true;

  // Hide welcome, show messages
  welcome.classList.add('hidden');

  // Add user message
  conversationHistory.push({ role: 'user', content: text });
  appendMessage('user', text);

  // Clear input
  userInput.value = '';
  userInput.style.height = 'auto';

  // Show typing indicator
  const typingEl = appendTyping();

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: conversationHistory,
        model: modelSelect.value
      })
    });

    // Remove typing indicator
    typingEl.remove();

    if (!response.ok) {
      const err = await response.json().catch(() => ({ error: 'Unknown error' }));
      throw new Error(err.error || `HTTP ${response.status}`);
    }

    const data = await response.json();
    conversationHistory.push({ role: 'assistant', content: data.reply });
    appendMessage('assistant', data.reply, data.model, data.code_executed, data.total_exec_time_ms);

  } catch (error) {
    typingEl.remove();
    appendError(error.message);
  }

  isLoading = false;
  btnSend.disabled = !userInput.value.trim();
  userInput.focus();
}

// ── Append user/assistant message ──────────────────────────
function appendMessage(role, content, modelName, codeExecuted, totalExecTimeMs) {
  const div = document.createElement('div');
  div.className = `message ${role}`;

  const avatarContent = role === 'user' ? 'You' : '♪';

  let codeDetailsHtml = '';
  if (codeExecuted && codeExecuted.length > 0) {
    codeDetailsHtml = `
      <details class="code-execution-details">
        <summary class="code-execution-summary">
          <span class="code-icon">⚡</span>
          <span class="code-title">Analyzed 10,058 rows using Pandas (${totalExecTimeMs || 2} ms)</span>
          <span class="code-toggle-label">View Code ▾</span>
        </summary>
        <div class="code-execution-body">
          ${codeExecuted.map(c => `
            <div class="code-block-item">
              <div class="code-block-header">
                <span>Python / Pandas Execution</span>
                <span>${c.time_ms} ms</span>
              </div>
              <pre class="code-snippet"><code>${escapeHtml(c.code)}</code></pre>
              ${c.output ? `
                <div class="code-output-header">Data Result:</div>
                <pre class="code-result"><code>${escapeHtml(c.output)}</code></pre>
              ` : ''}
            </div>
          `).join('')}
        </div>
      </details>
    `;
  }

  let html = `
    <div class="message-inner">
      <div class="message-avatar">${avatarContent}</div>
      <div class="message-content">
        ${codeDetailsHtml}
        ${role === 'assistant' ? renderMarkdown(content) : escapeHtml(content)}
        ${modelName ? `<div class="model-badge">${escapeHtml(modelName)}</div>` : ''}
      </div>
    </div>
  `;

  div.innerHTML = html;
  messagesEl.appendChild(div);
  scrollToBottom();
}

// ── Append typing indicator ────────────────────────────────
function appendTyping() {
  const div = document.createElement('div');
  div.className = 'message assistant';
  div.innerHTML = `
    <div class="message-inner">
      <div class="message-avatar">♪</div>
      <div class="message-content">
        <div class="typing-indicator">
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
        </div>
      </div>
    </div>
  `;
  messagesEl.appendChild(div);
  scrollToBottom();
  return div;
}

// ── Append error ───────────────────────────────────────────
function appendError(msg) {
  const div = document.createElement('div');
  div.className = 'message assistant';
  div.innerHTML = `
    <div class="message-inner">
      <div class="message-avatar">♪</div>
      <div class="message-content">
        <div class="error-msg">⚠️ ${escapeHtml(msg)}</div>
      </div>
    </div>
  `;
  messagesEl.appendChild(div);
  scrollToBottom();
}

// ── Clear chat ─────────────────────────────────────────────
function clearChat() {
  conversationHistory = [];
  messagesEl.innerHTML = '';
  welcome.classList.remove('hidden');
  userInput.focus();
}

// ── Scroll to bottom ───────────────────────────────────────
function scrollToBottom() {
  requestAnimationFrame(() => {
    chatArea.scrollTop = chatArea.scrollHeight;
  });
}

// ── Markdown cleaner & table unifier ──────────────────────
function cleanMarkdown(text) {
  if (!text) return '';

  // 1. Remove table rows that consist solely of pipes and whitespace (e.g. | | | | |)
  text = text.replace(/^\|[\s\|]+\|$/gm, (match) => {
    // Retain header separator rows like |---|---|
    if (/\|(?:\s*:?-+:?\s*\|)+/.test(match)) {
      return match;
    }
    return '';
  });

  // 2. Collapse blank lines occurring between table rows so tables never split
  let prev;
  do {
    prev = text;
    text = text.replace(/(\|[^\n]+\|)\r?\n(?:[ \t]*\r?\n)+(\|)/g, '$1\n$2');
  } while (text !== prev);

  // 3. Normalize multiple excessive blank lines
  text = text.replace(/(\r?\n){3,}/g, '\n\n');

  return text.trim();
}

// ── Markdown renderer ──────────────────────────────────────
function renderMarkdown(text) {
  if (!text) return '';

  const cleanedText = cleanMarkdown(text);

  if (typeof marked !== 'undefined') {
    try {
      marked.setOptions({
        gfm: true,
        breaks: false
      });
      return marked.parse(cleanedText);
    } catch (e) {
      console.warn('marked.js parse error, falling back:', e);
    }
  }

  // Fallback parser if marked is unavailable
  let html = escapeHtml(text);
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
  html = html.replace(/^#### (.+)$/gm, '<h4>$1</h4>');
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');
  html = html.replace(/^---$/gm, '<hr>');
  html = html.replace(/^[\-\*] (.+)$/gm, '<li>$1</li>');
  html = html.replace(/((?:<li>.*<\/li>\n?)+)/g, '<ul>$1</ul>');
  html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');
  return html;
}

// ── Escape HTML ────────────────────────────────────────────
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// ── Focus input on load ────────────────────────────────────
userInput.focus();
