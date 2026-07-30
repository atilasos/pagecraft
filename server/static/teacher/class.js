/* Aula ao vivo: lançar sessão com catálogo classificado, régua da aula,
   cadernetas de alunos com detalhe, chamar a atenção e congelar ecrãs. */

const $ = (id) => document.getElementById(id);
const students = new Map(); // id → projeção viva emitida pelo servidor
let session = null;
let liveSessionState = { status: "live", closed: false, frozen: false };
let units = [];
let activities = [];
let pickerState = { search: "", year: null, subject: null, selected: null };
let messageTarget = null; // null = turma
let highlightTarget = null; // null = todos
let drawerStudent = null;

const EVENT_TEXT = {
  joined: () => "entrou na aula",
  activity_loaded: () => "abriu a atividade",
  heartbeat: () => "",
  unit_started: (e) => `começou ${unitLabel(e.payload?.unit_id || e.unit_id)}`,
  attempt: (e) => (e.payload?.correct ? "acertou uma tentativa ✓" : "fez uma tentativa"),
  discovery: (e) => `descobriu: ${e.payload?.message || ""}`,
  assessment_result: (e) => `avaliação: ${e.payload?.result || ""}`,
  feedback_request: (e) => `pediu feedback: «${(e.payload?.answer || "").slice(0, 60)}»`,
  help_needed: () => "pediu ajuda 🙋",
  share_requested: (e) => `quer partilhar: ${e.payload?.what || ""}`,
  ai_feedback: (e) => `assistente respondeu: «${(e.payload?.text || "").slice(0, 80)}»`,
  feedback_timeout: () => "feedback IA demorou — vê a resposta manualmente",
  feedback_dropped: () => "pedidos de feedback a mais — um foi ignorado",
  feedback_error: (e) => `erro no feedback IA: ${e.payload?.error || "falha sem detalhe"}`,
  pit_updated: (e) => `plano: ${e.payload?.text || ""} → ${e.payload?.status || ""}`,
  teacher_message: (e) => `mensagem enviada: ${e.payload?.text || ""}`,
  teacher_highlight: (e) => `atenção chamada para ${e.payload?.unit_label || e.payload?.unit_id || "a atividade"}`,
  identity_released: () => "identidade libertada pelo professor",
  freeze_screens: () => "ecrãs congelados: olhem para o quadro",
  unfreeze_screens: () => "ecrãs libertados",
  session_closed: () => "sessão terminada",
};

const TRIAGE_BANDS = [
  { name: "Sem sinal", listId: "band-no-signal", countId: "band-no-signal-count" },
  { name: "Precisa de ti", listId: "band-needs-you", countId: "band-needs-you-count" },
  { name: "A tropeçar", listId: "band-stumbling", countId: "band-stumbling-count" },
  { name: "A fluir", listId: "band-flowing", countId: "band-flowing-count" },
];

function readableEventType(type) {
  return type.replace(/_/g, " ");
}

function eventText(type, record) {
  return (EVENT_TEXT[type] || (() => readableEventType(type)))(record);
}

function unitLabel(unitId) {
  const u = units.find((u) => u.id === unitId);
  return u ? `«${u.summary}»` : unitId || "uma unidade";
}

/* ---------- turmas ---------- */

async function loadClasses() {
  const resp = await tfetch("/api/classes");
  if (!resp.ok) return;
  const classes = await resp.json();
  $("classes-list").innerHTML = classes.length
    ? `<ul class="plain">${classes
        .map((c) => `<li><strong>${esc(c.name)}</strong> <span class="muted">· ${esc(c.year)}.º ano · ${c.students.length} alunos</span></li>`)
        .join("")}</ul>`
    : "Ainda não há turmas — cria a primeira em baixo.";
  const options = classes
    .map((c) => `<option value="${esc(c.id)}">${esc(c.name)}</option>`)
    .join("");
  $("launch-class").innerHTML = options;
  $("report-class").innerHTML = options;
}

/* ---------- relatório para avaliação cooperada ---------- */

