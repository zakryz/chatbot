const chatWindow = document.getElementById('chat-window');
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const welcomeState = document.getElementById('welcome-state');
const chatState = document.getElementById('chat-state');
const welcomeForm = document.getElementById('welcome-form');
const welcomeInput = document.getElementById('welcome-input');
const selectedModelInput = document.getElementById('selected-model');
let messages = [];
let streamController = null;
let isStreaming = false;

function updateWelcomeState() {
  if (messages.length === 0) {
    welcomeState.style.display = 'flex';
    chatState.style.display = 'none';
    chatForm.classList.add('hidden');
  } else {
    welcomeState.style.display = 'none';
    chatState.style.display = 'flex';
    chatForm.classList.remove('hidden');
  }
}

function showChatState() {
  welcomeState.classList.add('hidden');
  chatState.classList.remove('hidden');
  chatForm.classList.remove('hidden');
}

function renderMarkdownWithMath(text) {
  marked.setOptions({
    gfm: true,
    breaks: true,
    smartLists: true,
    smartypants: true,
    highlight: function(code, lang) {
      // highlight.js will handle highlighting after rendering
      return code;
    }
  });
  let html = marked.parse(text || "");
  // Add copy button to each code block (top-right)
  const tempDiv = document.createElement('div');
  tempDiv.innerHTML = html;
  tempDiv.querySelectorAll('pre > code').forEach((codeBlock) => {
    const pre = codeBlock.parentElement;
    if (pre.querySelector('.copy-btn')) return;
    pre.style.position = 'relative';
    const btn = document.createElement('button');
    btn.className = 'copy-btn';
    btn.type = 'button';
    btn.innerText = 'Copy';
    btn.setAttribute('aria-label', 'Copy code');
    btn.onclick = function() {
      navigator.clipboard.writeText(codeBlock.innerText);
      btn.innerText = 'Copied!';
      setTimeout(() => { btn.innerText = 'Copy'; }, 1200);
    };
    pre.appendChild(btn);
    // Ensure code color is applied (handled by CSS)
  });
  // Highlight code blocks using highlight.js
  setTimeout(() => {
    if (window.hljs) window.hljs.highlightAll();
  }, 0);
  return tempDiv.innerHTML;
}

// Optional: Switch highlight.js theme on mode toggle
document.addEventListener("DOMContentLoaded", function () {
  const body = document.getElementById('body-root');
  const hljsDark = document.getElementById('hljs-theme-dark');
  const hljsLight = document.getElementById('hljs-theme-light');
  function updateHljsTheme() {
    if (body.classList.contains('light')) {
      hljsDark.disabled = true;
      hljsLight.disabled = false;
    } else {
      hljsDark.disabled = false;
      hljsLight.disabled = true;
    }
  }
  updateHljsTheme();
  // Listen for mode changes (mode-toggle.js should toggle body class)
  const observer = new MutationObserver(updateHljsTheme);
  observer.observe(body, { attributes: true, attributeFilter: ['class'] });
});

function appendMessage(role, content) {
  updateWelcomeState();

  const wrapper = document.createElement('div');
  wrapper.className = role === 'user'
    ? "flex justify-end"
    : "flex justify-start";
  const bubble = document.createElement('div');
  bubble.className = role === 'user'
    ? "bg-[var(--brown)] text-[var(--offwhite)] px-4 py-3 rounded-2xl rounded-br-md max-w-[75%] shadow"
    : "bg-[var(--beige)] text-[var(--dark)] px-4 py-3 rounded-2xl rounded-bl-md max-w-[75%] shadow";
  if (role === 'assistant') {
    bubble.innerHTML = renderMarkdownWithMath(content);
  } else {
    bubble.innerHTML = content;
  }
  wrapper.appendChild(bubble);
  chatWindow.appendChild(wrapper);
  chatWindow.scrollTo({ top: chatWindow.scrollHeight, behavior: 'smooth' }); // smooth scroll
  if (role === 'assistant' && window.MathJax) {
    MathJax.typesetPromise([bubble]);
  }
}

