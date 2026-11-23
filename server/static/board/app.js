let publicOrigin = location.origin;
/* Quadro passivo: o emparelhamento cria o Papel Quadro; depois só lê a
   Sessão de aula e os seus Acontecimentos coletivos. */

const pairing = document.getElementById("pairing");
const waiting = document.getElementById("waiting");
const live = document.getElementById("live");
const pairingCode = document.getElementById("pairing-code");
const pairingStatus = document.getElementById("pairing-status");
const waitingStatus = document.getElementById("waiting-status");
const sessionTitle = document.getElementById("session-title");
const sessionStatus = document.getElementById("session-status");
const sessionEntryUrl = document.getElementById("session-entry-url");
const sessionJoinCode = document.getElementById("session-join-code");
const board = document.getElementById("board");

let pairingTimer = null;
let sessionTimer = null;
let stream = null;
let currentSessionId = null;

function show(view) {
  pairing.hidden = view !== pairing;
  waiting.hidden = view !== waiting;
  live.hidden = view !== live;
}

function later(callback, delay) {
  return window.setTimeout(callback, delay);
}

function clearTimer(timer) {
  if (timer !== null) window.clearTimeout(timer);
}

function showPairingCode(code) {
  pairingCode.replaceChildren();
  [...code].forEach((character) => {
    const block = document.createElement("span");
    block.textContent = character;
    pairingCode.appendChild(block);
  });
}

async function createPairing() {
  stopLiveSession();
  clearTimer(pairingTimer);
  clearTimer(sessionTimer);
  show(pairing);
  pairingCode.replaceChildren();
  pairingStatus.textContent = "A preparar o código…";

  try {
    const response = await fetch("/api/board/pairings", { method: "POST" });
    if (!response.ok) {
      pairingStatus.textContent = "Não foi possível criar o código. A tentar novamente…";
      pairingTimer = later(createPairing, 3000);
      return;
    }
    const candidate = await response.json();
    if (
      typeof candidate?.pairing_id !== "string" ||
      typeof candidate?.code !== "string"
    ) {
      throw new Error("resposta de emparelhamento incompreensível");
    }
    showPairingCode(candidate.code);
    pairingStatus.textContent = "À espera da confirmação do professor…";
    completePairing(candidate.pairing_id);
  } catch (error) {
    pairingStatus.textContent = "Sem ligação ao servidor. A tentar novamente…";
    pairingTimer = later(createPairing, 3000);
  }
}

async function completePairing(pairingId) {
  clearTimer(pairingTimer);
  try {
    const response = await fetch("/api/board/pairings/complete", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ pairing_id: pairingId }),
    });
    if (response.status === 202) {
      pairingTimer = later(() => completePairing(pairingId), 1500);
      return;
    }
    if (response.ok) {
      pairingStatus.textContent = "Quadro emparelhado.";
      await checkSession();
      return;
    }
    if (response.status === 404 || response.status === 410) {
      await createPairing();
      return;
    }
    pairingStatus.textContent = "Não foi possível confirmar. A tentar novamente…";
    pairingTimer = later(() => completePairing(pairingId), 2500);
  } catch (error) {
    pairingStatus.textContent = "Sem ligação ao servidor. A tentar novamente…";
    pairingTimer = later(() => completePairing(pairingId), 2500);
  }
}

async function checkSession() {
  clearTimer(sessionTimer);
  try {
    const response = await fetch("/api/board/session");
    if (response.status === 401 || response.status === 403) {
      await createPairing();
      return;
    }
    if (response.status === 204) {
      stopLiveSession();
      show(waiting);
      waitingStatus.textContent = "A aguardar que o professor comece uma sessão.";
      sessionTimer = later(checkSession, 2500);
      return;
    }
    if (!response.ok) {
      show(waiting);
      waitingStatus.textContent = "Não foi possível consultar a aula. A tentar novamente…";
      sessionTimer = later(checkSession, 3000);
      return;
    }
    const session = await response.json();
    if (session?.kind === "lesson") {
      startLessonFocus(session);
      sessionTimer = later(checkSession, 3000);
      return;
    }
    if (
      typeof session?.id !== "string" ||
      typeof session?.activity_slug !== "string"
    ) {
      throw new Error("sessão incompreensível");
    }
    startLiveSession(session);
  } catch (error) {
    show(waiting);
    waitingStatus.textContent = "Sem ligação ao servidor. A tentar novamente…";
    sessionTimer = later(checkSession, 3000);
  }
}