$("report-btn").addEventListener("click", async () => {
  const classId = $("report-class").value;
  if (!classId) return;
  const params = new URLSearchParams();
  if ($("report-from").value) params.set("from", $("report-from").value);
  if ($("report-to").value) params.set("to", $("report-to").value);
  const resp = await tfetch(`/api/classes/${classId}/report?${params}`);
  const out = $("report-out");
  if (!resp.ok) {
    out.innerHTML = '<p class="feedback-warn">Não foi possível gerar o registo.</p>';
    return;
  }
  const report = await resp.json();
  params.set("format", "md");
  const mdLink = $("report-md");
  mdLink.href = `/api/classes/${classId}/report?${params}`;
  mdLink.download = `registo-${report.class_name}.md`;
  mdLink.hidden = false;

  const head = `
    <tr><th>Aluno</th><th>Aulas</th><th>Tent.</th><th>Certas</th><th>Desc.</th>
    <th>Ajuda</th><th>Feedback</th><th>Partilhas</th><th>PIT</th></tr>`;
  const rows = report.students
    .map(
      (s) => `<tr><td>${esc(s.display_name)}</td><td>${s.sessions}</td><td>${s.attempt}</td>
        <td>${s.correct}</td><td>${s.discovery}</td><td>${s.help_needed}</td>
        <td>${s.feedback_request}</td><td>${s.share_requested}</td>
        <td>${s.pit_done}/${s.pit_total}</td></tr>`
    )
    .join("");
  const sessions = report.sessions.length
    ? `<p class="muted" style="margin-top:0.75rem">${report.sessions.length} sessões no período.</p>`
    : '<p class="muted" style="margin-top:0.75rem">Sem sessões no período escolhido.</p>';
  out.innerHTML = `<div class="card" style="margin-top:0.75rem; overflow-x:auto">
    <table>${head}${rows}</table>${sessions}</div>`;
});

$("class-form").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  await tfetch("/api/classes", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      name: $("class-name").value,
      year: Number($("class-year").value),
      students: $("class-students").value.split("\n"),
    }),
  });
  $("class-form").reset();
  loadClasses();
});

/* ---------- picker de atividades ---------- */

async function loadActivities() {
  const data = await (await tfetch("/api/activities")).json();
  activities = data.items || [];
  renderFilterChips("picker-years", data.years, "year", (y) => `${y}.º ano`);
  renderFilterChips("picker-subjects", data.subjects, "subject", (s) => s);
  renderPicker();
}

function renderFilterChips(elId, values, key, labelFn) {
  const el = $(elId);
  el.innerHTML = "";
  values.forEach((value) => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "chip";
    chip.textContent = labelFn(value);
    chip.setAttribute("aria-pressed", "false");
    chip.addEventListener("click", () => {
      pickerState[key] = pickerState[key] === value ? null : value;
      el.querySelectorAll(".chip").forEach((c) => c.setAttribute("aria-pressed", "false"));
      if (pickerState[key] === value) chip.setAttribute("aria-pressed", "true");
      renderPicker();
    });
    el.appendChild(chip);
  });
}

$("picker-search").addEventListener("input", (ev) => {
  pickerState.search = ev.target.value.trim().toLowerCase();
  renderPicker();
});

function renderPicker() {
  const list = $("picker-list");
  list.innerHTML = "";
  const matches = activities.filter((a) => {
    if (pickerState.year && a.year !== pickerState.year) return false;
    if (pickerState.subject && a.subject !== pickerState.subject) return false;
    if (pickerState.search) {
      const hay = `${a.title} ${a.subject} ${(a.tags || []).join(" ")}`.toLowerCase();
      if (!hay.includes(pickerState.search)) return false;
    }
    return true;
  });
  // seleção escondida pelos filtros deixa de ser lançável
  if (pickerState.selected && !matches.some((a) => a.slug === pickerState.selected.slug)) {
    pickerState.selected = null;
    $("launch-btn").disabled = true;
    $("launch-hint").textContent = "Escolhe uma atividade ao lado.";
  }
  if (!matches.length) {
    list.innerHTML = '<p class="muted">Nenhuma atividade corresponde aos filtros.</p>';
    return;
  }
  matches.forEach((a) => {
    const opt = document.createElement("button");
    opt.type = "button";
    opt.className = "activity-option";
    opt.setAttribute("aria-pressed", String(pickerState.selected?.slug === a.slug));
    const title = document.createElement("strong");
    title.textContent = a.title || a.slug;
    const meta = document.createElement("span");
    meta.className = "meta";
    meta.innerHTML =
      (a.subject ? `<span class="pill subject">${esc(a.subject)}</span>` : "") +
      (a.year ? `<span class="pill">${esc(a.year)}.º ano</span>` : "") +
      (a.duration ? `<span class="pill">${esc(a.duration)} min</span>` : "");
    opt.append(title, meta);
    opt.addEventListener("click", () => {
      pickerState.selected = a;
      $("launch-btn").disabled = false;
      $("launch-hint").textContent = `Selecionada: ${a.title || a.slug}`;
      renderPicker();
    });
    list.appendChild(opt);
  });
}

