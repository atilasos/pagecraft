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
    broto: "Broto · Apoio",
    young: "Árvore jovem",
    robust: "Árvore robusta",
    reflect: "Autoavaliar e terminar",
    yourvoice: "A tua reflexão",
    reflection: "O que descobriste?",
    optional:
      "Podes deixar perguntas por responder. O teu trabalho fica guardado.",
    back: "Voltar à atividade",
    finish: "Guardar e terminar",
    saved: "Guardado",
    thanks: "Obrigado por partilhares!",
    teacherSees:
      "O teu professor pode agora ler o teu trabalho e a tua reflexão.",
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
    unavailable:
      "Não foi possível abrir a atividade. Confirma o endereço ou tenta novamente.",
    newAttempt:
      "Tens trabalho por guardar. Tenta guardar antes de trocar de aluno.",
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
    broto: "Sprout",
    young: "Young tree",
    robust: "Strong tree",
    reflect: "Reflect and finish",
    yourvoice: "Your reflection",
    reflection: "What did you discover?",
    optional: "You can leave questions unanswered. Your work will be saved.",
    back: "Back to the activity",
    finish: "Save and finish",
    saved: "Saved",
    thanks: "Thank you for sharing!",
    teacherSees: "Your teacher can now read your work and reflection.",
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
    unavailable:
      "We could not open this activity. Check the address or try again.",
    newAttempt:
      "Some work still needs saving. Try saving before changing pupil.",
    readUnavailable: "Reading aloud is not available on this device.",
    preview: "Preview: these records are not included in pupil reports.",
  },
};
let lang = "pt",
  activity,
  attempt,
  queue = [],
  flushing = null,
  reflectionDraft = { answers: {}, strategy: "", next_step: "" };
const code = location.pathname.split("/").filter(Boolean).pop().toUpperCase();
const t = (key) => copy[lang][key];
function status(message, error = false) {
  $("status").textContent = message;
  $("status").classList.toggle("error", error);
}
async function api(path, method = "GET", data) {
  const r = await fetch(path, {
    method,
    headers: data ? { "Content-Type": "application/json" } : {},
    body: data ? JSON.stringify(data) : undefined,
  });
  if (!r.ok)
    throw new Error(
      lang === "en"
        ? "Could not save. Please try again."
        : (await r.json().catch(() => ({}))).detail ||
          "Não foi possível guardar. Tenta novamente.",
    );
  return r.status === 204 ? null : r.json();
}
function persist() {
  if (!attempt) return;
  try {
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
  if (attempt)
    $("lesson").contentWindow?.postMessage(
      {
        pagecraft: 1,
        type: "learning_preferences",
        payload: { language: lang, level: $("level").value },
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
function record(type, payload = {}, unitId = "") {
  if (!attempt || attempt.completed_at) return;
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
      await api("/api/learning/me/events", "POST", { events: batch });
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
  for (const id of ["entry", "reflection", "done"]) $(id).hidden = true;
  $("work").hidden = false;
  $("leave").hidden = false;
  $("lesson").src = `/api/learning/activities/${code}/content`;
  $("level").value = attempt.level;
  $("language").value = lang;
  translate();
}
function renderReflection() {
  const level = $("level").value,
    young = activity.year <= 2;
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
  $("scaffold").textContent = p[0];
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
      label.append(input, document.createTextNode(t(value)));
      fs.append(label);
    }
    $("criteria").append(fs);
  }
  $("strategy").value = reflectionDraft.strategy;
  $("next-step").value = reflectionDraft.next_step;
}
function openReflection() {
  if (!attempt || attempt.completed_at) return;
  $("work").hidden = true;
  $("reflection").hidden = false;
  renderReflection();
  $("reflection").scrollIntoView({ behavior: "smooth" });
}
function showDone() {
  for (const id of ["entry", "work", "reflection"]) $(id).hidden = true;
  $("done").hidden = false;
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
  captureReflection();
  $("reflection").hidden = true;
  $("work").hidden = false;
};
$("finish-form").oninput = captureReflection;
$("finish-form").onsubmit = async (e) => {
  e.preventDefault();
  captureReflection();
  e.submitter.disabled = true;
  try {
    status(t("saving"));
    await flush();
    attempt = await api("/api/learning/me/finish", "POST", {
      ...reflectionDraft,
      language: lang,
      level: $("level").value,
    });
    sessionStorage.removeItem("pc-queue:" + attempt.id);
    sessionStorage.removeItem("pc-reflection:" + attempt.id);
    showDone();
  } catch (e) {
    status(e.message, true);
  } finally {
    e.submitter.disabled = false;
  }
};
async function leave() {
  try {
    await flush();
    await api("/api/learning/me/leave", "POST");
    if (attempt) {
      sessionStorage.removeItem("pc-queue:" + attempt.id);
      sessionStorage.removeItem("pc-reflection:" + attempt.id);
    }
    location.reload();
  } catch {
    status(t("newAttempt"), true);
  }
}
$("leave").onclick = leave;
$("again").onclick = leave;
window.addEventListener("message", (e) => {
  if (e.source !== $("lesson").contentWindow || e.data?.pagecraft !== 1) return;
  const { type, payload = {}, unitId = "" } = e.data;
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
    "activity_loaded",
    "unit_started",
    "attempt",
    "discovery",
    "assessment_result",
    "help_needed",
    "share_requested",
    "language_changed",
    "level_changed",
  ];
  if (allowed.includes(type) && JSON.stringify(payload).length <= 4096)
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
(async () => {
  try {
    activity = await api(`/api/learning/activities/${code}`);
    $("title").textContent = activity.title;
    document.title = activity.title + " · PageCraft";
    $("group").value = activity.group || "";
    $("language-label").hidden = !activity.languages.includes("en");
    $("draft").hidden = activity.published;
    try {
      const previous = await api("/api/learning/me");
      if (previous.code === code) {
        attempt = previous;
        lang = previous.language;
        queue = JSON.parse(
          sessionStorage.getItem("pc-queue:" + attempt.id) || "[]",
        );
        reflectionDraft =
          JSON.parse(
            sessionStorage.getItem("pc-reflection:" + attempt.id) || "null",
          ) || reflectionDraft;
        showWork();
        if (attempt.completed_at) showDone();
        else flush().catch(() => {});
      }
    } catch {}
    translate();
  } catch {
    status(t("unavailable"), true);
    $("start-form").hidden = true;
  }
})();
