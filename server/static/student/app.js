/* Página do aluno: entrar com código, escolher identidade, trabalhar na
   atividade (iframe + PageCraftBridge) e receber feedback em tempo real. */

const state = {
  session: null,
  studentId: null,
  token: null,
  displayName: null,
  outbox: [],
  pitItems: {},
};

const $ = (id) => document.getElementById(id);

/* ---- passo 1: código ---- */

$("code-form").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const code = $("code-input").value.trim().toUpperCase();
  const status = $("code-status");
  status.textContent = "A procurar a aula…";
  try {
    const resp = await fetch(`/api/join/${encodeURIComponent(code)}`);
    if (!resp.ok) throw new Error((await resp.json()).detail || "código não encontrado");
    state.session = await resp.json();
    status.textContent = "";
    showIdentityStep();
  } catch (err) {
    status.textContent = err.message;
  }
});

/* ---- passo 2: identidade ---- */

function showIdentityStep() {
  $("step-code").hidden = true;
  $("step-identity").hidden = false;
  $("session-title").textContent = `${state.session.class_name} · ${state.session.activity_title}`;
  const grid = $("identities");
  grid.innerHTML = "";
  state.session.roster.forEach((s) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = s.display_name;
    btn.disabled = s.taken;
    btn.addEventListener("click", () => claim(s));
    grid.appendChild(btn);
  });
}

async function claim(student) {
  const status = $("claim-status");
  status.textContent = `A entrar como ${student.display_name}…`;
  const resp = await fetch(`/api/sessions/${state.session.id}/claim`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ student_id: student.student_id }),
  });
  if (!resp.ok) {
    status.textContent = (await resp.json()).detail || "não foi possível";
    return;
  }
  const data = await resp.json();
  state.studentId = data.student_id;
  state.token = data.student_token;
  state.displayName = data.display_name;
  startActivity();
}

/* ---- passo 3: atividade ---- */

function startActivity() {
  $("step-identity").hidden = true;
  $("step-activity").hidden = false;
  $("student-name").textContent = state.displayName;
  $("activity-title").textContent = state.session.activity_title;
  $("activity-frame").src = `/activities/${state.session.activity_slug}/`;
  listenToBridge();
  connectStream();
  setInterval(flushOutbox, 2000);
  // nota: o evento "joined" é emitido pelo servidor no claim; não repetir aqui
}

/* eventos da atividade (PageCraftBridge → postMessage) */
function listenToBridge() {
  const frame = $("activity-frame");
  window.addEventListener("message", (ev) => {
    // aceitar apenas mensagens vindas do iframe da atividade
    if (!frame.contentWindow || ev.source !== frame.contentWindow) return;
    const d = ev.data;
    if (!d || d.pagecraft !== 1 || !d.type) return;
    queueEvent(d.type, d.unitId || null, sanitizePayload(d.payload));
  });
}

function sanitizePayload(payload) {
  // payloads vêm de código gerado: só primitivos curtos, sem objetos fundos
  const out = {};
  if (payload && typeof payload === "object") {
    for (const [k, v] of Object.entries(payload).slice(0, 8)) {
      if (typeof v === "string") out[k] = v.slice(0, 500);
      else if (typeof v === "number" || typeof v === "boolean") out[k] = v;
    }
  }
  return out;
}

function queueEvent(type, unitId, payload) {
  state.outbox.push({
    event_id: crypto.randomUUID(),
    type,
    unit_id: unitId,
    payload,
    ts: new Date().toISOString(),
  });
}

async function flushOutbox() {
  if (!state.outbox.length || !state.token) return;
  const batch = state.outbox.slice(0, 20);
  try {
    const resp = await fetch(`/api/sessions/${state.session.id}/events`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ student_token: state.token, events: batch }),
    });
    if (resp.ok) {
      const ids = new Set(batch.map((e) => e.event_id));
      state.outbox = state.outbox.filter((e) => !ids.has(e.event_id));
    }
  } catch (err) {
    /* fica na outbox; tentamos outra vez no próximo flush (at-least-once) */
  }
}

/* SSE: feedback IA, mensagens do professor, PIT */
function connectStream() {
  const es = new EventSource(
    `/api/sessions/${state.session.id}/stream?role=student&student_token=${state.token}`
  );
  es.addEventListener("ai_feedback", (ev) => {
    const data = JSON.parse(ev.data);
    showMessage(data.payload.text, "feedback-warn");
    // reencaminha para a atividade (caixa .ai-feedback)
    $("activity-frame").contentWindow?.postMessage(
      { pagecraft: 1, type: "ai_feedback", payload: { text: data.payload.text } },
      "*"
    );
  });
  es.addEventListener("teacher_message", (ev) => {
    const data = JSON.parse(ev.data);
    showMessage(`Professor: ${data.payload.text}`, "feedback-ok");
  });
  es.addEventListener("pit_updated", (ev) => {
    const data = JSON.parse(ev.data);
    if (data.student_id === state.studentId) {
      state.pitItems[data.payload.id] = data.payload;
      renderPit();
    }
  });
  es.addEventListener("session_closed", () => {
    showMessage("A aula terminou. Bom trabalho!", "feedback-ok");
    es.close();
  });
}

function showMessage(text, cls) {
  const box = document.createElement("div");
  box.className = cls;
  box.textContent = text;
  $("messages").appendChild(box);
  setTimeout(() => box.remove(), 15000);
}

/* ---- ajuda + PIT ---- */

$("help-btn").addEventListener("click", () => {
  queueEvent("help_needed", null, { note: "botão de ajuda" });
  showMessage("O professor já sabe que precisas de ajuda.", "feedback-ok");
});

$("pit-btn").addEventListener("click", () => {
  $("pit-panel").hidden = !$("pit-panel").hidden;
});

$("pit-form").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const text = $("pit-text").value.trim();
  if (!text) return;
  const resp = await fetch(`/api/sessions/${state.session.id}/pit`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ student_token: state.token, text, status: "planned" }),
  });
  if (resp.ok) {
    const item = await resp.json();
    state.pitItems[item.id] = item;
    $("pit-text").value = "";
    renderPit();
  }
});

const PIT_LABELS = { planned: "por fazer", doing: "a fazer", done: "feito", to_share: "para partilhar" };
const PIT_NEXT = { planned: "doing", doing: "done", done: "to_share", to_share: "planned" };

function renderPit() {
  const list = $("pit-list");
  list.innerHTML = "";
  Object.values(state.pitItems).forEach((item) => {
    const li = document.createElement("li");
    const btn = document.createElement("button");
    btn.className = "ghost";
    btn.style.minHeight = "48px";
    btn.textContent = PIT_LABELS[item.status] || item.status;
    btn.addEventListener("click", async () => {
      const resp = await fetch(`/api/sessions/${state.session.id}/pit`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          student_token: state.token,
          text: item.text,
          status: PIT_NEXT[item.status] || "planned",
          item_id: item.id,
        }),
      });
      if (resp.ok) {
        const updated = await resp.json();
        state.pitItems[updated.id] = updated;
        renderPit();
      }
    });
    li.append(btn, document.createTextNode(" " + item.text));
    list.appendChild(li);
  });
}