$("launch-btn").addEventListener("click", async () => {
  const a = pickerState.selected;
  if (!a) return;
  const resp = await tfetch("/api/sessions", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      class_id: $("launch-class").value,
      activity_slug: a.slug,
      activity_title: a.title || a.slug,
    }),
  });
  if (resp.ok) startLive(await resp.json());
});

/* ---------- sessão ao vivo ---------- */

async function startLive(s) {
  session = s;
  $("prep-desk").hidden = true;
  $("live").hidden = false;
  $("ruler").hidden = false;
  $("live-title").textContent = `${s.class_name} · ${s.activity_title}`;
  $("live-url").textContent = `${location.host}/student/`;
  $("live-code").innerHTML = "";
  [...s.join_code].forEach((ch) => {
    const b = document.createElement("span");
    b.textContent = ch;
    $("live-code").appendChild(b);
  });
  $("present-link").href = `/teacher/present.html?session=${encodeURIComponent(s.id)}`;
  $("export-link").href = `/api/sessions/${s.id}`;
  $("export-link").download = `sessao-${s.id}.json`;

  students.clear();
  renderPulse();
  renderStudents();
  loadUnits(s.activity_slug);

  const eventTypes = await loadPanelEventTypes();
  const es = await teacherEventSource(
    `/api/sessions/${s.id}/stream?role=teacher`
  );
  es.onmessage = () => {};
  addJsonListener(es, "session_state_snapshot", (data) => applySnapshot(data, es));
  addJsonListener(es, "student_state_changed", applyStudentState);
  addJsonListener(es, "session_state_changed", (data) => applySessionState(data, es));
  eventTypes.forEach((type) => {
    addJsonListener(es, type, (data) => handleEvent(type, { ...data, type }));
  });
}

function addJsonListener(es, type, listener) {
  es.addEventListener(type, (ev) => {
    try {
      const data = JSON.parse(ev.data);
      if (!data || typeof data !== "object" || Array.isArray(data)) return;
      listener(data);
    } catch (error) {
      // Um frame incompreensível não pode interromper os seguintes.
    }
  });
}

function applySnapshot(snapshot, es) {
  if (!snapshot.students || typeof snapshot.students !== "object" || Array.isArray(snapshot.students)) return;
  students.clear();
  Object.entries(snapshot.students).forEach(([studentId, student]) => {
    if (student && typeof student === "object" && !Array.isArray(student)) {
      students.set(studentId, student);
    }
  });
  renderStudents();
  renderPulse();
  applySessionState(snapshot, es);
  if (drawerStudent) fillDrawer(drawerStudent);
}

function applyStudentState(delta) {
  if (
    typeof delta.student_id !== "string" ||
    !delta.student ||
    typeof delta.student !== "object" ||
    Array.isArray(delta.student)
  ) return;
  const previousBand = triageBand(students.get(delta.student_id)).name;
  students.set(delta.student_id, delta.student);
  placeStudentCard(delta.student_id);
  updateBandCount(previousBand);
  updateBandCount(triageBand(delta.student).name);
  updatePulseStudent(delta.student_id);
  if (drawerStudent === delta.student_id) fillDrawer(delta.student_id);
}

function applySessionState(delta, es) {
  const next = delta.session;
  if (!next || typeof next !== "object" || Array.isArray(next)) return;
  liveSessionState = { ...next };
  reflectFreeze(next.frozen === true);
  if (next.closed === true) es.close();
}

async function loadPanelEventTypes() {
  try {
    const resp = await tfetch("/api/session-event-types");
    if (!resp.ok) return fallbackPanelEventTypes();
    const declaration = await resp.json();
    if (!Array.isArray(declaration?.types)) return fallbackPanelEventTypes();
    const declaredTypes = [
      ...new Set(
        declaration.types
          .filter(
            (entry) =>
              entry &&
              typeof entry.name === "string" &&
              /^[a-z][a-z0-9_]*$/.test(entry.name) &&
              entry.timeline === true
          )
          .map((entry) => entry.name)
      ),
    ];
    return declaredTypes.length ? declaredTypes : fallbackPanelEventTypes();
  } catch (error) {
    return fallbackPanelEventTypes();
  }
}

function fallbackPanelEventTypes() {
  return Object.keys(EVENT_TEXT).filter((type) => type !== "heartbeat");
}

