const form = document.querySelector("#chatForm");
const input = document.querySelector("#messageInput");
const messages = document.querySelector("#messages");
const newChat = document.querySelector("#newChat");

const welcomeText =
  "Halo. Saya siap bantu kamu membuat ide, menjawab pertanyaan Python, atau membahas project.";

function scrollToBottom() {
  messages.scrollTop = messages.scrollHeight;
}

function appendMessage(text, type) {
  const article = document.createElement("article");
  article.className = `message ${type === "user" ? "user-message" : "bot-message"}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;

  article.appendChild(bubble);
  messages.appendChild(article);
  scrollToBottom();
}

function appendTyping() {
  const article = document.createElement("article");
  article.className = "message bot-message typing-row";
  article.innerHTML = `
    <div class="bubble typing" aria-label="Bot sedang mengetik">
      <span></span><span></span><span></span>
    </div>
  `;
  messages.appendChild(article);
  scrollToBottom();
  return article;
}

function resizeInput() {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 140)}px`;
}

async function sendMessage(message) {
  appendMessage(message, "user");
  const typing = appendTyping();

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });

    const data = await response.json();
    typing.remove();
    appendMessage(data.reply || "Maaf, saya belum bisa menjawab itu.", "bot");
  } catch (error) {
    typing.remove();
    appendMessage("Koneksi ke server belum tersedia. Pastikan Flask sedang berjalan.", "bot");
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const message = input.value.trim();

  if (!message) {
    input.focus();
    return;
  }

  input.value = "";
  resizeInput();
  sendMessage(message);
});

input.addEventListener("input", resizeInput);

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

newChat.addEventListener("click", () => {
  messages.innerHTML = "";
  appendMessage(welcomeText, "bot");
  input.value = "";
  resizeInput();
  input.focus();
});

resizeInput();
