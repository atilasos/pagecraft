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
const SAVED_KEY = "pagecraft_student";
let bridgeHandler = null;
let stream = null;
let streamRequest = 0;
let flushTimer = null;

function saveIdentity() {
  try {
    localStorage.setItem(
      SAVED_KEY,
      JSON.stringify({
        sessionId: state.session.id,
        token: state.token,
        studentId: state.studentId,
        displayName: state.displayName,
      })
    );
  } catch (e) { /* modo privado sem storage: segue sem persistência */ }
}

function clearIdentity() {
  try { localStorage.removeItem(SAVED_KEY); } catch (e) {}
}

/* reentrada automática: se este dispositivo já tem identidade nesta aula,
   valida-a no servidor e volta direto à atividade */
async function tryResume() {
  let saved = null;
  try { saved = JSON.parse(localStorage.getItem(SAVED_KEY) || "null"); } catch (e) {}
  if (!saved?.sessionId || !saved?.token) return false;
  try {
    const resp = await fetch(
      `/api/sessions/${saved.sessionId}/me?student_token=${encodeURIComponent(saved.token)}`
    );
    if (!resp.ok) {
      clearIdentity();
      return false;
    }
    const me = await resp.json();
    if (me.session.status !== "live") {
      clearIdentity();
      return false;
    }
    state.session = me.session;
    state.studentId = me.student_id;
    state.token = saved.token;
    state.displayName = me.display_name;
    startActivity();
    showMessage(`Bem-vinda de volta, ${me.display_name}!`, "feedback-ok");
    return true;
  } catch (e) {
    return false; // sem rede: fica no ecrã do código
  }
}

tryResume();

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
  saveIdentity();
  startActivity();
}

/* ---- passo 3: atividade ---- */

function startActivity() {
  stopActivityConnections();
  $("step-identity").hidden = true;
  $("step-activity").hidden = false;
  $("student-name").textContent = state.displayName;
  $("activity-title").textContent = state.session.activity_title;
  $("activity-frame").src = `/activities/${state.session.activity_slug}/`;
  listenToBridge();
  connectStream();
  flushTimer = setInterval(flushOutbox, 2000);
  // nota: o evento "joined" é emitido pelo servidor no claim; não repetir aqui
}

function stopActivityConnections() {
  streamRequest += 1;
  if (bridgeHandler) window.removeEventListener("message", bridgeHandler);
  if (stream) stream.close();
  if (flushTimer) clearInterval(flushTimer);
  bridgeHandler = null;
  stream = null;
  flushTimer = null;
}

/* eventos da atividade (PageCraftBridge → postMessage) */
function listenToBridge() {
  const frame = $("activity-frame");
  bridgeHandler = (ev) => {
    // aceitar apenas mensagens vindas do iframe da atividade
    if (!frame.contentWindow || ev.source !== frame.contentWindow) return;
    const d = ev.data;
    if (!d || d.pagecraft !== 1 || !d.type) return;
    queueEvent(d.type, d.unitId || null, sanitizePayload(d.payload));
  };
  window.addEventListener("message", bridgeHandler);
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
const STUDENT_EVENT_HANDLERS = {
  ai_feedback(data) {
    showMessage(data.payload.text, "feedback-warn");
    return { payload: { text: data.payload.text } };
  },
  teacher_message(data) {
    showMessage(`Professor: ${data.payload.text}`, "feedback-ok");
  },
  pit_updated(data) {
    state.pitItems[data.payload.id] = data.payload;
    renderPit();
  },
  teacher_highlight(data) {
    const { unit_id: unitId, unit_label: label } = data.payload || {};
    // fallback sempre visível, mesmo em atividades sem suporte
    showMessage(`👀 Olha para: ${label || unitId || "a atividade"}`, "feedback-warn");
    return { unitId };
  },
  freeze_screens() {
    $("freeze-overlay").hidden = false;
  },
  unfreeze_screens() {
    $("freeze-overlay").hidden = true;
  },
  session_closed() {
    $("freeze-overlay").hidden = true;
    showMessage("A aula terminou. Bom trabalho!", "feedback-ok");
    clearIdentity();
    stopActivityConnections();
  },
};

const FALLBACK_STUDENT_EVENT_TYPES = Object.keys(STUDENT_EVENT_HANDLERS).map((name) => ({
  name,
  bridge_name: name === "ai_feedback" ? "ai_feedback" : name === "teacher_highlight" ? "highlight" : null,
}));

async function loadStudentEventTypes() {
  try {
    const resp = await fetch("/api/session-event-types");
    if (!resp.ok) return FALLBACK_STUDENT_EVENT_TYPES;
    const declaration = await resp.json();
    if (!Array.isArray(declaration?.types)) return FALLBACK_STUDENT_EVENT_TYPES;
    const seen = new Set();
    return declaration.types
      .filter((entry) => {
        if (
          !entry ||
          entry.student_visible !== true ||
          typeof entry.name !== "string" ||
          !/^[a-z][a-z0-9_]*$/.test(entry.name) ||
          seen.has(entry.name)
        ) {
          return false;
        }
        seen.add(entry.name);
        return true;
      })
      .map((entry) => {
        return {
          name: entry.name,
          bridge_name:
            typeof entry.bridge_name === "string" &&
            /^[a-z][a-z0-9_]*$/.test(entry.bridge_name)
              ? entry.bridge_name
              : null,
        };
      });
  } catch (error) {
    return FALLBACK_STUDENT_EVENT_TYPES;
  }
}

function dispatchStudentEvent(declaration, rawData) {
  try {
    const data = JSON.parse(rawData);
    if (!data || typeof data !== "object" || Array.isArray(data)) return;
    const target = data.student_id;
    if (target != null && target !== state.studentId) return;
    const handler = STUDENT_EVENT_HANDLERS[declaration.name];
    if (!handler) return;
    const bridgePayload = handler(data);
    if (declaration.bridge_name && bridgePayload) {
      $("activity-frame").contentWindow?.postMessage(
        { pagecraft: 1, type: declaration.bridge_name, ...bridgePayload },
        "*"
      );
    }
  } catch (error) {
    // Um acontecimento incompreensível não pode interromper os seguintes.
  }
}

async function connectStream() {
  const request = ++streamRequest;
  const sessionId = state.session.id;
  const token = state.token;
  const eventTypes = await loadStudentEventTypes();
  if (request !== streamRequest) return;
  const es = new EventSource(
    `/api/sessions/${sessionId}/stream?role=student&student_token=${token}`
  );
  stream = es;
  eventTypes.forEach((declaration) => {
    es.addEventListener(declaration.name, (ev) => {
      dispatchStudentEvent(declaration, ev.data);
    });
  });
}

window.addEventListener("pagehide", stopActivityConnections);

// restauro via back-forward cache: o iframe mantém o estado da atividade,
// mas as ligações (bridge, SSE, outbox) foram fechadas no pagehide
window.addEventListener("pageshow", (ev) => {
  if (!ev.persisted || $("step-activity").hidden || !state.session) return;
  stopActivityConnections();
  listenToBridge();
  connectStream();
  flushTimer = setInterval(flushOutbox, 2000);
});

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
