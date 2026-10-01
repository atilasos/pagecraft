/* Página do aluno: entrar com código, escolher identidade, trabalhar na
   atividade (iframe + PageCraftBridge) e receber feedback em tempo real. */

const state = {
  session: null,
  studentId: null,
  workGroup: null,
  displayName: null,
  studentState: null,
  sessionState: null,
  restoringWork: false,
  restoreGeneration: 0,
};

let workMode = "alone";
const selectedParticipants = new Set();
const $ = (id) => document.getElementById(id);
const hasIdentity = () => !!(state.studentId || state.workGroup);
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
        studentId: state.studentId,
        displayName: state.displayName,
        workGroupId: state.workGroup?.id,
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
  if (!saved?.sessionId) return false;
  try {
    const resp = await fetch(`/api/sessions/${saved.sessionId}/me`);
    if (!resp.ok) {
      clearIdentity();
      return false;
    }
    const me = await resp.json();
    state.session = me.session;
    state.studentId = me.student_id;
    state.workGroup = me.work_group || null;
    state.displayName = state.workGroup?.display_name || me.display_name;
    startActivity();
    showMessage(`Bem-vindos de volta, ${state.displayName}!`, "feedback-ok");
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
    const resumingGroup = code.length === 8;
    const resp = await fetch(resumingGroup ? '/api/groups/enter' : `/api/join/${encodeURIComponent(code)}`,
      resumingGroup ? {method:'POST', headers:{'content-type':'application/json'}, body:JSON.stringify({code})} : {});
    if (!resp.ok) throw new Error((await resp.json()).detail || "código não encontrado");
    const data = await resp.json();
    status.textContent = "";
    if (resumingGroup) {
      state.session = data.session;
      state.studentId = null;
      state.workGroup = data.work_group;
      state.displayName = data.work_group.display_name;
      saveIdentity();
      startActivity();
    } else {
      state.session = data;
      showIdentityStep();
    }
  } catch (err) {
    status.textContent = err.message;
  }
});

/* ---- passo 2: identidade ---- */

function showIdentityStep() {
  $("step-code").hidden = true;
  $("step-identity").hidden = false;
  $("session-title").textContent = `${state.session.class_name} · ${state.session.activity_title}`;
  renderIdentityChoices();
}

function renderIdentityChoices() {
  const grid = $("identities");
  grid.replaceChildren();
  state.session.roster.forEach((student) => {
    const button = document.createElement("button");
    button.type = "button";
    const selected = selectedParticipants.has(student.student_id);
    button.textContent = (selected ? "✓ " : "") + student.display_name;
    button.setAttribute("aria-label", student.display_name);
    button.setAttribute("aria-pressed", String(selected));
    button.disabled = student.taken;
    button.addEventListener("click", () => {
      if (selectedParticipants.has(student.student_id)) selectedParticipants.delete(student.student_id);
      else {
        if (workMode === "alone") selectedParticipants.clear();
        selectedParticipants.add(student.student_id);
      }
      renderIdentityChoices();
      [...grid.children].find(item => item.getAttribute("aria-label") === student.display_name)?.focus();
    });
    grid.appendChild(button);
  });
  document.querySelectorAll("[data-work-mode]").forEach(button => button.setAttribute("aria-pressed", String(button.dataset.workMode === workMode)));
  const count = selectedParticipants.size;
  const valid = workMode === "alone" ? count === 1 : workMode === "pair" ? count === 2 : count >= 3;
  $("confirm-participants").disabled = !valid;
  $("entry-group-level").hidden = workMode === "alone";
  const names = state.session.roster.filter(student => selectedParticipants.has(student.student_id)).map(student => student.display_name);
  $("selected-participants").textContent = names.length ? names.join(" + ") : workMode === "alone" ? "Escolhe o teu nome." : workMode === "pair" ? "Escolham dois nomes." : "Escolham três ou mais nomes.";
}

for (const button of document.querySelectorAll("[data-work-mode]")) button.addEventListener("click", () => {
  workMode = button.dataset.workMode;
  selectedParticipants.clear();
  $("claim-status").textContent = "";
  renderIdentityChoices();
});