async function loadUnits(slug) {
  units = [];
  const list = $("units-list");
  try {
    const resp = await fetch(`/api/activities/${encodeURIComponent(slug)}/units`);
    if (resp.ok) units = (await resp.json()).units || [];
  } catch (e) { /* atividades antigas podem não ter docspec */ }
  list.innerHTML = "";
  if (!units.length) {
    list.innerHTML = '<li class="muted">Esta atividade não expõe a sua estrutura — o aviso «olha para…» chega na mesma ao aluno.</li>';
    const li = document.createElement("li");
    const btn = document.createElement("button");
    btn.className = "ghost";
    btn.textContent = "Chamar a atenção para a atividade";
    btn.addEventListener("click", () => sendHighlight(null, "a atividade"));
    li.appendChild(btn);
    list.appendChild(li);
    return;
  }
  units.forEach((u, i) => {
    const li = document.createElement("li");
    const btn = document.createElement("button");
    btn.className = "ghost";
    btn.style.width = "100%";
    btn.style.textAlign = "left";
    btn.textContent = `${i + 1}. ${u.summary}`;
    btn.addEventListener("click", () => sendHighlight(u.id, u.summary));
    li.appendChild(btn);
    list.appendChild(li);
  });
}

async function sendHighlight(unitId, label) {
  if (!session) return;
  const resp = await tfetch(`/api/sessions/${session.id}/control`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      action: "highlight",
      unit_id: unitId,
      unit_label: label,
      student_id: highlightTarget,
    }),
  });
  if (resp.ok) setHighlightTarget(null); // depois de chamar, volta a "todos"
}

function setHighlightTarget(studentId) {
  highlightTarget = studentId;
  $("highlight-target-label").textContent = studentId
    ? `de ${students.get(studentId)?.display_name || "?"}`
    : "de todos";
}

$("freeze-btn").addEventListener("click", async () => {
  if (!session) return;
  const action = liveSessionState.frozen ? "unfreeze" : "freeze";
  await tfetch(`/api/sessions/${session.id}/control`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ action }),
  });
  // o estado visual confirma-se pelo evento SSE (freeze_screens/unfreeze_screens)
});

function reflectFreeze(state) {
  $("freeze-btn").setAttribute("aria-pressed", String(state));
  $("freeze-label").textContent = state ? "Libertar os ecrãs" : "Olhem para o quadro";
}

/* ---------- eventos ---------- */

function handleEvent(type, record) {
  const st = record.student_id ? students.get(record.student_id) : null;
  const text = eventText(type, record);
  if (st) blip(record.student_id, type);
  if (text) {
    const li = document.createElement("li");
    const t = document.createElement("span");
    t.className = "t";
    t.textContent = new Date(record.ts).toLocaleTimeString("pt-PT", { hour: "2-digit", minute: "2-digit" });
    const body = document.createElement("span");
    body.textContent = `${st ? st.display_name + " · " : ""}${text}`;
    li.append(t, body);
    $("timeline").prepend(li);
  }
  if (type === "identity_released") {
    if (messageTarget === record.student_id) {
      messageTarget = null;
      $("msg-target").textContent = "para a turma";
    }
    if (highlightTarget === record.student_id) setHighlightTarget(null);
  }
}

function blip(studentId, type) {
  if (type === "heartbeat") return;
  requestAnimationFrame(() => {
    const card = document.getElementById(`student-${studentId}`);
    if (card) {
      card.classList.remove("blip");
      void card.offsetWidth;
      card.classList.add("blip");
    }
    const dot = document.getElementById(`dot-${studentId}`);
    if (dot) {
      dot.classList.remove("blip");
      void dot.offsetWidth;
      dot.classList.add("blip");
    }
  });
}

/* ---------- render ---------- */

function renderPulse() {
  const el = $("class-pulse");
  el.querySelectorAll(".dot").forEach((dot) => {
    if (!students.has(dot.dataset.studentId)) dot.remove();
  });
  students.forEach((st, id) => {
    updatePulseStudent(id);
  });
}

function updatePulseStudent(studentId) {
  const st = students.get(studentId);
  if (!st) return;
  let dot = document.getElementById(`dot-${studentId}`);
  if (!dot) {
    dot = document.createElement("span");
    dot.id = `dot-${studentId}`;
    dot.dataset.studentId = studentId;
    $("class-pulse").appendChild(dot);
  }
  dot.className =
    "dot" +
    (st.triage?.explicit_help
      ? " help"
      : st.participated && st.triage?.band !== "Sem sinal"
        ? " on"
        : "");
  dot.title = st.display_name || studentId;
}

