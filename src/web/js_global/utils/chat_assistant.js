/**
 * Chat Assistant - Prompt playground with optional AI backend
 * When backend is unavailable: copy prompts, use templates, open external AI
 */
window.UtilsTools = window.UtilsTools || {};
window.UtilsTools['chat-assistant'] = {
  API_URL: 'https://nori.fish/api/chat',
  TEMPLATES: [
    { label: 'Summarize', prompt: 'Summarize the following in 2-3 sentences:' },
    { label: 'Explain simply', prompt: 'Explain the following in simple terms:' },
    { label: 'Code help', prompt: 'Help me with this code. Explain what it does and suggest improvements:' },
    { label: 'Rewrite', prompt: 'Rewrite the following to be clearer and more concise:' },
    { label: 'Brainstorm', prompt: 'Brainstorm 5 ideas for: ' },
    { label: 'Translate', prompt: 'Translate to English (keep technical terms if needed):' }
  ],
  init: function(container) {
    var self = this;
    container.innerHTML =
      '<a href="#" class="utils-back-link" data-utils-back>← Back to Utils</a>' +
      '<h1 class="utils-tool-title">💬 Chat Assistant</h1>' +
      '<p class="utils-subtitle" style="color:var(--utils-text-dim);font-size:0.85rem;margin-bottom:1rem">Compose prompts and get AI help. When our API is available, responses appear here. Otherwise, copy and paste into ChatGPT or Claude.</p>' +
      '<div class="utils-options" style="margin-bottom:1rem">' +
        '<label>Quick templates</label>' +
        '<div class="utils-btns" id="chat-templates"></div>' +
      '</div>' +
      '<label>Your message</label>' +
      '<textarea id="chat-input" class="utils-textarea" placeholder="Type your prompt..." style="min-height:120px"></textarea>' +
      '<div class="utils-btns" style="margin-top:0.5rem">' +
        '<button class="utils-btn" id="chat-send">Send (try API)</button>' +
        '<button class="utils-btn secondary" id="chat-copy">Copy to clipboard</button>' +
        '<button class="utils-btn secondary" id="chat-clear">Clear history</button>' +
        '<a href="https://chat.openai.com" target="_blank" rel="noopener" class="utils-btn secondary">Open ChatGPT</a>' +
        '<a href="https://claude.ai" target="_blank" rel="noopener" class="utils-btn secondary">Open Claude</a>' +
      '</div>' +
      '<div class="utils-status" id="chat-status"></div>' +
      '<div id="chat-history" class="utils-box" style="margin-top:1.5rem;max-height:400px;overflow-y:auto"></div>';

    var back = container.querySelector('[data-utils-back]');
    back.onclick = function(e) { e.preventDefault(); location.hash = '#'; };

    var input = container.querySelector('#chat-input');
    var historyEl = container.querySelector('#chat-history');
    var statusEl = container.querySelector('#chat-status');

    function loadHistory() {
      try {
        var s = localStorage.getItem('nori-chat-history');
        return s ? JSON.parse(s) : [];
      } catch (_) { return []; }
    }
    function saveHistory(hist) {
      try {
        localStorage.setItem('nori-chat-history', JSON.stringify(hist.slice(-50)));
      } catch (_) {}
    }
    function renderHistory() {
      var hist = loadHistory();
      if (hist.length === 0) {
        historyEl.innerHTML = '<p style="color:var(--utils-text-dim);font-size:0.9rem">No messages yet. Send a message or use a template.</p>';
        return;
      }
      historyEl.innerHTML = hist.map(function(m) {
        return '<div class="utils-result" style="margin-bottom:0.75rem"><strong>' + (m.sender === 'user' ? 'You' : 'Nori') + ':</strong> ' + escapeHtml(m.text) + '</div>';
      }).join('');
      historyEl.scrollTop = historyEl.scrollHeight;
    }
    function escapeHtml(s) {
      var d = document.createElement('div');
      d.textContent = s;
      return d.innerHTML;
    }
    function addToHistory(sender, text) {
      var hist = loadHistory();
      hist.push({ sender: sender, text: text });
      saveHistory(hist);
      renderHistory();
    }

    self.TEMPLATES.forEach(function(t) {
      var btn = document.createElement('button');
      btn.className = 'utils-btn secondary';
      btn.textContent = t.label;
      btn.onclick = function() {
        input.value = (input.value ? input.value + '\n\n' : '') + t.prompt + '\n';
        input.focus();
      };
      container.querySelector('#chat-templates').appendChild(btn);
    });

    container.querySelector('#chat-send').onclick = function() {
      var text = input.value.trim();
      if (!text) {
        statusEl.textContent = 'Enter a message first';
        statusEl.className = 'utils-status err';
        return;
      }
      addToHistory('user', text);
      input.value = '';
      statusEl.textContent = 'Sending...';
      statusEl.className = 'utils-status loading';
      fetch(self.API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_input: text })
      }).then(function(r) {
        if (!r.ok) throw new Error('API unavailable');
        return r.json();
      }).then(function(data) {
        var reply = (data.output || '').trim();
        addToHistory('assistant', reply);
        statusEl.textContent = '';
        statusEl.className = 'utils-status';
      }).catch(function() {
        addToHistory('assistant', '[API unavailable] Copy your message and paste it into ChatGPT or Claude for a response.');
        statusEl.textContent = 'API unavailable. Use "Copy to clipboard" then paste into ChatGPT or Claude.';
        statusEl.className = 'utils-status err';
      });
    };

    container.querySelector('#chat-clear').onclick = function() {
      if (confirm('Clear chat history?')) {
        localStorage.removeItem('nori-chat-history');
        renderHistory();
        statusEl.textContent = 'History cleared';
        statusEl.className = 'utils-status ok';
        setTimeout(function() { statusEl.textContent = ''; }, 1500);
      }
    };

    container.querySelector('#chat-copy').onclick = function() {
      var text = input.value.trim();
      if (!text) {
        statusEl.textContent = 'Nothing to copy';
        statusEl.className = 'utils-status err';
        return;
      }
      navigator.clipboard.writeText(text).then(function() {
        statusEl.textContent = 'Copied to clipboard!';
        statusEl.className = 'utils-status ok';
        setTimeout(function() { statusEl.textContent = ''; }, 2000);
      }).catch(function() {
        statusEl.textContent = 'Copy failed';
        statusEl.className = 'utils-status err';
      });
    };

    renderHistory();
  },
  destroy: function() {}
};
