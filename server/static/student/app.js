/* Página do aluno: entrar com código, escolher identidade, trabalhar na
   atividade (iframe + PageCraftBridge) e receber feedback em tempo real. */

const state = {
  session: null,
  studentId: null,
  token: null,
  displayName: null,
  studentState: null,
  sessionState: null,
};

const $ = (id) => document.getElementById(id);
const SAVED_KEY = "pagecraft_student";
const OUTBOX_LIMIT = 200;
const OUTBOX_BATCH_SIZE = 20;
const FLUSH_INTERVAL_MS = 2000;

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
  studentTransport.stop({ discardQueue: true });
  state.studentState = null;
  state.sessionState = null;
  $("freeze-overlay").hidden = true;
  $("step-identity").hidden = true;
  $("step-activity").hidden = false;
  $("student-name").textContent = state.displayName;
  $("activity-title").textContent = state.session.activity_title;
  $("activity-frame").src = `/activities/${state.session.activity_slug}/`;
  $("help-btn").disabled = false;
  $("pit-form").querySelectorAll("button, input").forEach((element) => {
    element.disabled = false;
  });
  studentTransport.start();
  // nota: o evento "joined" é emitido pelo servidor no claim; não repetir aqui
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

/* SSE: feedback IA, mensagens do professor, PIT */
const STUDENT_EVENT_HANDLERS = {
  ai_feedback(data) {
    showMessage(data.payload.text, "feedback-warn");
    return { payload: { text: data.payload.text } };
  },
  teacher_message(data) {
    showMessage(`Professor: ${data.payload.text}`, "feedback-ok");
  },
  teacher_highlight(data) {
    const { unit_id: unitId, unit_label: label } = data.payload || {};
    // fallback sempre visível, mesmo em atividades sem suporte
    showMessage(`👀 Olha para: ${label || unitId || "a atividade"}`, "feedback-warn");
    return { unitId };
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

function acceptStudentState(student) {
  if (!student || typeof student !== "object" || Array.isArray(student)) return;
  state.studentState = student;
  renderPit();
}

function acceptSessionState(session) {
  if (!session || typeof session !== "object" || Array.isArray(session)) return;
  const wasClosed = state.sessionState?.closed === true;
  state.sessionState = session;
  $("freeze-overlay").hidden = session.frozen !== true;
  if (session.closed === true && !wasClosed) {
    showMessage("A aula terminou. Bom trabalho!", "feedback-ok");
    finishStudentSession();
  }
}

function finishStudentSession() {
  studentTransport.stop({ discardQueue: true });
  clearIdentity();
  state.token = null;
  $("freeze-overlay").hidden = true;
  $("help-btn").disabled = true;
  $("pit-form").querySelectorAll("button, input").forEach((element) => {
    element.disabled = true;
  });
}

function invalidateStudentIdentity() {
  studentTransport.stop({ discardQueue: true });
  clearIdentity();
  state.studentId = null;
  state.token = null;
  state.displayName = null;
  state.studentState = null;
  state.sessionState = null;
  $("freeze-overlay").hidden = true;
  $("pit-panel").hidden = true;
  renderPit();
  $("activity-frame").src = "about:blank";
  $("step-activity").hidden = true;
  $("step-identity").hidden = true;
  $("step-code").hidden = false;
  $("code-status").textContent =
    "A tua identidade deixou de estar disponível. Volta a entrar.";
}

function dispatchStateFrame(type, rawData) {
  try {
    const data = JSON.parse(rawData);
    if (!data || typeof data !== "object" || Array.isArray(data)) return;
    if (type === "session_state_snapshot") {
      acceptStudentState(data.students?.[state.studentId]);
      acceptSessionState(data.session);
    } else if (type === "student_state_changed") {
      if (data.student_id !== state.studentId) return;
      acceptStudentState(data.student);
    } else if (type === "session_state_changed") {
      acceptSessionState(data.session);
    }
  } catch (error) {
    // Frames incompletos não substituem a última projeção válida.
  }
}

const studentTransport = createStudentTransport();

function createStudentTransport() {
  const outbox = [];
  let bridgeHandler = null;
  let stream = null;
  let generation = 0;
  let flushTimer = null;
  let flushing = false;
  let validatingIdentity = false;
  const requests = new Set();

  function stop({ discardQueue = false } = {}) {
    generation += 1;
    if (bridgeHandler) window.removeEventListener("message", bridgeHandler);
    if (stream) stream.close();
    if (flushTimer) clearInterval(flushTimer);
    bridgeHandler = null;
    stream = null;
    flushTimer = null;
    requests.forEach((controller) => controller.abort());
    requests.clear();
    if (discardQueue) outbox.length = 0;
  }

  function enqueue(type, unitId, payload) {
    if (!state.token || outbox.length >= OUTBOX_LIMIT) return false;
    outbox.push({
      event_id: crypto.randomUUID(),
      type,
      unit_id: unitId,
      payload,
      ts: new Date().toISOString(),
    });
    return true;
  }

  function listenToBridge() {
    const frame = $("activity-frame");
    bridgeHandler = (ev) => {
      // aceitar apenas mensagens vindas do iframe da atividade
      if (!frame.contentWindow || ev.source !== frame.contentWindow) return;
      const data = ev.data;
      if (!data || data.pagecraft !== 1 || !data.type) return;
      enqueue(
        data.type,
        data.unitId || null,
        sanitizePayload(data.payload)
      );
    };
    window.addEventListener("message", bridgeHandler);
  }

  async function post(path, body) {
    if (!state.token) return null;
    const controller = new AbortController();
    requests.add(controller);
    try {
      const resp = await fetch(path, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ ...body, student_token: state.token }),
        signal: controller.signal,
      });
      if (resp.status === 401) {
        invalidateStudentIdentity();
        return null;
      }
      return resp;
    } catch (error) {
      return null;
    } finally {
      requests.delete(controller);
    }
  }

  async function flush() {
    if (flushing || !outbox.length || !state.token) return;
    flushing = true;
    const batch = outbox.slice(0, OUTBOX_BATCH_SIZE);
    try {
      const resp = await post(
        `/api/sessions/${state.session.id}/events`,
        { events: batch }
      );
      if (resp?.ok) {
        const ids = new Set(batch.map((event) => event.event_id));
        for (let index = outbox.length - 1; index >= 0; index -= 1) {
          if (ids.has(outbox[index].event_id)) outbox.splice(index, 1);
        }
      }
    } catch (error) {
      /* fica na fila; tentamos outra vez no próximo flush (at-least-once) */
    } finally {
      flushing = false;
    }
  }

  async function validateIdentity(request, sessionId, token) {
    if (validatingIdentity || request !== generation) return;
    validatingIdentity = true;
    const controller = new AbortController();
    requests.add(controller);
    try {
      const resp = await fetch(
        `/api/sessions/${sessionId}/me?student_token=${encodeURIComponent(token)}`,
        { signal: controller.signal }
      );
      if (request !== generation) return;
      if (resp.status === 401) invalidateStudentIdentity();
    } catch (error) {
      // Uma falha de rede é transitória; o EventSource continua a reconectar.
    } finally {
      requests.delete(controller);
      validatingIdentity = false;
    }
  }

  async function connect(request, sessionId, token) {
    const eventTypes = await loadStudentEventTypes();
    if (request !== generation) return;
    const eventStream = new EventSource(
      `/api/sessions/${sessionId}/stream?role=student&student_token=${encodeURIComponent(token)}`
    );
    stream = eventStream;
    eventStream.addEventListener("error", () => {
      validateIdentity(request, sessionId, token);
    });
    [
      "session_state_snapshot",
      "student_state_changed",
      "session_state_changed",
    ].forEach((type) => {
      eventStream.addEventListener(
        type,
        (ev) => dispatchStateFrame(type, ev.data)
      );
    });
    eventTypes.forEach((declaration) => {
      eventStream.addEventListener(declaration.name, (ev) => {
        dispatchStudentEvent(declaration, ev.data);
      });
    });
  }

  function start() {
    stop();
    const request = ++generation;
    const sessionId = state.session.id;
    const token = state.token;
    listenToBridge();
    flushTimer = setInterval(flush, FLUSH_INTERVAL_MS);
    connect(request, sessionId, token);
  }

  return { enqueue, flush, post, start, stop };
}