function triageBand(student) {
  return (
    TRIAGE_BANDS.find((band) => band.name === student?.triage?.band) ||
    TRIAGE_BANDS[TRIAGE_BANDS.length - 1]
  );
}

function waitSeconds(student) {
  const value = Number(student?.triage?.wait_seconds);
  return Number.isFinite(value) ? Math.max(0, Math.floor(value)) : 0;
}

function compareStudents([leftId, left], [rightId, right]) {
  return (
    waitSeconds(right) - waitSeconds(left) ||
    String(left.display_name || leftId).localeCompare(
      String(right.display_name || rightId),
      "pt-PT"
    )
  );
}

function studentsInBand(bandName) {
  return [...students.entries()]
    .filter(([, student]) => triageBand(student).name === bandName)
    .sort(compareStudents);
}

function formatWait(seconds) {
  const total = Math.max(0, Math.floor(Number(seconds) || 0));
  if (total < 60) return `${total} s`;
  const minutes = Math.floor(total / 60);
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  const remainder = minutes % 60;
  return remainder ? `${hours} h ${remainder} min` : `${hours} h`;
}

function createStudentCard(studentId) {
    const card = document.createElement("button");
    card.type = "button";
    card.id = `student-${studentId}`;
    card.dataset.studentId = studentId;
    card.innerHTML = `
      <h3><span class="presence" aria-hidden="true"></span><span class="student-name"></span></h3>
      <div class="counts">
        <span class="pill ok correct-count"></span>
        <span class="pill attempt-count"></span>
        <span class="pill ok discovery-count"></span>
        <span class="pill warn help-badge" hidden>🙋 Pediu ajuda</span>
      </div>
      <p class="last"></p>`;
    card.addEventListener("click", () => openDrawer(studentId));
    return card;
}

function updateStudentCard(studentId) {
  const st = students.get(studentId);
  if (!st) return null;
  const numbers = st.numbers || {};
  const evidence = numbers.evidence || {};
  let card = document.getElementById(`student-${studentId}`);
  if (!card) card = createStudentCard(studentId);
  card.className =
    "student-card" +
    (st.triage?.explicit_help ? " help" : "") +
    (st.participated && st.triage?.band !== "Sem sinal" ? " on" : " away");
  card.querySelector(".student-name").textContent = st.display_name || studentId;
  card.querySelector(".correct-count").textContent = `${numbers.correct_attempts || 0}✓`;
  card.querySelector(".attempt-count").textContent = `${evidence.attempt || 0} tent.`;
  card.querySelector(".discovery-count").textContent = `${evidence.discovery || 0} desc.`;
  card.querySelector(".help-badge").hidden = st.triage?.explicit_help !== true;
  card.querySelector(".last").textContent =
    `${st.triage?.reason || "Sem estado"} · espera ${formatWait(st.triage?.wait_seconds)}`;
  return card;
}

function placeStudentCard(studentId) {
  const st = students.get(studentId);
  if (!st) return;
  const band = triageBand(st);
  const list = $(band.listId);
  const ordered = studentsInBand(band.name);
  const index = ordered.findIndex(([id]) => id === studentId);
  const nextId = ordered[index + 1]?.[0];
  const nextCard = nextId ? document.getElementById(`student-${nextId}`) : null;
  const card = updateStudentCard(studentId);
  const hadFocus = document.activeElement === card;
  if (card.parentElement !== list || card.nextElementSibling !== nextCard) {
    list.insertBefore(card, nextCard);
  }
  if (hadFocus && document.activeElement !== card) card.focus();
}

function updateBandCount(bandName) {
  const band = TRIAGE_BANDS.find((candidate) => candidate.name === bandName);
  if (!band) return;
  $(band.countId).textContent = studentsInBand(band.name).length;
}

function renderStudents() {
  document.querySelectorAll(".student-card[data-student-id]").forEach((card) => {
    if (!students.has(card.dataset.studentId)) card.remove();
  });
  students.forEach((student, studentId) => updateStudentCard(studentId));
  TRIAGE_BANDS.forEach((band) => {
    const list = $(band.listId);
    let cursor = list.firstElementChild;
    studentsInBand(band.name).forEach(([studentId]) => {
      const card = document.getElementById(`student-${studentId}`);
      if (card === cursor) {
        cursor = cursor.nextElementSibling;
      } else {
        list.insertBefore(card, cursor);
      }
    });
    updateBandCount(band.name);
  });
}

/* ---------- drawer do aluno ---------- */