/* Atividade de um Roteiro da aula escolhida pelo professor: só a atividade
   e o código de entrada, sem stream nem trabalho individual. */
function startLessonFocus(focus) {
  if (
    typeof focus.id !== "string" ||
    typeof focus.lesson_code !== "string" ||
    typeof focus.activity_code !== "string"
  ) {
    throw new Error("roteiro incompreensível");
  }
  if (currentSessionId === focus.id && !stream) {
    show(live);
    return;
  }
  stopLiveSession();
  show(live);
  sessionTitle.textContent = `${focus.class_name} · ${focus.activity_title}`;
  sessionStatus.textContent = "Roteiro da aula";
  sessionEntryUrl.textContent = `${new URL(publicOrigin).host}/aula/${focus.lesson_code}`;
  document.getElementById("session-code-label").textContent = "Código do roteiro";
  sessionJoinCode.textContent = focus.lesson_code;
  board.src = `/api/board/lesson-content?atividade=${encodeURIComponent(focus.activity_code)}&presentation=1`;
  currentSessionId = focus.id;
}

/* Os jogos do ciclo esperam o arranque que a página do aluno lhes dá. O quadro
   envia uma realização vazia, sem dados de nenhum aluno. */
board.addEventListener("load", () => {
  if (!currentSessionId?.startsWith("lesson-") || !board.getAttribute("src")) return;
  board.contentWindow?.postMessage({ pagecraft: 1, type: "learning_restore", payload: { events: [] } }, "*");
  board.contentWindow?.postMessage({
    pagecraft: 1,
    type: "learning_preferences",
    payload: { language: "pt", level: "intermediate", participant_count: 1, route: "permanent" },
  }, "*");
});

function startLiveSession(session) {
  if (currentSessionId === session.id && stream) return;
  stopLiveSession();
  show(live);
  sessionTitle.textContent = `${session.class_name} · ${session.activity_title}`;
  sessionStatus.textContent = "Aula em curso";
  document.getElementById("session-code-label").textContent = "Código da atividade";
  sessionEntryUrl.textContent = new URL(publicOrigin).host;
  sessionJoinCode.textContent = session.join_code;

  // Presentation changes lesson navigation only; board access stays on its existing policy.
  const activityUrl = `/api/board/sessions/${encodeURIComponent(session.id)}/content?presentation=1`;
  if (board.getAttribute("src") !== activityUrl) board.src = activityUrl;
  currentSessionId = session.id;
  stream = new EventSource(`/api/board/sessions/${session.id}/stream`);
  const activeStream = stream;
  stream.addEventListener("session_state_snapshot", (event) => {
    if (stream !== activeStream) return;
    const snapshot = parseObject(event.data);
    if (!snapshot) return;
    registerCollectiveEventListeners(activeStream, snapshot.event_types);
    applySessionState(snapshot);
  });
  stream.addEventListener("session_state_changed", (event) => {
    if (stream !== activeStream) return;
    const delta = parseObject(event.data);
    if (delta) applySessionState(delta);
  });
  stream.addEventListener("error", () => {
    if (stream !== activeStream) return;
    finishLiveSession("A atualizar a sessão no quadro…");
  });
}

function parseObject(rawData) {
  try {
    const data = JSON.parse(rawData);
    return data && typeof data === "object" && !Array.isArray(data) ? data : null;
  } catch (error) {
    return null;
  }
}