window.addEventListener("pagehide", () => studentTransport.stop());

// restauro via back-forward cache: o iframe mantém o estado da atividade,
// mas as ligações (bridge, SSE, fila) foram fechadas no pagehide
window.addEventListener("pageshow", (ev) => {
  if (!ev.persisted || $("step-activity").hidden || !state.session) return;
  studentTransport.start();
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
  studentTransport.enqueue("help_needed", null, { note: "botão de ajuda" });
  showMessage("O professor já sabe que precisas de ajuda.", "feedback-ok");
});

$("pit-btn").addEventListener("click", () => {
  $("pit-panel").hidden = !$("pit-panel").hidden;
});

$("pit-form").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const text = $("pit-text").value.trim();
  if (!text) return;
  const resp = await studentTransport.post(
    `/api/sessions/${state.session.id}/pit`,
    { text }
  );
  if (resp?.ok) {
    const item = await resp.json();
    acceptPitItem(item);
    $("pit-text").value = "";
  }
});

const PIT_LABELS = { planned: "por fazer", doing: "a fazer", done: "feito", to_share: "para partilhar" };

function acceptPitItem(item) {
  if (!item || typeof item !== "object" || Array.isArray(item) || !item.id) return;
  const current = Array.isArray(state.studentState?.pit_items)
    ? state.studentState.pit_items
    : [];
  let replaced = false;
  const pitItems = current.map((candidate) => {
    if (candidate.id !== item.id) return candidate;
    replaced = true;
    return item;
  });
  if (!replaced) pitItems.push(item);
  state.studentState = {
    ...(state.studentState || {}),
    pit_items: pitItems,
  };
  renderPit();
}

function renderPit() {
  const list = $("pit-list");
  list.innerHTML = "";
  const pitItems = Array.isArray(state.studentState?.pit_items)
    ? state.studentState.pit_items
    : [];
  pitItems.forEach((item) => {
    const li = document.createElement("li");
    const btn = document.createElement("button");
    btn.className = "ghost";
    btn.style.minHeight = "48px";
    btn.textContent = PIT_LABELS[item.status] || item.status;
    btn.addEventListener("click", async () => {
      const resp = await studentTransport.post(
        `/api/sessions/${state.session.id}/pit/${encodeURIComponent(item.id)}/advance`,
        {}
      );
      if (resp?.ok) {
        acceptPitItem(await resp.json());
      }
    });
    li.append(btn, document.createTextNode(" " + item.text));
    list.appendChild(li);
  });
}