$("confirm-participants").addEventListener("click", async () => {
  $("confirm-participants").disabled = true;
  const student = state.session.roster.find(item => selectedParticipants.has(item.student_id));
  try { await claim(student); }
  catch { $("claim-status").textContent = "Não foi possível entrar. Tenta novamente."; }
  finally { renderIdentityChoices(); }
});

async function claim(student) {
  const status = $("claim-status");
  const joint = workMode !== "alone";
  status.textContent = joint ? "A entrar com o grupo…" : `A entrar como ${student.display_name}…`;
  const resp = await fetch(`/api/sessions/${state.session.id}/${joint ? "groups/claim" : "claim"}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(joint ? { participant_ids: [...selectedParticipants], mode: workMode, level: $("entry-level").value } : { student_id: student.student_id }),
  });
  if (!resp.ok) {
    status.textContent = (await resp.json()).detail || "não foi possível";
    return;
  }
  const data = await resp.json();
  state.studentId = data.student_id || null;
  state.workGroup = data.work_group || null;
  state.displayName = state.workGroup?.display_name || data.display_name;
  saveIdentity();
  startActivity();
}

/* ---- passo 3: atividade ---- */

function startActivity() {
  groupReflection.mount();
  studentTransport.stop({ discardQueue: true });
  state.studentState = null;
  state.sessionState = null;
  $("freeze-overlay").hidden = true;
  $("step-code").hidden = true;
  $("step-identity").hidden = true;
  $("step-activity").hidden = false;
  $("history-panel").hidden = true;
  $("student-name").textContent = state.displayName;
  $("activity-title").textContent = state.session.activity_title;
  state.restoringWork = true;
  state.restoreGeneration += 1;
  $("activity-frame").hidden = true;
  $("restore-work").hidden = false;
  $("restore-status").textContent = 'A recuperar o trabalho guardado…';
  $("restore-retry").hidden = true;
  $("save-work").disabled = true;
  $("activity-frame").src = `/api/sessions/${state.session.id}/content`;
  $("group-level-label").hidden = !state.workGroup;
  $("group-level").disabled = false;
  if (state.workGroup) $("group-level").value = state.workGroup.level;
  $("pit-btn").hidden = !!state.workGroup;
  $("help-btn").disabled = false;
  $("pit-form").querySelectorAll("button, input").forEach((element) => {
    element.disabled = false;
  });
  studentTransport.start();
  // nota: o evento "joined" é emitido pelo servidor no claim; não repetir aqui
}

function sanitizePayload(payload) {
  try {
    if (!payload || typeof payload !== 'object' || Array.isArray(payload)) return {};
    const json = JSON.stringify(payload);
    if (new TextEncoder().encode(json).length > 4096) return null;
    return JSON.parse(json);
  } catch { return null; }
}

async function restoreWork() {
  if (!hasIdentity()) return;
  const generation = state.restoreGeneration;
  const sessionId = state.session.id;
  try {
    const path = state.workGroup ? 'groups/me/history' : `students/${state.studentId}/history`;
    const response = await fetch(`/api/sessions/${sessionId}/${path}`);
    if (generation !== state.restoreGeneration) return;
    if (response.status === 401) { invalidateStudentIdentity(); return; }
    if (!response.ok) throw new Error('history');
    const history = await response.json();
    if (!Array.isArray(history.events)) throw new Error('history');
    state.restoringWork = false;
    $('activity-frame').contentWindow?.postMessage({pagecraft:1, type:'learning_restore',
      payload:{events:history.events}}, '*');
    sendGroupPreferences();
    // Let the activity apply both messages before a child can edit its controls.
    await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    if (generation !== state.restoreGeneration) return;
    $('restore-work').hidden = true;
    $('activity-frame').hidden = false;
    $('save-work').disabled = false;
  } catch {
    if (generation !== state.restoreGeneration) return;
    $('restore-status').textContent = 'Não foi possível recuperar o trabalho. Tenta novamente.';
    $('restore-retry').hidden = false;
  }
}
$('restore-retry').addEventListener('click', restoreWork);

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
    if (target != null && target !== state.studentId && !state.workGroup?.participant_ids.includes(target)) return;
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
  $("freeze-overlay").hidden = true;
  $("help-btn").disabled = true;
  $("group-level").disabled = true;
  $("save-work").disabled = true;
  $("pit-form").querySelectorAll("button, input").forEach((element) => {
    element.disabled = true;
  });
  loadOwnHistory();
}

function invalidateStudentIdentity() {
  state.restoreGeneration += 1;
  groupReflection.reset();
  studentTransport.stop({ discardQueue: true });
  clearIdentity();
  state.studentId = null;
  state.workGroup = null;
  state.displayName = null;
  state.studentState = null;
  state.sessionState = null;
  $("freeze-overlay").hidden = true;
  $("pit-panel").hidden = true;
  $("history-panel").hidden = true;
  $("history-list").innerHTML = "";
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
      if (state.workGroup && data.groups?.[state.workGroup.id]) acceptGroupState(data.groups[state.workGroup.id]);
      acceptSessionState(data.session);
    } else if (type === "work_group_state_changed") {
      if (state.workGroup?.id === data.work_group_id) acceptGroupState(data.group);
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
  let queueKey = null;
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
    persistQueue();
    if (discardQueue) { outbox.length = 0; queueKey = null; }
  }

  function enqueue(type, unitId, payload) {
    const currentQueue = outbox.filter(event => !event.composition_conflict);
    if (!hasIdentity() || currentQueue.length >= OUTBOX_LIMIT) return false;
    outbox.push({
      event_id: crypto.randomUUID(),
      type,
      unit_id: unitId,
      payload,
      ts: new Date().toISOString(),
      ...(state.workGroup ? {composition_version:state.workGroup.composition_version, access_version:state.workGroup.access_version, work_group_name:state.workGroup.display_name} : {}),
    });
    persistQueue();
    renderPendingWork();
    return true;
  }

  function persistQueue() {
    if (!queueKey) return;
    try { sessionStorage.setItem(queueKey, JSON.stringify(outbox)); } catch {}
  }

  function renderPendingWork() {
    const previous = outbox.filter(event => event.composition_conflict && HISTORY_LABELS[event.type]);
    const panel = $("pending-group-work");
    panel.hidden = !previous.length;
    $("pending-group-list").replaceChildren();
    const captions = new Set(previous.map(event => `${event.work_group_name || 'Grupo anterior'} · ${HISTORY_LABELS[event.type]}${event.payload?.detail ? ': '+event.payload.detail : ''}`));
    for (const caption of captions) {
      const item = document.createElement('li');
      item.textContent = caption;
      $("pending-group-list").append(item);
    }
  }

  function listenToBridge() {
    const frame = $("activity-frame");
    bridgeHandler = (ev) => {
      // aceitar apenas mensagens vindas do iframe da atividade
      if (!frame.contentWindow || ev.source !== frame.contentWindow) return;
      const data = ev.data;
      if (!data || data.pagecraft !== 1 || !data.type) return;
      if (state.restoringWork && ['activity_state', 'unit_started', 'level_changed', 'assessment_result'].includes(data.type)) return;
      const declaration = data.payload?.detail;
      const sharedWork = declaration && typeof declaration === 'object' &&
        declaration.activity === state.session.activity_slug && (declaration.field || declaration.productChanged);
      if (state.workGroup && (data.type === 'open_reflection' || (data.type === 'assessment_result' && !sharedWork))) {
        // Legacy self-assessment is a request to open individual voice, never a group answer.
        if (data.type === "open_reflection") groupReflection.open();
        return;
      }
      if (state.workGroup && data.type === "level_changed") {
        if (data.payload?.level === state.workGroup.level) return;
        if (["support", "intermediate", "challenge"].includes(data.payload?.level)) {
          state.workGroup.level = data.payload.level;
          $("group-level").value = data.payload.level;
          sendGroupPreferences();
        }
      }
      const payload = sanitizePayload(data.payload);
      if (payload !== null) {
        if (['assessment_result', 'attempt', 'level_changed'].includes(data.type)) $('save-work-status').textContent = '';
        enqueue(data.type, data.unitId || null, payload);
      }
    };
    window.addEventListener("message", bridgeHandler);
  }

  async function post(path, body) {
    if (!hasIdentity()) return null;
    const controller = new AbortController();
    requests.add(controller);
    try {
      const resp = await fetch(path, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(body),
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
    if (flushing || !outbox.length || !hasIdentity()) return;
    flushing = true;
    const batch = outbox.filter(event => !event.composition_conflict).slice(0, OUTBOX_BATCH_SIZE);
    if (!batch.length) { flushing = false; return; }
    const request = generation;
    try {
      const resp = await post(
        `/api/sessions/${state.session.id}/events`,
        { events: batch }
      );
      if (resp?.status === 409) {
        const error = await resp.json();
        if (request !== generation) return;
        if (error.detail?.code === 'composition_changed') {
          const conflicts = new Set(error.detail.event_ids);
          outbox.forEach(event => { if (conflicts.has(event.event_id)) event.composition_conflict = true; });
          acceptComposition(error.detail.work_group);
        }
      } else if (resp?.ok) {
        const ids = new Set(batch.map((event) => event.event_id));
        for (let index = outbox.length - 1; index >= 0; index -= 1) {
          if (ids.has(outbox[index].event_id)) outbox.splice(index, 1);
        }
      }
    } catch (error) {
      /* fica na fila; tentamos outra vez no próximo flush (at-least-once) */
    } finally {
      persistQueue();
      renderPendingWork();
      flushing = false;
    }
  }

  async function validateIdentity(request, sessionId) {
    if (validatingIdentity || request !== generation) return;
    validatingIdentity = true;
    const controller = new AbortController();
    requests.add(controller);
    try {
      const resp = await fetch(`/api/sessions/${sessionId}/me`, {
        signal: controller.signal,
      });
      if (request !== generation) return;
      if (resp.status === 401) invalidateStudentIdentity();
      else if (resp.ok) {
        const identity = await resp.json();
        if (request !== generation) return;
        if (identity.work_group) acceptComposition(identity.work_group);
      }
    } catch (error) {
      // Uma falha de rede é transitória; o EventSource continua a reconectar.
    } finally {
      requests.delete(controller);
      validatingIdentity = false;
    }
  }

  async function connect(request, sessionId) {
    const eventTypes = await loadStudentEventTypes();
    if (request !== generation) return;
    const eventStream = new EventSource(`/api/sessions/${sessionId}/stream`);
    stream = eventStream;
    eventStream.addEventListener("error", () => {
      validateIdentity(request, sessionId);
    });
    [
      "session_state_snapshot",
      "student_state_changed",
      "work_group_state_changed",
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
    const nextKey = state.workGroup ? `pc-group-outbox:${sessionId}:${state.workGroup.device_id}` : null;
    if (nextKey !== queueKey) {
      outbox.length = 0; queueKey = nextKey;
      try { outbox.push(...JSON.parse(sessionStorage.getItem(queueKey) || '[]')); } catch {}
    }
    markPreviousComposition();
    renderPendingWork();
    listenToBridge();
    flushTimer = setInterval(flush, FLUSH_INTERVAL_MS);
    connect(request, sessionId);
  }

  async function savePending() {
    for (let tries = 0; tries < 100; tries++) {
      if (flushing) { await new Promise(resolve => setTimeout(resolve, 50)); continue; }
      const before = outbox.length;
      if (!before) return true;
      await flush();
      if (outbox.length >= before) return false;
    }
    return outbox.length === 0;
  }

  function markPreviousComposition() {
    if (!state.workGroup) return;
    outbox.forEach(event => {
      if (event.composition_version !== state.workGroup.composition_version ||
          (event.access_version || 1) !== state.workGroup.access_version) event.composition_conflict = true;
    });
    persistQueue();
  }

  return {
    enqueue, flush, post, start, stop, savePending, markPreviousComposition,
    pendingLevel: () => outbox.findLast(event => event.type === "level_changed" && !event.composition_conflict)?.payload.level,
  };
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

$('save-work').addEventListener('click', async () => {
  $('save-work').disabled = true;
  $('save-work-status').textContent = 'A guardar…';
  // Leaving the activity commits its focused field through the existing bridge.
  await new Promise(resolve => setTimeout(resolve, 50));
  const saved = await studentTransport.savePending();
  $('save-work-status').textContent = saved ? 'Guardado. Podem continuar na próxima aula.' :
    'Ainda não foi possível guardar tudo. Mantém esta página aberta e tenta novamente.';
  $('save-work').disabled = state.sessionState?.closed === true;
});

const HISTORY_LABELS = {
  unit_started: "Comecei uma parte",
  level_changed: "Mudei de nível de diferenciação",
  attempt: "Fiz uma tentativa",
  discovery: "Fiz uma descoberta",
  assessment_result: "Registei um resultado",
  feedback_request: "Pedi feedback",
  help_needed: "Pedi ajuda",
  share_requested: "Escolhi para partilhar",
  ai_feedback: "Recebi feedback",
  teacher_message: "Recebi uma mensagem",
  teacher_highlight: "O professor chamou a atenção",
  pit_updated: "Atualizei o meu plano",
};

function describeHistoryEvent(event) {
  const payload = event?.payload || {};
  const detail =
    payload.message ||
    payload.text ||
    (typeof payload.detail === "object" ? payload.detail.note || payload.detail.value : payload.detail) ||
    payload.note ||
    payload.what ||
    "";
  const label = (event?.work_group_id ? `Trabalho conjunto · ${event.work_group_name || ""} · ` : "") + (HISTORY_LABELS[event?.type] || "Trabalho registado");
  return detail ? `${label}: ${detail}` : label;
}

async function loadOwnHistory() {
  if (!state.session?.id || !hasIdentity()) return;
  try {
    const resp = await fetch(
      state.workGroup ? `/api/sessions/${state.session.id}/groups/me/history` : `/api/sessions/${state.session.id}/students/${state.studentId}/history`
    );
    if (resp.status === 401) {
      invalidateStudentIdentity();
      return;
    }
    if (!resp.ok) return;
    const history = await resp.json();
    const list = $("history-list");
    list.innerHTML = "";
    const events = Array.isArray(history?.events) ? history.events.filter(event => event.type !== "activity_state") : [];
    if (!events.length) {
      const empty = document.createElement("li");
      empty.textContent = "Ainda não há trabalho registado.";
      list.appendChild(empty);
    } else {
      events.forEach((event) => {
        const item = document.createElement("li");
        item.textContent = describeHistoryEvent(event);
        list.appendChild(item);
      });
    }
    $("history-panel").hidden = false;
  } catch (error) {
    // O histórico continua disponível quando a ligação regressar.
  }
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

function sendGroupPreferences() {
  if (!state.workGroup || state.restoringWork) return;
  $("activity-frame").contentWindow?.postMessage({pagecraft:1, type:"work_group_preferences", payload:{level:state.workGroup.level}}, '*');
  $("activity-frame").contentWindow?.postMessage({pagecraft:1, type:"learning_preferences", payload:{level:state.workGroup.level}}, '*');
}

function acceptComposition(group) {
  if (!state.workGroup || group.device_id !== state.workGroup.device_id ||
      (group.composition_version <= state.workGroup.composition_version && group.access_version <= state.workGroup.access_version)) return;
  const participantsChanged = group.composition_version !== state.workGroup.composition_version;
  state.workGroup = group;
  studentTransport.markPreviousComposition();
  state.displayName = group.display_name;
  $("student-name").textContent = group.display_name;
  $("group-level").value = group.level;
  sendGroupPreferences();
  saveIdentity();
  groupReflection.mount();
  showMessage(participantsChanged ? `O professor alterou os participantes: ${group.display_name}. O trabalho anterior mantém os seus autores.` :
    'A entrada no grupo foi renovada. Os envios antigos ficam separados do trabalho atual.', "feedback-warn");
  studentTransport.start();
}

function acceptGroupState(group) {
  if (!group) return;
  const pendingLevel = studentTransport.pendingLevel();
  if (pendingLevel && pendingLevel !== group.level) return;
  const levelChanged = state.workGroup.level !== group.level;
  state.workGroup.level = group.level;
  $("group-level").value = group.level;
  if (levelChanged) sendGroupPreferences();
}

$("activity-frame").addEventListener("load", restoreWork);
$("group-level").addEventListener("change", () => {
  if (!state.workGroup) return;
  state.workGroup.level = $("group-level").value;
  studentTransport.enqueue("level_changed", null, {level:state.workGroup.level});
  sendGroupPreferences();
});
