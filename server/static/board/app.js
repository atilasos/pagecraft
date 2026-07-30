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
  board.removeAttribute("src");
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

function startLiveSession(session) {
  clearTimer(sessionTimer);
  show(live);
  sessionTitle.textContent = `${session.class_name} · ${session.activity_title}`;
  sessionStatus.textContent = "Aula em curso";

  const activityUrl = `/activities/${encodeURIComponent(session.activity_slug)}/`;
  if (board.getAttribute("src") !== activityUrl) board.src = activityUrl;
  if (currentSessionId === session.id && stream) return;

  stopLiveSession();
  currentSessionId = session.id;
  stream = new EventSource(`/api/sessions/${session.id}/stream`);
  stream.addEventListener("session_state_snapshot", (event) => {
    applySessionState(event.data);
  });
  stream.addEventListener("session_state_changed", (event) => {
    applySessionState(event.data);
  });
  ["teacher_highlight", "freeze_screens", "unfreeze_screens", "session_closed"].forEach(
    (type) => {
      stream.addEventListener(type, (event) => {
        dispatchCollectiveEvent(type, event.data);
      });
    }
  );
  stream.addEventListener("error", () => {
    stopLiveSession();
    show(waiting);
    waitingStatus.textContent = "A recuperar a ligação à aula…";
    sessionTimer = later(checkSession, 1000);
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

function applySessionState(rawData) {
  const data = parseObject(rawData);
  const state = data?.session;
  if (!state || typeof state !== "object" || Array.isArray(state)) return;
  if (state.closed === true || state.status === "closed") {
    stopLiveSession();
    board.removeAttribute("src");
    show(waiting);
    waitingStatus.textContent = "Sessão terminada. A aguardar a próxima aula.";
    sessionTimer = later(checkSession, 1500);
  }
}

function dispatchCollectiveEvent(type, rawData) {
  const data = parseObject(rawData);
  if (!data) return;
  if (data.student_id != null) return;
  if (type === "session_closed") {
    stopLiveSession();
    board.removeAttribute("src");
    show(waiting);
    waitingStatus.textContent = "Sessão terminada. A aguardar a próxima aula.";
    sessionTimer = later(checkSession, 1500);
    return;
  }
  if (type === "teacher_highlight") {
    board.contentWindow?.postMessage(
      {
        pagecraft: 1,
        type: "highlight",
        unitId: data.payload?.unit_id,
      },
      "*"
    );
  }
}

function stopLiveSession() {
  if (stream) stream.close();
  stream = null;
  currentSessionId = null;
}

checkSession();
