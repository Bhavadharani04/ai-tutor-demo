// frontend/chat.js

let currentSessionId = null;
let learnedTopics    = JSON.parse(localStorage.getItem("ai_tutor_topics") || "[]");
let quizScore        = { correct: 0, total: 0 };
let currentQuiz      = null;
let isStreaming      = false;
let diagramCounter   = 0;
const IMAGE_TAG_PATTERN = /^\[IMAGE:(.+?)\]\s*([\s\S]*)$/;
const IMAGE_SOURCE_PATTERN = /\[IMAGE_SOURCE:([\s\S]*?)\]/;
const IMAGE_SOURCE_LABEL_PATTERN = /\[IMAGE_SOURCE_LABEL:([\s\S]*?)\]/;
const DIAGRAM_TITLE_PATTERN = /\[DIAGRAM_TITLE:([\s\S]*?)\]/;
const DIAGRAM_EXPLANATION_PATTERN = /\[DIAGRAM_EXPLANATION:([\s\S]*?)\]/;
const DIAGRAM_MERMAID_PATTERN = /\[DIAGRAM_MERMAID:([\s\S]*)\]$/;

// ── Wait for DOM to be ready ────────────────────────────
document.addEventListener("DOMContentLoaded", function() {
  loadHistorySidebar();
  renderProgress();
});

// ── DOM refs ────────────────────────────────────────────
function getEl(id) {
  return document.getElementById(id);
}