function setInputStateStreaming(streaming) {
  isStreaming = streaming;
  userInput.disabled = streaming;
  const btn = chatForm.querySelector('button[type="submit"]');
  if (streaming) {
    btn.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <rect x="6" y="6" width="12" height="12" rx="2" fill="currentColor" />
      </svg>
    `;
    btn.title = "Stop response";
  } else {
    btn.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M12 5l7 7-7 7" />
      </svg>
    `;
    btn.title = "Send";
  }
}

async function sendMessage(content) {
  appendMessage('user', content);
  messages.push({ role: 'user', content });

  updateWelcomeState();
  const wrapper = document.createElement('div');
  wrapper.className = "flex justify-start";
  const bubble = document.createElement('div');
  bubble.className = "bg-[var(--beige)] text-[var(--dark)] px-4 py-3 rounded-2xl rounded-bl-md max-w-[75%] shadow";
  bubble.innerHTML = '<span class="italic text-gray-400">Thinking...</span>';
  wrapper.appendChild(bubble);
  chatWindow.appendChild(wrapper);
  chatWindow.scrollTop = chatWindow.scrollHeight;

  setInputStateStreaming(true);

  try {
    const model = selectedModelInput ? selectedModelInput.value : 'llama-3.3-70b-versatile';
    streamController = new AbortController();
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages, model: model, max_tokens: 800 }),
      signal: streamController.signal
    });

    if (!res.body || !window.ReadableStream) {
      bubble.innerHTML = '<span class="text-red-500">Streaming not supported.</span>';
      setInputStateStreaming(false);
      return;
    }

    bubble.innerHTML = '';
    let assistantContent = '';
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let done = false;
    while (!done && isStreaming) {
      const { value, done: doneReading } = await reader.read();
      done = doneReading;
      if (value) {
        const chunk = decoder.decode(value, { stream: true });
        chunk.split('\n').forEach(line => {
          if (line.startsWith('data:')) {
            try {
              const data = JSON.parse(line.replace('data: ', '').replace('data:', ''));
              if (data.delta) {
                assistantContent += data.delta;
                bubble.innerHTML = renderMarkdownWithMath(assistantContent);
                chatWindow.scrollTop = chatWindow.scrollHeight;
                if (window.MathJax) MathJax.typesetPromise([bubble]);
              }
              if (data.error) {
                bubble.innerHTML = `<span class="text-red-500">${data.error}</span>`;
              }
            } catch (e) {
            }
          }
        });
      }
    }
    if (assistantContent.trim() !== "") {
      messages.push({ role: 'assistant', content: assistantContent });
    } else if (!bubble.innerHTML) {
      bubble.innerHTML = '<span class="text-red-500">No response from assistant.</span>';
    }
    if (window.MathJax) MathJax.typesetPromise([bubble]);
  } catch (err) {
    if (err.name === 'AbortError') {
      bubble.innerHTML += '<span class="text-gray-400 ml-2">(stopped)</span>';
    } else {
      bubble.innerHTML = '<span class="text-red-500">Error: Could not get response.</span>';
    }
  } finally {
    setInputStateStreaming(false);
    streamController = null;
  }
}

// Welcome form submit
welcomeForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const content = welcomeInput.value.trim();
  if (!content) return;
  showChatState();
  chatForm.classList.remove('hidden');
  welcomeInput.value = '';
  await sendMessage(content);
});

// Chat form submit or stop
chatForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  if (isStreaming) {
    // Stop the stream
    if (streamController) streamController.abort();
    setInputStateStreaming(false);
    return;
  }
  const content = userInput.value.trim();
  if (!content) return;
  userInput.value = '';
  await sendMessage(content);
});


chatForm.querySelector('button[type="submit"]').addEventListener('click', (e) => {
  if (isStreaming) {
    e.preventDefault();
    if (streamController) streamController.abort();
    setInputStateStreaming(false);
  }
});

updateWelcomeState();