function openDrawer(studentId) {
  drawerStudent = studentId;
  fillDrawer(studentId);
  $("drawer-keep").checked = true;
  $("drawer-events").innerHTML = '<li class="muted">a carregar percurso…</li>';
  $("drawer").classList.add("open");
  loadDrawerHistory(studentId);
}

function fillDrawer(studentId) {
  const st = students.get(studentId);
  if (!st) return;
  const numbers = st.numbers || {};
  const evidence = numbers.evidence || {};
  $("drawer-name").textContent = st.display_name || studentId;
  $("drawer-now").textContent =
    `${st.triage?.band || "Sem estado"} · ${st.triage?.reason || ""}`;
  $("drawer-counts").innerHTML = `
    <span class="pill ok">${numbers.correct_attempts || 0} certas</span>
    <span class="pill">${evidence.attempt || 0} tentativas</span>
    <span class="pill ok">${evidence.discovery || 0} descobertas</span>
    ${st.triage?.explicit_help ? '<span class="pill warn">pediu ajuda</span>' : ""}`;
}

async function loadDrawerHistory(studentId) {
  const list = $("drawer-events");
  try {
    const resp = await tfetch(
      `/api/sessions/${encodeURIComponent(session.id)}/students/${encodeURIComponent(studentId)}/history?role=teacher`
    );
    if (drawerStudent !== studentId) return;
    if (!resp.ok) {
      list.innerHTML = '<li class="muted">não foi possível carregar o percurso</li>';
      return;
    }
    const data = await resp.json();
    if (!Array.isArray(data?.events)) {
      list.innerHTML = '<li class="muted">percurso incompreensível</li>';
      return;
    }
    renderDrawerHistory(data.events);
  } catch (error) {
    if (drawerStudent === studentId) {
      list.innerHTML = '<li class="muted">não foi possível carregar o percurso</li>';
    }
  }
}

function renderDrawerHistory(events) {
  const list = $("drawer-events");
  list.innerHTML = "";
  [...events].reverse().forEach((record) => {
    if (!record || typeof record !== "object" || typeof record.type !== "string") return;
    const text = eventText(record.type, record);
    if (!text) return;
    const li = document.createElement("li");
    const when = new Date(record.ts).toLocaleTimeString("pt-PT", {
      hour: "2-digit",
      minute: "2-digit",
    });
    li.textContent = `${when} · ${text}`;
    list.appendChild(li);
  });
  if (!list.children.length) {
    list.innerHTML = '<li class="muted">ainda sem atividade</li>';
  }
}

$("drawer-close").addEventListener("click", () => {
  drawerStudent = null;
  $("drawer").classList.remove("open");
});
$("drawer-msg").addEventListener("click", () => {
  const st = students.get(drawerStudent);
  messageTarget = drawerStudent;
  $("msg-target").textContent = st ? `para ${st.display_name}` : "para a turma";
  $("drawer").classList.remove("open");
  drawerStudent = null;
  $("msg-text").focus();
});
$("drawer-highlight").addEventListener("click", () => {
  setHighlightTarget(drawerStudent);
  $("drawer").classList.remove("open");
  drawerStudent = null;
});
$("drawer-release").addEventListener("click", async () => {
  if (!session || !drawerStudent) return;
  const studentId = drawerStudent;
  const resp = await tfetch(`/api/sessions/${session.id}/release/${studentId}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ reset_progress: $("drawer-reset").checked }),
  });
  if (resp.ok && drawerStudent === studentId) {
    $("drawer").classList.remove("open");
    drawerStudent = null;
  }
});

/* ---------- mensagens / fecho ---------- */

$("msg-btn").addEventListener("click", async () => {
  const text = $("msg-text").value.trim();
  if (!text || !session) return;
  await tfetch(`/api/sessions/${session.id}/message`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ text, student_id: messageTarget }),
  });
  $("msg-text").value = "";
  messageTarget = null;
  $("msg-target").textContent = "para a turma";
});

$("close-btn").addEventListener("click", async () => {
  if (!session) return;
  await tfetch(`/api/sessions/${session.id}/close`, { method: "POST" });
  location.reload(); // estado limpo: régua fora, bancada de lançamento de volta
});

/* ---------- arranque ---------- */

(async function init() {
  await Promise.all([loadClasses(), loadActivities()]);
  const resp = await tfetch("/api/sessions");
  if (!resp.ok) return;
  const sessions = await resp.json();
  const live = sessions.find((s) => s.status === "live");
  if (live) startLive(live);
})();
