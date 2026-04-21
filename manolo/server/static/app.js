/* global fetch, document */

async function apiJson(path, options) {
  const res = await fetch(path, options);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json();
}

function el(tag, cls, text) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text !== undefined) n.textContent = text;
  return n;
}

function appendLine(role, text) {
  const log = document.getElementById("log");
  log.appendChild(el("div", `msg ${role}`, text));
  log.scrollTop = log.scrollHeight;
}

async function ensureConversation() {
  let cid = window.sessionStorage.getItem("conversation_id");
  if (cid) return cid;
  const conv = await apiJson("/v1/conversations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title: "Chat" }),
  });
  cid = conv.id;
  window.sessionStorage.setItem("conversation_id", cid);
  return cid;
}

async function streamChat(message) {
  const cid = await ensureConversation();
  const res = await fetch("/v1/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify({ conversation_id: cid, message }),
  });
  if (!res.ok || !res.body) {
    const t = await res.text();
    throw new Error(t || "chat failed");
  }
  const reader = res.body.getReader();
  const dec = new TextDecoder();
  let buf = "";
  let assistant = "";
  // eslint-disable-next-line no-constant-condition
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    let idx;
    while ((idx = buf.indexOf("\n\n")) >= 0) {
      const chunk = buf.slice(0, idx);
      buf = buf.slice(idx + 2);
      const lines = chunk.split("\n");
      for (const line of lines) {
        if (!line.startsWith("data:")) continue;
        const payload = line.slice(5).trim();
        let ev;
        try {
          ev = JSON.parse(payload);
        } catch {
          continue;
        }
        if (ev.event === "token" && ev.text) {
          assistant += ev.text;
          const log = document.getElementById("log");
          let node = log.querySelector(".msg.assistant.streaming");
          if (!node) {
            node = el("div", "msg assistant streaming", "");
            log.appendChild(node);
          }
          node.textContent = assistant;
          log.scrollTop = log.scrollHeight;
        } else if (ev.event === "tool_call") {
          appendLine("tool", `Tool: ${ev.name}`);
        } else if (ev.event === "tool_result") {
          appendLine("tool", `Result (${ev.name}): ${JSON.stringify(ev.result)}`);
        } else if (ev.event === "error") {
          appendLine("tool", `Error: ${ev.message}`);
        } else if (ev.event === "done") {
          const log = document.getElementById("log");
          const node = log.querySelector(".msg.assistant.streaming");
          if (node) {
            node.classList.remove("streaming");
          }
        }
      }
    }
  }
}

async function main() {
  const form = document.getElementById("form");
  const input = document.getElementById("input");
  const status = document.getElementById("status");
  const newChat = document.getElementById("newChat");

  newChat.addEventListener("click", () => {
    window.sessionStorage.removeItem("conversation_id");
    document.getElementById("log").innerHTML = "";
    status.textContent = "New conversation";
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    input.value = "";
    status.textContent = "Thinking…";
    appendLine("user", text);
    const btn = form.querySelector("button[type='submit']");
    btn.disabled = true;
    try {
      await streamChat(text);
      status.textContent = "Ready";
    } catch (err) {
      status.textContent = "Error";
      appendLine("tool", String(err));
    } finally {
      btn.disabled = false;
    }
  });
}

main();
