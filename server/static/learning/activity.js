"use strict";
const $ = (id) => document.getElementById(id);
const copy = {
  pt: {
    language: "Língua",
    leave: "Trocar de aluno",
    welcome: "Uma atividade para explorar, criar e partilhar.",
    name: "Como te chamas?",
    group: "Turma (se souberes)",
    where: "Onde vais trabalhar?",
    classroom: "Na aula",
    home: "Em casa",
    start: "Começar",
    support: "Apoio",
    supportLevel: "Com pistas",
    intermediateLevel: "Passo a passo",
    challengeLevel: "Mais desafios",
    reflect: "Autoavaliar e terminar",
    yourvoice: "A tua reflexão",
    reflection: "O que descobriste?",
    reflectionOf: "Reflexão de",
    optional:
      "Podes deixar perguntas por responder. O teu trabalho fica guardado.",
    back: "Voltar à atividade",
    finish: "Guardar e terminar",
    saved: "Guardado",
    thanks: "Obrigado por partilhares!",
    teacherSees:
      "O teu professor pode agora ler o teu trabalho e a tua reflexão.",
    teacherSeesPreview:
      "Esta foi uma pré-visualização. O ensaio ficou guardado, mas não entra nos relatórios dos alunos.",
    again: "Começar uma nova realização",
    alone: "Consegui com autonomia",
    help: "Consegui com ajuda",
    practising: "Quero praticar mais",
    skip: "Prefiro não responder",
    listen: "Ouvir",
    pending:
      "Há trabalho por guardar. Mantém esta página aberta; voltaremos a tentar.",
    synced: "Trabalho guardado.",
    saving: "A guardar…",
    recovering: "A recuperar o teu trabalho…",
    recoveryUnavailable:
      "Não foi possível recuperar o teu trabalho. Tenta novamente antes de começar.",
    retryRecovery: "Tentar recuperar novamente",
    recoveryExpired:
      "O acesso a esta realização terminou. Não há trabalho pendente neste separador. Podes começar uma nova realização.",
    unavailable:
      "Não foi possível abrir a atividade. Confirma o endereço ou tenta novamente.",
    newAttempt:
      "Tens trabalho por guardar. Tenta guardar antes de trocar de aluno.",
    identityConflict:
      "Foi aberta outra realização neste browser. O trabalho deste separador continua por guardar. Mantém esta página aberta e pede ajuda ao professor.",
    readUnavailable: "Este dispositivo não tem leitura em voz alta disponível.",
    preview:
      "Pré-visualização: estes registos não entram nos relatórios dos alunos.",
  },
  en: {
    language: "Language",
    leave: "Change pupil",
    welcome: "An activity to explore, create and share.",
    name: "What is your name?",
    group: "Class (if you know it)",
    where: "Where will you work?",
    classroom: "At school",
    home: "At home",
    start: "Start",
    support: "Support",
    supportLevel: "With hints",
    intermediateLevel: "Step by step",
    challengeLevel: "More challenges",
    reflect: "Reflect and finish",
    yourvoice: "Your reflection",
    reflection: "What did you discover?",
    reflectionOf: "Reflection by",
    optional: "You can leave questions unanswered. Your work will be saved.",
    back: "Back to the activity",
    finish: "Save and finish",
    saved: "Saved",
    thanks: "Thank you for sharing!",
    teacherSees: "Your teacher can now read your work and reflection.",
    teacherSeesPreview:
      "This was a preview. The trial was saved, but it will not appear in pupil reports.",
    again: "Start a new attempt",
    alone: "I managed on my own",
    help: "I managed with help",
    practising: "I want more practice",
    skip: "I prefer not to answer",
    listen: "Listen",
    pending:
      "Some work still needs saving. Keep this page open; we will try again.",
    synced: "Work saved.",
    saving: "Saving…",
    recovering: "Recovering your work…",
    recoveryUnavailable:
      "We could not recover your work. Please try again before starting.",
    retryRecovery: "Try recovering again",
    recoveryExpired:
      "Access to this attempt has expired. There is no pending work in this tab. You can start a new attempt.",
    unavailable:
      "We could not open this activity. Check the address or try again.",
    newAttempt:
      "Some work still needs saving. Try saving before changing pupil.",
    identityConflict:
      "Another attempt was opened in this browser. This tab's work still needs saving. Keep this page open and ask your teacher for help.",
    readUnavailable: "Reading aloud is not available on this device.",
    preview: "Preview: these records are not included in pupil reports.",
  },
};
let reflectionReady = true;
let reflectionAudio = null;
let requiresCompletion = false;
let lessonLoaded = false;
let lang = "pt",
  activity,
  attempt,
  expiredIdentity,
  identityConflict = false,
  queue = [],
  flushing = null,
  reflectionDraft = { answers: {}, strategy: "", next_step: "" };
