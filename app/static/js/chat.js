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

function addCopyButtonsToCodeBlocks(container) {
  container.querySelectorAll('pre > code').forEach((codeBlock) => {
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
      setTimeout(() => { btn.innerText = 'Copy'; }, 600);
    };
    pre.appendChild(btn);
  });
}

function renderMarkdownWithMath(text) {
  marked.setOptions({
    gfm: true,
    breaks: true,
    smartLists: true,
    smartypants: true,
    highlight: function(code, lang) {
      return code;
    }
  });
  let html = marked.parse(text || "");
  const tempDiv = document.createElement('div');
  tempDiv.innerHTML = html;

  setTimeout(() => {
    if (window.hljs) window.hljs.highlightAll();
  }, 0);
  return tempDiv.innerHTML;
}

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
    // Add copy buttons to code blocks in this bubble
    addCopyButtonsToCodeBlocks(bubble);
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
  if (messages.length === 0 && window.botMarkdownInstructions) {
    content = window.botMarkdownInstructions + "\n\n" + content;
  }
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

  let assistantContent = '';
  let abortController = new AbortController();
  streamController = abortController;

  // Helper for typing animation
  async function typeText(target, fullText, prevText = "") {
    // Only type the new part
    let start = prevText.length;
    for (let i = start; i < fullText.length; i++) {
      if (!isStreaming) break;
      target.innerHTML = renderMarkdownWithMath(fullText.slice(0, i + 1));
      addCopyButtonsToCodeBlocks(target);
      chatWindow.scrollTop = chatWindow.scrollHeight;
      if (window.MathJax) MathJax.typesetPromise([target]);
      await new Promise(r => setTimeout(r, 0)); // Typing speed (ms per char)
    }
  }

  try {
    const model = selectedModelInput ? selectedModelInput.value : 'llama-3.3-70b-versatile';
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages, model: model, max_tokens: 8192, stream: true }),
      signal: abortController.signal
    });

    if (!res.ok) {
      bubble.innerHTML = '<span class="text-red-500">Error: Could not get response.</span>';
      setInputStateStreaming(false);
      return;
    }

    if (!res.body || !res.body.getReader) {
      // Not a stream, fallback to JSON
      const data = await res.json();
      assistantContent = data.response || '';
      await typeText(bubble, assistantContent);
      if (assistantContent.trim() !== "") {
        messages.push({ role: 'assistant', content: assistantContent });
      } else {
        bubble.innerHTML = '<span class="text-red-500">No response from assistant.</span>';
      }
      setInputStateStreaming(false);
      streamController = null;
      return;
    }

    // Stream response with typing animation
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    assistantContent = '';
    bubble.innerHTML = '';
    let done = false;
    let prevContent = '';
    while (!done) {
      const { value, done: streamDone } = await reader.read();
      if (value) {
        const chunk = decoder.decode(value, { stream: true });
        assistantContent += chunk;
        // Animate only the new part
        await typeText(bubble, assistantContent, prevContent);
        prevContent = assistantContent;
      }
      done = streamDone;
      if (!isStreaming) break;
    }
    if (assistantContent.trim() !== "") {
      messages.push({ role: 'assistant', content: assistantContent });
    } else {
      bubble.innerHTML = '<span class="text-red-500">No response from assistant.</span>';
    }
  } catch (err) {
    if (abortController.signal.aborted) {
      bubble.innerHTML = '<span class="italic text-gray-400">Response stopped.</span>';
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