function registerCollectiveEventListeners(activeStream, declarations) {
  if (!Array.isArray(declarations)) return;
  const registeredNames = new Set();
  declarations.forEach((declaration) => {
    if (
      !declaration ||
      typeof declaration.name !== "string" ||
      !/^[a-z][a-z0-9_]*$/.test(declaration.name) ||
      registeredNames.has(declaration.name)
    ) {
      return;
    }
    const bridgeName =
      typeof declaration.bridge_name === "string" &&
      /^[a-z][a-z0-9_]*$/.test(declaration.bridge_name)
        ? declaration.bridge_name
        : null;
    const safeDeclaration = {
      name: declaration.name,
      bridge_name: bridgeName,
    };
    registeredNames.add(safeDeclaration.name);
    activeStream.addEventListener(safeDeclaration.name, (event) => {
      if (stream !== activeStream) return;
      dispatchCollectiveEvent(safeDeclaration, event.data);
    });
  });
}

function finishLiveSession(message) {
  stopLiveSession();
  showClassSentence(null);
  show(waiting);
  waitingStatus.textContent = message;
  sessionTimer = later(checkSession, 1500);
}

function showClassSentence(sentence) {
  let panel = document.getElementById('class-sentence-panel');
  if (!panel) {
    panel = document.createElement('div'); panel.id = 'class-sentence-panel';
    panel.setAttribute('role', 'status');
    panel.style.cssText = 'position:fixed;inset:0;z-index:100;display:flex;align-items:center;justify-content:center;padding:5vw;background:#fff;color:#182b32;font:700 clamp(48px,7vw,120px)/1.4 "Century Gothic","Didact Gothic","URW Gothic",sans-serif;text-align:center;white-space:pre-wrap';
    document.body.appendChild(panel);
  }
  panel.textContent = sentence?.text || '';
  panel.style.display = sentence ? 'flex' : 'none';
}
function applySessionState(data) {
  const state = data.session;
  if (!state || typeof state !== "object" || Array.isArray(state)) return;
  showClassSentence(state.class_sentence);
  const showingCodes = state.group_codes_visible === true;
  document.getElementById('group-codes-panel').hidden = !showingCodes;
  board.hidden = showingCodes;
  document.getElementById('group-entry-url').textContent = `${publicOrigin}/student/`;
  const grid = document.getElementById('group-codes-grid');
  grid.replaceChildren();
  for (const group of state.group_codes || []) {
    const card = document.createElement('article');
    const name = document.createElement('h2'); name.textContent = group.display_name;
    const code = document.createElement('p'); code.className = 'group-access-code';
    code.textContent = group.code || 'Grupo já entrou';
    card.append(name, code); grid.append(card);
  }
  if (state.closed === true || state.status === "closed") {
    finishLiveSession("Sessão terminada. A aguardar a próxima aula.");
  }
}

function dispatchCollectiveEvent(declaration, rawData) {
  const data = parseObject(rawData);
  if (!data) return;
  if (data.student_id != null) return;
  if (declaration.name === 'class_sentence_shown' || declaration.name === 'class_sentence_hidden') {
    showClassSentence(data.payload?.sentence); return;
  }
  if (declaration.name === "session_closed") {
    finishLiveSession("Sessão terminada. A aguardar a próxima aula.");
    return;
  }
  if (!declaration.bridge_name) return;
  const message = {
    pagecraft: 1,
    type: declaration.bridge_name,
  };
  if (Object.hasOwn(data.payload || {}, "unit_id")) {
    message.unitId = data.payload.unit_id;
  }
  board.contentWindow?.postMessage(message, "*");
}

function stopLiveSession() {
  clearTimer(sessionTimer);
  sessionTimer = null;
  if (stream) stream.close();
  stream = null;
  currentSessionId = null;
  board.removeAttribute("src");
  board.hidden = false;
  document.getElementById("group-codes-panel").hidden = true;
  document.getElementById("group-codes-grid").replaceChildren();
  sessionTitle.textContent = "";
  sessionJoinCode.textContent = "";
  sessionEntryUrl.textContent = "";
  sessionStatus.textContent = "";
}

(async () => {
  try {
    const response = await fetch('/api/access-info');
    if (response.ok) publicOrigin = (await response.json()).public_origin || location.origin;
  } catch { /* A origem local continua disponível. */ }
  checkSession();
})();