const code = location.pathname.split("/").filter(Boolean).pop().toUpperCase();
const t = (key) => copy[lang][key];
function status(message, error = false) {
  if (identityConflict) {
    message = t("identityConflict");
    error = true;
  }
  $("status").textContent = message;
  $("status").classList.toggle("error", error);
}
async function api(path, method = "GET", data, expectedId) {
  const headers = data ? { "Content-Type": "application/json" } : {};
  if (expectedId) headers["X-PageCraft-Realization"] = expectedId;
  const r = await fetch(path, {
    method,
    headers,
    body: data ? JSON.stringify(data) : undefined,
  });
  if (!r.ok) {
    const detail = (await r.json().catch(() => ({}))).detail;
    if (detail?.code === "realization_conflict") {
      identityConflict = true;
      status(t("identityConflict"), true);
    }
    const error = new Error(
      identityConflict ? t("identityConflict") : lang === "en"
        ? "Could not save. Please try again."
        : (typeof detail === "string" ? detail : detail?.message) ||
          "Não foi possível guardar. Tenta novamente.",
    );
    error.status = r.status;
    error.identityConflict = identityConflict;
    throw error;
  }
  return r.status === 204 ? null : r.json();
}
function persist() {
  if (!attempt) return;
  try {
    sessionStorage.setItem("pc-realization:" + code, attempt.id);
    sessionStorage.setItem("pc-queue:" + attempt.id, JSON.stringify(queue));
    sessionStorage.setItem(
      "pc-reflection:" + attempt.id,
      JSON.stringify(reflectionDraft),
    );
  } catch {
    status(t("pending"), true);
  }
}
function captureReflection() {
  if (!$("reflection").hidden) {
    reflectionDraft = {
      answers: {},
      strategy: $("strategy").value,
      next_step: $("next-step").value,
    };
    document
      .querySelectorAll("#criteria input:checked")
      .forEach((input) => (reflectionDraft.answers[input.name] = input.value));
    persist();
  }
}
function sendPreferences() {
  if (attempt && lessonLoaded)
    $("lesson").contentWindow?.postMessage(
      {
        pagecraft: 1,
        type: "learning_preferences",
        payload: { language: lang, level: $("level").value, participant_count: 1, route: "permanent" },
      },
      "*",
    );
}
function translate() {
  document.documentElement.lang = lang === "pt" ? "pt-PT" : "en";
  if (activity)
    document.title =
      (lang === "en" && activity.title_en
        ? activity.title_en
        : activity.title) + " · PageCraft";
  document
    .querySelectorAll("[data-i18n]")
    .forEach((el) => (el.textContent = t(el.dataset.i18n)));
  if (activity) {
    $("title").textContent =
      lang === "en" && activity.title_en ? activity.title_en : activity.title;
  }
  if (activity)
    $("metadata").textContent =
      lang === "pt"
        ? `${activity.year}.º ano · ${activity.duration} minutos`
        : `Year ${activity.year} · ${activity.duration} minutes`;
  if (attempt)
    $("greeting").textContent =
      (lang === "pt" ? "Olá, " : "Hello, ") + attempt.name + ".";
  if (!$("reflection").hidden) renderReflection();
  sendPreferences();
}
function applyPendingPreference({ type, payload = {} }) {
  if (type === "level_changed" && ["support", "intermediate", "challenge"].includes(payload.level)) {
    attempt.level = payload.level;
  }
  if (type === "language_changed" && activity.languages.includes(payload.language)) {
    attempt.language = payload.language;
    lang = payload.language;
  }
}
function record(type, payload = {}, unitId = "") {
  if (!attempt || attempt.completed_at) return;
  applyPendingPreference({ type, payload });
  queue.push({ id: crypto.randomUUID(), type, payload, unitId });
  persist();
  flush().catch(() => {});
}
async function flush() {
  if (flushing) return flushing;
  if (!queue.length || !attempt) return;
  flushing = (async () => {
    while (queue.length) {
      const batch = queue.slice(0, 100);
      await api("/api/learning/me/events", "POST", { events: batch }, attempt.id);
      attempt.events.push(...batch);
      queue.splice(0, batch.length);
      persist();
    }
    status(attempt.preview ? t("preview") : t("synced"));
  })();
  try {
    await flushing;
  } catch (e) {
    status(t("pending"), true);
    throw e;
  } finally {
    flushing = null;
  }
}
function showWork() {
  requiresCompletion = activity.requires_completion === true;
  reflectionReady = !requiresCompletion;
  $("reflect").disabled = !reflectionReady;
  for (const id of ["entry", "reflection", "done"]) $(id).hidden = true;
  $("work").hidden = false;
  $("leave").hidden = false;
  lessonLoaded = false;
  // New drafts can defer input until restore and preferences are consumed.
  // Older activities ignore the fragment and keep their existing behavior.
  $("lesson").src = `/api/learning/activities/${code}/content#learning`;
  $("level").value = attempt.level;
  $("language").value = lang;
  translate();
}
function renderReflection() {
  reflectionAudio?.pause();
  $("reflection-pupil").textContent = `${t("reflectionOf")} ${attempt.name}.`;
  const level = $("level").value,
    young = activity.year <= 2;
  const visual = activity.group === "m28p-v3";
  $("reflection").classList.toggle("visual-reflection", visual);
  $("reflection").querySelector("h1").textContent = visual ? "Como foi o jogo?" : t("reflection");
  $("strategy").closest("label").hidden = visual;
  $("next-step").closest("label").hidden = visual;
  const prompts =
    lang === "pt"
      ? {
          support: [
            young
              ? "Pensa no que fizeste. Podes ouvir cada pergunta."
              : "Escolhe uma resposta para cada objetivo. Podes ouvir as perguntas.",
            "O que te ajudou? Podes escrever uma palavra.",
            "O que queres experimentar a seguir?",
          ],
          intermediate: [
            "Pensa no teu trabalho e na ajuda que recebeste.",
            "Que estratégia te ajudou?",
            "Qual será o teu próximo passo?",
          ],
          challenge: [
            "Usa um exemplo do teu trabalho para explicar a tua reflexão.",
            "Que estratégia usaste e porque resultou?",
            "O que vais melhorar e como saberás que conseguiste?",
          ],
        }
      : {
          support: [
            young
              ? "Think about what you did. You can listen to each question."
              : "Choose an answer for each goal. You can listen to the questions.",
            "What helped you? You can write one word.",
            "What would you like to try next?",
          ],
          intermediate: [
            "Think about your work and the help you received.",
            "Which strategy helped you?",
            "What will your next step be?",
          ],
          challenge: [
            "Use an example from your work to explain your reflection.",
            "Which strategy did you use and why did it work?",
            "What will you improve and how will you know you managed it?",
          ],
        };
  const p = prompts[level];
  $("scaffold").textContent = visual ? "Podes escolher ou passar." : p[0];
  $("strategy-label").textContent = p[1];
  $("next-label").textContent = p[2];
  $("criteria").replaceChildren();
  for (const c of activity.criteria) {
    const fs = document.createElement("fieldset"),
      legend = document.createElement("legend");
    legend.textContent = c[lang] || c.pt;
    fs.append(legend);
    const listen = document.createElement("button");
    listen.type = "button";
    listen.textContent = t("listen");
    listen.onclick = () => {
      if (visual) {
        reflectionAudio?.pause();
        reflectionAudio = new Audio("/learning-assets/m28p-reflection.mp3");
        reflectionAudio.play().catch(() => status("Podes escolher ou passar."));
        return;
      }
      if (!("speechSynthesis" in window)) {
        status(t("readUnavailable"), true);
        return;
      }
      const u = new SpeechSynthesisUtterance(legend.textContent);
      u.lang = lang === "pt" ? "pt-PT" : "en-GB";
      speechSynthesis.cancel();
      speechSynthesis.speak(u);
    };
    fs.append(listen);
    for (const value of ["alone", "help", "practising", "skip"]) {
      const label = document.createElement("label"),
        input = document.createElement("input");
      input.type = "radio";
      input.name = c.id;
      input.value = value;
      input.checked = (reflectionDraft.answers[c.id] || "skip") === value;
      if (visual) {
        const icon = document.createElement("span");
        icon.className = "reflection-icon";
        icon.setAttribute("aria-hidden", "true");
        icon.textContent = {alone: "✓", help: "☞", practising: "↻", skip: "→"}[value];
        label.append(input, icon, document.createTextNode({alone: "Sozinho", help: "Com ajuda", practising: "Praticar", skip: "Passar"}[value]));
      } else label.append(input, document.createTextNode(t(value)));
      fs.append(label);
    }
    $("criteria").append(fs);
  }
  $("strategy").value = reflectionDraft.strategy;
  $("next-step").value = reflectionDraft.next_step;
}
function openReflection() {
  if (!reflectionReady || !attempt || attempt.completed_at) return;
  $("work").hidden = true;
  $("reflection").hidden = false;
  renderReflection();
  $("reflection").scrollIntoView({ behavior: "smooth" });
  const heading = $("reflection").querySelector("h1");
  heading.tabIndex = -1;
  heading.focus({ preventScroll: true });
}
function showDone() {
  for (const id of ["entry", "work", "reflection"]) $(id).hidden = true;
  $("done").hidden = false;
  const teacherMessage = $("done-teacher-sees");
  teacherMessage.dataset.i18n = attempt.preview
    ? "teacherSeesPreview"
    : "teacherSees";
  teacherMessage.textContent = t(teacherMessage.dataset.i18n);
  $("done-next").textContent = attempt.assessment?.next_step || "";
  status(attempt.preview ? t("preview") : t("synced"));
}
$("start-form").onsubmit = async (e) => {
  e.preventDefault();
  const button = e.submitter;
  button.disabled = true;
  try {
    attempt = await api(`/api/learning/activities/${code}/start`, "POST", {
      name: $("name").value,
      group: $("group").value,
      mode: $("mode").value,
      language: lang,
      level: "intermediate",
    });
    queue = [];
    reflectionDraft = { answers: {}, strategy: "", next_step: "" };
    persist();
    showWork();
  } catch (e) {
    status(e.message, true);
  } finally {
    button.disabled = false;
  }
};
$("language").onchange = () => {
  captureReflection();
  lang = $("language").value;
  translate();
  record("language_changed", { language: lang });
};
$("level").onchange = () => {
  captureReflection();
  record("level_changed", { level: $("level").value });
  sendPreferences();
};
$("lesson").onload = () => {
  lessonLoaded = true;
  if (attempt)
    $("lesson").contentWindow.postMessage(
      {
        pagecraft: 1,
        type: "learning_restore",
        payload: { events: [...attempt.events, ...queue] },
      },
      "*",
    );
  sendPreferences();
};
$("reflect").onclick = openReflection;
$("back").onclick = () => {
  reflectionAudio?.pause();
  captureReflection();
  $("reflection").hidden = true;
  $("work").hidden = false;
};
$("finish-form").oninput = captureReflection;
$("finish-form").onsubmit = async (e) => {
  e.preventDefault();
  reflectionAudio?.pause();
  if (!reflectionReady || !attempt || attempt.completed_at) return;
  captureReflection();
  e.submitter.disabled = true;
  try {
    status(t("saving"));
    await flush();
    attempt = await api("/api/learning/me/finish", "POST", {
      ...reflectionDraft,
      language: lang,
      level: $("level").value,
    }, attempt.id);
    sessionStorage.removeItem("pc-queue:" + attempt.id);
    sessionStorage.removeItem("pc-reflection:" + attempt.id);
    showDone();
  } catch (e) {
    status(e.message, true);
  } finally {
    e.submitter.disabled = false;
  }
};
function emptyReflection(draft) {
  return draft && typeof draft === "object" && !Array.isArray(draft) &&
    Object.keys(draft).every((key) => ["answers", "strategy", "next_step"].includes(key)) &&
    draft.answers && typeof draft.answers === "object" && !Array.isArray(draft.answers) &&
    Object.keys(draft.answers).length === 0 && draft.strategy === "" && draft.next_step === "";
}
function noPendingWork(id) {
  try {
    if (queue.length || (attempt && !attempt.completed_at && !emptyReflection(reflectionDraft))) return false;
    const storedQueue = sessionStorage.getItem("pc-queue:" + id);
    const pending = storedQueue === null ? [] : JSON.parse(storedQueue);
    const storedReflection = sessionStorage.getItem("pc-reflection:" + id);
    return Array.isArray(pending) && pending.length === 0 &&
      (storedReflection === null || emptyReflection(JSON.parse(storedReflection)));
  } catch {
    // Unreadable or malformed storage is not proof that no work is pending.
    return false;
  }
}
function startLocally(id) {
  if (identityConflict || !id || !noPendingWork(id)) return false;
  try {
    if (sessionStorage.getItem("pc-realization:" + code) !== id) return false;
    // This explicit choice only forgets this tab's reference. It never clears
    // a shared cookie, nor removes drafts belonging to any realization.
    sessionStorage.removeItem("pc-realization:" + code);
  } catch {
    return false;
  }
  attempt = null;
  expiredIdentity = null;
  queue = [];
  reflectionDraft = { answers: {}, strategy: "", next_step: "" };
  for (const id of ["work", "reflection", "done", "leave", "recovery-retry", "recovery-new"]) $(id).hidden = true;
  $("lesson").src = "about:blank";
  $("entry").hidden = false;
  $("start-form").hidden = false;
  $("name").value = "";
  status("");
  return true;
}
async function leave() {
  try {
    await flush();
    await api("/api/learning/me/leave", "POST", undefined, attempt.id);
    if (attempt) {
      sessionStorage.removeItem("pc-queue:" + attempt.id);
      sessionStorage.removeItem("pc-reflection:" + attempt.id);
      sessionStorage.removeItem("pc-realization:" + code);
    }
    location.reload();
  } catch (error) {
    // The pupil already chose to start anew. A 401 permits a local exit only
    // when every source of pending work can be checked; 409 never permits it.
    if (error.status === 401 && startLocally(attempt?.id)) return;
    status(t("newAttempt"), true);
  }
}
$("leave").onclick = leave;
$("again").onclick = leave;
async function requestFeedback(payload, unitId) {
  if (!attempt || attempt.completed_at || !payload.request_id) return;
  const owner = attempt.id;
  let result;
  try {
    await flush();
    result = await api("/api/learning/me/feedback", "POST", {
      unit_id: unitId, request_id: payload.request_id, context: payload,
    }, owner);
  } catch (error) {
    // A conflict must not turn into an apparently delivered hint for this work.
    if (error.identityConflict) return;
    result = {request_id: payload.request_id, unit_id: unitId, source: "unavailable",
      text: "Não consegui dar uma pista agora. Usa as pistas do guião ou pede ajuda ao professor."};
  }
  if (attempt?.id === owner && !attempt.completed_at)
    $("lesson").contentWindow?.postMessage({pagecraft: 1, type: "ai_feedback", payload: result}, "*");
}
window.addEventListener("message", (e) => {
  if (e.source !== $("lesson").contentWindow || e.data?.pagecraft !== 1) return;
  const { type, payload = {}, unitId = "" } = e.data;
  if (type === "support_modal") return;
  if (type === "activity_state" && requiresCompletion) {
    reflectionReady = payload.readyForReflection === true;
    $("reflect").disabled = !reflectionReady;
    if (!reflectionReady && !$("reflection").hidden) {
      captureReflection();
      $("reflection").hidden = true;
      $("work").hidden = false;
    }
  }
  if (type === "feedback_request") {
    requestFeedback(payload, unitId);
    return;
  }
  if (type === "open_reflection") {
    openReflection();
    return;
  }
  if (
    type === "language_changed" &&
    activity.languages.includes(payload.language)
  ) {
    captureReflection();
    lang = payload.language;
    $("language").value = lang;
    translate();
  }
  if (
    type === "level_changed" &&
    ["support", "intermediate", "challenge"].includes(payload.level)
  )
    $("level").value = payload.level;
  const allowed = [
    "hint_presented", "hint_feedback", "hint_acknowledged", "hint_listened", "work_location", "help_resolved",
    "activity_loaded",
    "activity_state",
    "unit_started",
    "attempt",
    "discovery",
    "assessment_result",
    "help_needed",
    "share_requested",
    "language_changed",
    "level_changed",
  ];
  const limit = ["hint_presented", "help_needed"].includes(type) ? 12000 : 4096;
  if (allowed.includes(type) && JSON.stringify(payload).length <= limit)
    record(type, payload, String(unitId || "").slice(0, 80));
});
window.addEventListener("online", () => flush().catch(() => {}));
window.addEventListener("beforeunload", (e) => {
  if (queue.length) {
    e.preventDefault();
    e.returnValue = "";
  }
});
setInterval(() => flush().catch(() => {}), 5000);
async function recoverAttempt() {
  $("start-form").hidden = true;
  $("recovery-retry").hidden = true;
  $("recovery-new").hidden = true;
  expiredIdentity = null;
  status(t("recovering"));
  let expectedId;
  try {
    expectedId = sessionStorage.getItem("pc-realization:" + code);
    const previous = await api("/api/learning/me", "GET", undefined, expectedId);
    if (previous.code === code) {
      identityConflict = false;
      attempt = previous;
      lang = previous.language;
      queue = JSON.parse(
        sessionStorage.getItem("pc-queue:" + attempt.id) || "[]",
      );
      // Pending choices are newer than the server snapshot used for restore.
      queue.forEach(applyPendingPreference);
      reflectionDraft =
        JSON.parse(
          sessionStorage.getItem("pc-reflection:" + attempt.id) || "null",
        ) || reflectionDraft;
      persist();
      status("");
      showWork();
      if (attempt.completed_at) showDone();
      else flush().catch(() => {});
    } else {
      $("start-form").hidden = false;
      status("");
    }
  } catch (error) {
    // Known tabs need an explicit choice to forget their reference. Pending
    // or uncertain data must remain recoverable, even after credentials expire.
    if (error.status === 401 && !expectedId) {
      $("start-form").hidden = false;
      status("");
    } else {
      const canStartNew = error.status === 401 && expectedId && !identityConflict && noPendingWork(expectedId);
      if (canStartNew) expiredIdentity = expectedId;
      status(t(canStartNew ? "recoveryExpired" : "recoveryUnavailable"), true);
      $("recovery-retry").hidden = false;
      $("recovery-new").hidden = !canStartNew;
    }
  }
}
$("recovery-retry").onclick = recoverAttempt;
$("recovery-new").onclick = () => {
  if (!startLocally(expiredIdentity)) {
    $("recovery-new").hidden = true;
    status(t("recoveryUnavailable"), true);
  }
};
(async () => {
  try {
    activity = await api(`/api/learning/activities/${code}`);
    document.body.dataset.year = String(activity.year);
    $("title").textContent = activity.title;
    document.title = activity.title + " · PageCraft";
    $("group").value = activity.group || "";
    $("language-label").hidden = !activity.languages.includes("en");
    $("draft").hidden = activity.published;
    await recoverAttempt();
    translate();
  } catch {
    status(t("unavailable"), true);
    $("start-form").hidden = true;
  }
})();