// ── Markdown renderer ───────────────────────────────────
function renderMarkdown(text) {
  if (!text) return "";
  text = text.replace(/\[TOPIC:.*?\]/g, "").trim();
  text = text.replace(/```([\s\S]*?)```/g, "<pre><code>$1</code></pre>");
  text = text.replace(/`([^`]+)`/g, "<code>$1</code>");
  text = text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  text = text.replace(/\*(.*?)\*/g, "<em>$1</em>");
  text = text.replace(/^### (.+)$/gm, "<h3>$1</h3>");
  text = text.replace(/^## (.+)$/gm,  "<h2>$1</h2>");
  text = text.replace(/^# (.+)$/gm,   "<h1>$1</h1>");
  text = text.replace(/^\d+\.\s(.+)$/gm, "<li>$1</li>");
  text = text.replace(/^[-*]\s(.+)$/gm,  "<li>$1</li>");
  text = text.replace(/\n\n/g, "</p><p>");
  text = text.replace(/\n/g, "<br>");
  return "<p>" + text + "</p>";
}

// ── Add bubble ──────────────────────────────────────────
function addBubble(text, type, withCopy) {
  const chatbox = getEl("chatbox");
  if (!chatbox) return null;

  const wrapper     = document.createElement("div");
  wrapper.className = "bubble-wrapper " + (type === "user" ? "user-wrapper" : "bot-wrapper");

  const div     = document.createElement("div");
  div.className = "bubble " + (type === "user" ? "user-bubble" : "bot-bubble");

  if (type === "user") {
    div.textContent = text;
  } else {
    div.innerHTML = renderMarkdown(text);
  }

  wrapper.appendChild(div);

  if (withCopy && type === "bot") {
    const copyBtn       = document.createElement("button");
    copyBtn.className   = "copy-btn";
    copyBtn.textContent = "Copy";
    copyBtn.onclick     = function() {
      navigator.clipboard.writeText(
        text.replace(/\[TOPIC:.*?\]/g, "").trim()
      );
      copyBtn.textContent = "Copied!";
      setTimeout(function() { copyBtn.textContent = "Copy"; }, 2000);
    };
    wrapper.appendChild(copyBtn);
  }

  chatbox.appendChild(wrapper);
  chatbox.scrollTop = chatbox.scrollHeight;
  return div;
}

function getRequestedTopic() {
  const input = getEl("userInput");
  const topic = input ? input.value.trim() : "";
  if (!topic) {
    alert("Type an AI topic in the input box first.");
    return null;
  }
  return topic;
}

function addCustomBotBubble(html) {
  const chatbox = getEl("chatbox");
  if (!chatbox) return null;

  const wrapper = document.createElement("div");
  wrapper.className = "bubble-wrapper bot-wrapper";

  const bubble = document.createElement("div");
  bubble.className = "bubble bot-bubble";
  bubble.innerHTML = html;
  wrapper.appendChild(bubble);

  chatbox.appendChild(wrapper);
  chatbox.scrollTop = chatbox.scrollHeight;
  return bubble;
}

function parseImageMessage(text) {
  const content = String(text || "");
  const match = content.match(IMAGE_TAG_PATTERN);
  if (!match) return null;

  const sourceMatch = content.match(IMAGE_SOURCE_PATTERN);
  const sourceLabelMatch = content.match(IMAGE_SOURCE_LABEL_PATTERN);
  const caption = content
    .replace(IMAGE_TAG_PATTERN, "$2")
    .replace(IMAGE_SOURCE_PATTERN, "")
    .replace(IMAGE_SOURCE_LABEL_PATTERN, "")
    .trim();

  return {
    imageUrl: match[1].trim(),
    caption: caption,
    sourceUrl: sourceMatch ? sourceMatch[1].trim() : "",
    sourceLabel: sourceLabelMatch ? sourceLabelMatch[1].trim() : ""
  };
}

function addImageBubble(imageUrl, caption, sourceUrl, sourceLabel) {
  const safeUrl = escapeHtml(imageUrl);
  const safeCaption = escapeHtml(caption || "AI-generated image");
  const safeSourceUrl = escapeHtml(sourceUrl || "");
  const safeSourceLabel = escapeHtml(sourceLabel || "Image source");
  const downloadName = "ai-tutor-image-" + Date.now() + ".png";
  const sourceLink = safeSourceUrl
    ? '<a class="generated-image-link" href="' + safeSourceUrl + '" target="_blank" rel="noopener noreferrer">' + safeSourceLabel + '</a>'
    : "";
  return addCustomBotBubble(
    '<div class="generated-image-card">' +
      '<img class="generated-image" src="' + safeUrl + '" alt="' + safeCaption + '">' +
      '<div class="generated-image-caption">' + safeCaption + '</div>' +
      '<div class="generated-image-actions">' +
        '<a class="generated-image-link" href="' + safeUrl + '" target="_blank" rel="noopener noreferrer">Open full image</a>' +
        '<a class="generated-image-link generated-image-download" href="' + safeUrl + '" download="' + downloadName + '">Download image</a>' +
        sourceLink +
      '</div>' +
    '</div>'
  );
}

function addSetupBubble(title, lines) {
  const body = [title].concat(lines || []).join("\n\n");
  addBubble(body, "bot", false);
}

function parseDiagramMessage(text) {
  const content = String(text || "");
  const titleMatch = content.match(DIAGRAM_TITLE_PATTERN);
  const explanationMatch = content.match(DIAGRAM_EXPLANATION_PATTERN);
  const mermaidMatch = content.match(DIAGRAM_MERMAID_PATTERN);

  if (!mermaidMatch) return null;

  return {
    title: titleMatch ? titleMatch[1].trim() : "Architecture Diagram",
    explanation: explanationMatch ? explanationMatch[1].trim() : "",
    mermaid: mermaidMatch[1].trim()
  };
}

function escapeHtml(text) {
  return String(text || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

async function fetchImageStatus() {
  try {
    const res = await fetch("/image-status");
    if (!res.ok) return null;
    return await res.json();
  } catch (error) {
    console.error("image status error:", error);
    return null;
  }
}

async function showImageGenerationHelp(errorMessage) {
  const status = await fetchImageStatus();
  const lines = [];

  if (status && status.message) {
    lines.push(status.message);
  }

  if (status && status.model) {
    lines.push("Model: `" + status.model + "`");
  }

  lines.push("Image generation is shown directly inside this same tutor chat screen.");
  lines.push("If Flux fails, check your internet connection and Hugging Face token in `.env`.");

  if (errorMessage) {
    lines.push("Latest error: " + errorMessage);
  }

  addSetupBubble("Flux image setup help", lines);
}

async function renderMermaidDiagram(container, mermaidText) {
  if (!container || !window.mermaid) return;
  const renderId = "mermaid-render-" + (diagramCounter + 1);

  try {
    const result = await window.mermaid.render(renderId, mermaidText);
    container.innerHTML = result.svg;
  } catch (error) {
    console.error("Mermaid render failed:", error);
    container.textContent = mermaidText;
  }
}

async function renderBotResponse(data) {
  const responseType = data.response_type || "text";

  if (responseType === "image" && data.image_url) {
    addImageBubble(
      data.image_url,
      data.reply || "AI-generated image",
      data.source_url || "",
      data.source_label || ""
    );
    return;
  }

  if (responseType === "diagram" && data.mermaid) {
    diagramCounter += 1;
    const targetId = "diagram-target-" + diagramCounter;
    const title = escapeHtml(data.title || "Architecture Diagram");
    const explanation = data.explanation || data.reply || "";
    const bubble = addCustomBotBubble(
      "<strong>" + title + "</strong><br><br>" +
      renderMarkdown(explanation) +
      '<div class="diagram-shell"><div id="' + targetId + '">Rendering diagram...</div></div>'
    );

    if (bubble) {
      const target = bubble.querySelector("#" + targetId);
      await renderMermaidDiagram(target, data.mermaid);
    }
    return;
  }

  const parsedImage = parseImageMessage(data.reply || "");
  if (parsedImage) {
    addImageBubble(parsedImage.imageUrl, parsedImage.caption, parsedImage.sourceUrl, parsedImage.sourceLabel);
    return;
  }

  const parsedDiagram = parseDiagramMessage(data.reply || "");
  if (parsedDiagram) {
    diagramCounter += 1;
    const targetId = "diagram-target-" + diagramCounter;
    const bubble = addCustomBotBubble(
      "<strong>" + escapeHtml(parsedDiagram.title) + "</strong><br><br>" +
      renderMarkdown(parsedDiagram.explanation) +
      '<div class="diagram-shell"><div id="' + targetId + '">Rendering diagram...</div></div>'
    );

    if (bubble) {
      const target = bubble.querySelector("#" + targetId);
      await renderMermaidDiagram(target, parsedDiagram.mermaid);
    }
    return;
  }

  addBubble(data.reply || "", "bot", true);
}

// ── Typing indicator ────────────────────────────────────
function showTypingIndicator() {
  const chatbox = getEl("chatbox");
  if (!chatbox) return;
  const wrapper     = document.createElement("div");
  wrapper.className = "bubble-wrapper bot-wrapper";
  wrapper.id        = "typing-indicator";
  wrapper.innerHTML = `
    <div class="bubble bot-bubble typing-bubble">
      <span class="dot"></span>
      <span class="dot"></span>
      <span class="dot"></span>
    </div>`;
  chatbox.appendChild(wrapper);
  chatbox.scrollTop = chatbox.scrollHeight;
}

function hideTypingIndicator() {
  const el = getEl("typing-indicator");
  if (el) el.remove();
}

// ── File handling ───────────────────────────────────────
function onFileSelected() {
  const fileInput    = getEl("fileInput");
  const fileNameSpan = getEl("file-name");
  const clearFileBtn = getEl("clear-file");
  if (fileInput && fileInput.files[0]) {
    fileNameSpan.textContent   = fileInput.files[0].name;
    clearFileBtn.style.display = "inline";
  }
}

function clearFile() {
  const fileInput    = getEl("fileInput");
  const fileNameSpan = getEl("file-name");
  const clearFileBtn = getEl("clear-file");
  if (fileInput)    fileInput.value            = "";
  if (fileNameSpan) fileNameSpan.textContent   = "No file selected";
  if (clearFileBtn) clearFileBtn.style.display = "none";
}

// ── Progress tracking ───────────────────────────────────
function extractTopic(text) {
  if (!text) return null;
  const match = text.match(/\[TOPIC:\s*(.+?)\]/i);
  return match ? match[1].trim() : null;
}

function addTopicToProgress(topic) {
  if (!topic) return;
  if (!learnedTopics.find(function(t) {
    return t.toLowerCase() === topic.toLowerCase();
  })) {
    learnedTopics.push(topic);
    localStorage.setItem("ai_tutor_topics", JSON.stringify(learnedTopics));
    renderProgress();
  }
}

function renderProgress() {
  const list  = getEl("progress-list");
  const empty = getEl("progress-empty");
  const count = getEl("progress-count");
  if (!list) return;

  list.querySelectorAll(".progress-item").forEach(function(i) { i.remove(); });

  if (learnedTopics.length === 0) {
    if (empty) empty.style.display = "block";
    if (count) count.textContent   = "0 topics learned";
    return;
  }

  if (empty) empty.style.display = "none";
  if (count) count.textContent   = learnedTopics.length + " topic(s) learned!";

  learnedTopics.forEach(function(topic) {
    const item     = document.createElement("div");
    item.className = "progress-item";
    item.innerHTML = '<div class="progress-dot"></div>' + topic;
    list.appendChild(item);
  });
}

// ── SEND MESSAGE ────────────────────────────────────────
async function sendMessage() {
  const input    = getEl("userInput");
  const fileInput = getEl("fileInput");
  const sendBtn  = getEl("sendBtn");
  const chatTitleBar = getEl("chat-title-text");

  if (!input) {
    console.error("userInput element not found!");
    return;
  }

  const msg  = input.value.trim();
  const file = fileInput ? fileInput.files[0] : null;

  if ((!msg && !file) || isStreaming) return;

  let userDisplay = msg || "Sent a file";
  if (file) userDisplay += " [File: " + file.name + "]";

  addBubble(userDisplay, "user", false);
  input.value = "";
  if (sendBtn)  sendBtn.disabled = true;
  isStreaming = true;

  // Update status
  if (typeof setStatus === "function") setStatus("thinking");

  showTypingIndicator();

  const formData = new FormData();
  if (msg)              formData.append("message",      msg);
  if (file)             formData.append("file",          file);
  if (currentSessionId) formData.append("session_id",   currentSessionId);

  const studentName = localStorage.getItem("ai_tutor_user") || "Student";
  formData.append("student_name", studentName);

  try {
    const res = await fetch("/chat", {
      method: "POST",
      body:   formData
    });

    if (!res.ok) {
      throw new Error("Server returned error: " + res.status);
    }

    const data = await res.json();

    hideTypingIndicator();

    await renderBotResponse(data);

    // Save session
    if (data.session_id) currentSessionId = data.session_id;

    // Track topic
    const topic = extractTopic(data.reply);
    if (topic) addTopicToProgress(topic);

    // Update title
    if (msg && chatTitleBar) chatTitleBar.textContent = msg.slice(0, 60);

    // Speak the reply
    if (typeof speakText === "function") speakText(data.reply);

    loadHistorySidebar();
    clearFile();

  } catch(err) {
    hideTypingIndicator();
    console.error("sendMessage error:", err);
    addBubble(
      "Error: " + err.message + ". Make sure run.py is running in terminal.",
      "bot", false
    );
    if (typeof setStatus === "function") setStatus("error");
    if (typeof stopTalking === "function") stopTalking();
  }

  if (sendBtn) sendBtn.disabled = false;
  isStreaming = false;
}

async function generateImageFromInput() {
  const input = getEl("userInput");
  const imageBtn = getEl("imageBtn");
  const sendBtn = getEl("sendBtn");
  const chatTitleBar = getEl("chat-title-text");

  if (!input) {
    console.error("userInput element not found!");
    return;
  }

  const prompt = input.value.trim();
  if (!prompt || isStreaming) {
    if (!prompt) alert("Type an image prompt first.");
    return;
  }

  addBubble(prompt, "user", false);
  input.value = "";
  isStreaming = true;
  if (imageBtn) imageBtn.disabled = true;
  if (sendBtn) sendBtn.disabled = true;

  if (typeof setStatus === "function") setStatus("thinking");
  showTypingIndicator();

  try {
    const res = await fetch("/generate-image", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt,
        session_id: currentSessionId
      })
    });

    const data = await res.json();
    hideTypingIndicator();

    if (!res.ok) {
      throw new Error(data.error || data.reply || ("Server returned error: " + res.status));
    }

    await renderBotResponse(data);

    if (data.session_id) currentSessionId = data.session_id;
    if (chatTitleBar) chatTitleBar.textContent = prompt.slice(0, 60);

    if (typeof speakText === "function" && data.reply) speakText(data.reply);

    loadHistorySidebar();
    clearFile();
  } catch (err) {
    hideTypingIndicator();
    console.error("generateImageFromInput error:", err);
    const lowerMessage = String(err.message || "").toLowerCase();
    if (lowerMessage.includes("flux") || lowerMessage.includes("hf_token") || lowerMessage.includes("hugging face")) {
      await showImageGenerationHelp(err.message);
    } else {
      addBubble("Error: " + err.message, "bot", false);
    }
    if (typeof setStatus === "function") setStatus("error");
    if (typeof stopTalking === "function") stopTalking();
  }

  if (imageBtn) imageBtn.disabled = false;
  if (sendBtn) sendBtn.disabled = false;
  isStreaming = false;
}

// ── History sidebar ─────────────────────────────────────
async function loadHistorySidebar() {
  try {
    const historyList = getEl("history-list");
    const empty       = getEl("history-empty");
    if (!historyList) return;

    const res      = await fetch("/sessions");
    if (!res.ok) return;
    const sessions = await res.json();

    historyList.querySelectorAll(".history-item").forEach(function(i) { i.remove(); });

    if (sessions.length === 0) {
      if (empty) empty.style.display = "block";
      return;
    }
    if (empty) empty.style.display = "none";

    sessions.forEach(function(session) {
      const item     = document.createElement("div");
      item.className = "history-item" +
        (session.id === currentSessionId ? " active" : "");
      item.innerHTML =
        '<div class="history-title">' + session.title + '</div>' +
        '<div class="history-time">'  + session.created_at + '</div>';
      item.onclick = function() { loadSession(session.id); };
      historyList.appendChild(item);
    });
  } catch(e) {
    console.error("History sidebar error:", e);
  }
}

// ── Load old session ────────────────────────────────────
async function loadSession(id) {
  const chatbox        = getEl("chatbox");
  const chatTitleBar   = getEl("chat-title-text");
  currentSessionId     = id;
  if (chatbox)      chatbox.innerHTML        = "";
  if (chatTitleBar) chatTitleBar.textContent = "Loading...";

  try {
    const res      = await fetch("/sessions/" + id + "/messages");
    const messages = await res.json();
    messages.forEach(function(msg) {
      const parsedImage = msg.role === "assistant" ? parseImageMessage(msg.content) : null;
      const parsedDiagram = msg.role === "assistant" ? parseDiagramMessage(msg.content) : null;
      if (parsedImage) {
        addImageBubble(parsedImage.imageUrl, parsedImage.caption, parsedImage.sourceUrl, parsedImage.sourceLabel);
      } else if (parsedDiagram) {
        diagramCounter += 1;
        const targetId = "diagram-target-" + diagramCounter;
        const bubble = addCustomBotBubble(
          "<strong>" + escapeHtml(parsedDiagram.title) + "</strong><br><br>" +
          renderMarkdown(parsedDiagram.explanation) +
          '<div class="diagram-shell"><div id="' + targetId + '">Rendering diagram...</div></div>'
        );
        if (bubble) {
          const target = bubble.querySelector("#" + targetId);
          renderMermaidDiagram(target, parsedDiagram.mermaid);
        }
      } else {
        addBubble(
          msg.content,
          msg.role === "user" ? "user" : "bot",
          msg.role === "assistant"
        );
      }
    });
    const res2     = await fetch("/sessions");
    const sessions = await res2.json();
    const session  = sessions.find(function(s) { return s.id === id; });
    if (session && chatTitleBar) chatTitleBar.textContent = session.title;
  } catch(e) {
    console.error("Load session error:", e);
  }
  loadHistorySidebar();
}

// ── New chat ────────────────────────────────────────────
async function startNewChat() {
  try {
    const res        = await fetch("/sessions/new", { method: "POST" });
    const data       = await res.json();
    currentSessionId = data.session_id;
  } catch(e) {
    currentSessionId = null;
  }

  const chatbox      = getEl("chatbox");
  const chatTitleBar = getEl("chat-title-text");
  const name         = localStorage.getItem("ai_tutor_user") || "there";

  if (chatbox) {
    chatbox.innerHTML =
      '<div class="bubble-wrapper bot-wrapper">' +
        '<div class="bubble bot-bubble">' +
          "Hello " + name + "! Starting a fresh conversation. What AI topic would you like to explore?" +
        "</div>" +
      "</div>";
  }
  if (chatTitleBar) chatTitleBar.textContent = "New Conversation";
  loadHistorySidebar();
}

// ── Clear all history ───────────────────────────────────
async function clearAllHistory() {
  if (!confirm("Clear all chat history? This cannot be undone.")) return;
  try {
    await fetch("/sessions/all", { method: "DELETE" });
  } catch(e) {}
  startNewChat();
}

// ── Download chat ───────────────────────────────────────
function downloadChatPDF() {
  const chatbox = getEl("chatbox");
  if (!chatbox) return;
  const bubbles = chatbox.querySelectorAll(".bubble");
  if (bubbles.length === 0) { alert("No chat to download!"); return; }

  let content  = "AI VIRTUAL TUTOR — CHAT EXPORT\n";
  content     += "================================\n\n";
  content     += "Student : " + (localStorage.getItem("ai_tutor_user") || "Student") + "\n";
  content     += "Date    : " + new Date().toLocaleString() + "\n\n";
  content     += "================================\n\n";

  bubbles.forEach(function(b) {
    const who  = b.classList.contains("user-bubble") ? "You" : "Ms. Aira";
    content   += who + ":\n" + b.innerText + "\n\n";
  });

  if (learnedTopics.length > 0) {
    content += "================================\n";
    content += "TOPICS LEARNED:\n";
    learnedTopics.forEach(function(t, i) {
      content += (i + 1) + ". " + t + "\n";
    });
  }

  const blob = new Blob([content], { type: "text/plain" });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement("a");
  a.href     = url;
  a.download = "AI_Tutor_Chat_" +
    new Date().toLocaleDateString().replace(/\//g, "-") + ".txt";
  a.click();
  URL.revokeObjectURL(url);
}

// ── Quiz ────────────────────────────────────────────────
async function startQuiz() {
  if (learnedTopics.length === 0) {
    alert("Learn at least one topic first before taking a quiz!");
    return;
  }

  const topic     = learnedTopics[Math.floor(Math.random() * learnedTopics.length)];
  const quizPanel = getEl("quiz-panel");
  if (quizPanel) quizPanel.classList.add("active");

  const qEl = getEl("quiz-question");
  const oEl = getEl("quiz-options");
  const fEl = getEl("quiz-feedback");
  if (qEl) qEl.textContent = "Loading question...";
  if (oEl) oEl.innerHTML   = "";
  if (fEl) { fEl.textContent = ""; fEl.className = "quiz-feedback"; }

  try {
    const formData    = new FormData();
    const studentName = localStorage.getItem("ai_tutor_user") || "Student";
    formData.append("message",
      'Generate a multiple choice quiz question about "' + topic + '".' +
      ' Create 4 options labeled A, B, C, and D.' +
      ' Randomly choose which option is correct, and do not always use A as the answer.' +
      ' Reply in this EXACT format only:\n' +
      'QUESTION: your question here\n' +
      'A) option one\n' +
      'B) option two\n' +
      'C) option three\n' +
      'D) option four\n' +
      'ANSWER: <A or B or C or D>'
    );
    formData.append("student_name", studentName);
    if (currentSessionId) formData.append("session_id", currentSessionId);

    const res  = await fetch("/chat", { method: "POST", body: formData });
    const data = await res.json();
    parseAndShowQuiz(data.reply, topic);

  } catch(e) {
    closeQuiz();
    alert("Could not load quiz. Try again!");
  }
}

function parseAndShowQuiz(text, topic) {
  const lines   = text.split("\n").map(function(l) { return l.trim(); }).filter(function(l) { return l; });
  const qLine   = lines.find(function(l) { return l.startsWith("QUESTION:"); });
  const aLine   = lines.find(function(l) { return /^A[).]/.test(l); });
  const bLine   = lines.find(function(l) { return /^B[).]/.test(l); });
  const cLine   = lines.find(function(l) { return /^C[).]/.test(l); });
  const dLine   = lines.find(function(l) { return /^D[).]/.test(l); });
  const ansLine = lines.find(function(l) { return l.startsWith("ANSWER:"); });

  if (!qLine || !aLine || !ansLine) {
    closeQuiz();
    alert("Quiz generation failed. Try again!");
    return;
  }

  const originalAnswer = ansLine.replace("ANSWER:", "").trim().charAt(0).toUpperCase();
  const optionLines = [aLine, bLine, cLine, dLine].filter(Boolean);
  const optionItems = optionLines.map(function(opt) {
    return {
      originalLetter: opt.charAt(0).toUpperCase(),
      text: opt.replace(/^[A-D][).]\s*/, "").trim()
    };
  });

  for (let i = optionItems.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    const temp = optionItems[i];
    optionItems[i] = optionItems[j];
    optionItems[j] = temp;
  }

  const displayLetters = ["A", "B", "C", "D"];
  const displayedOptions = optionItems.map(function(item, index) {
    return {
      letter: displayLetters[index],
      text: item.text,
      isCorrect: item.originalLetter === originalAnswer
    };
  });

  const correctDisplayedOption = displayedOptions.find(function(item) {
    return item.isCorrect;
  });

  currentQuiz = {
    answer: correctDisplayedOption ? correctDisplayedOption.letter : originalAnswer
  };

  const h2 = getEl("quiz-box") ? getEl("quiz-box").querySelector("h2") : null;
  if (h2)            h2.textContent = "Quiz — " + topic;

  const qEl = getEl("quiz-question");
  const sEl = getEl("quiz-score");
  const oEl = getEl("quiz-options");

  if (qEl) qEl.textContent = qLine.replace("QUESTION:", "").trim();
  if (sEl) sEl.textContent = "Score: " + quizScore.correct + "/" + quizScore.total;

  if (oEl) {
    oEl.innerHTML = "";
    displayedOptions.forEach(function(opt) {
      const btn       = document.createElement("button");
      btn.className   = "quiz-option";
      btn.textContent = opt.letter + ") " + opt.text;
      btn.onclick     = function() { checkAnswer(btn, opt.letter); };
      oEl.appendChild(btn);
    });
  }
}

function checkAnswer(btn, selected) {
  const feedback = getEl("quiz-feedback");
  const sEl      = getEl("quiz-score");

  document.querySelectorAll(".quiz-option").forEach(function(b) { b.onclick = null; });
  quizScore.total++;

  if (selected === currentQuiz.answer) {
    btn.classList.add("correct");
    if (feedback) {
      feedback.textContent = "Correct! Well done!";
      feedback.className   = "quiz-feedback correct";
    }
    quizScore.correct++;
    if (typeof speakText === "function") speakText("Correct! Well done!");
  } else {
    btn.classList.add("wrong");
    if (feedback) {
      feedback.textContent = "Incorrect. Correct answer is " + currentQuiz.answer;
      feedback.className   = "quiz-feedback wrong";
    }
    if (typeof speakText === "function") {
      speakText("Not quite! The correct answer is " + currentQuiz.answer + ". Keep trying!");
    }
    document.querySelectorAll(".quiz-option").forEach(function(b) {
      if (b.textContent.startsWith(currentQuiz.answer)) b.classList.add("correct");
    });
  }

  if (sEl) sEl.textContent = "Score: " + quizScore.correct + "/" + quizScore.total;
}

function closeQuiz() {
  const quizPanel = getEl("quiz-panel");
  if (quizPanel) quizPanel.classList.remove("active");
  currentQuiz = null;
}

function logout() {
  localStorage.removeItem("ai_tutor_user");
  location.reload();
}
