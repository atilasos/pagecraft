/* Aula ao vivo: lançar sessão com catálogo classificado, régua da aula,
   cadernetas de alunos com detalhe, chamar a atenção e congelar ecrãs. */

const $ = (id) => document.getElementById(id);
const students = new Map(); // id → {name, joined, attempts, correct, discoveries, help, lastText, currentUnit, events[]}
let session = null;
let units = [];
let activities = [];
let pickerState = { search: "", year: null, subject: null, selected: null };
let messageTarget = null; // null = turma
let highlightTarget = null; // null = todos
let drawerStudent = null;
let frozen = false;

const EVENT_TEXT = {
  joined: () => "entrou na aula",
  activity_loaded: () => "abriu a atividade",
  heartbeat: () => "",
  unit_started: (e) => `começou ${unitLabel(e.payload?.unit_id || e.unit_id)}`,
  attempt: (e) => (e.payload.correct ? "acertou uma tentativa ✓" : "fez uma tentativa"),
  discovery: (e) => `descobriu: ${e.payload.message || ""}`,
  assessment_result: (e) => `avaliação: ${e.payload.result || ""}`,
  feedback_request: (e) => `pediu feedback: «${(e.payload.answer || "").slice(0, 60)}»`,
  help_needed: () => "pediu ajuda 🙋",
  share_requested: (e) => `quer partilhar: ${e.payload.what || ""}`,
  ai_feedback: (e) => `assistente respondeu: «${(e.payload.text || "").slice(0, 80)}»`,
  feedback_timeout: () => "feedback IA demorou — vê a resposta manualmente",
  feedback_dropped: () => "pedidos de feedback a mais — um foi ignorado",
  pit_updated: (e) => `plano: ${e.payload.text} → ${e.payload.status}`,
  teacher_message: (e) => `mensagem enviada: ${e.payload.text}`,
  teacher_highlight: (e) => `atenção chamada para ${e.payload.unit_label || e.payload.unit_id || "a atividade"}`,
  identity_released: () => "identidade libertada pelo professor",
  freeze_screens: () => "ecrãs congelados: olhem para o quadro",
  unfreeze_screens: () => "ecrãs libertados",
  session_closed: () => "sessão terminada",
};

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
  $("launch-class").innerHTML = classes
    .map((c) => `<option value="${esc(c.id)}">${esc(c.name)}</option>`)
    .join("");
}

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
  const data = await (await fetch("/api/activities")).json();
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
  const token = await teacherToken();
  $("export-link").href = `/api/sessions/${s.id}?teacher_token=${encodeURIComponent(token)}`;
  $("export-link").download = `sessao-${s.id}.json`;

  students.clear();
  Object.entries(s.roster).forEach(([id, e]) => {
    students.set(id, {
      name: e.display_name, joined: false, attempts: 0, correct: 0,
      discoveries: 0, help: false, lastText: "ainda não entrou",
      currentUnit: null, events: [],
    });
  });
  renderPulse();
  renderStudents();
  loadUnits(s.activity_slug);

  const es = new EventSource(await teacherStreamUrl(`/api/sessions/${s.id}/stream`));
  es.onmessage = () => {};
  Object.keys(EVENT_TEXT).forEach((type) => {
    es.addEventListener(type, (ev) => handleEvent(type, JSON.parse(ev.data), es));
  });
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
    ? `de ${students.get(studentId)?.name || "?"}`
    : "de todos";
}

$("freeze-btn").addEventListener("click", async () => {
  if (!session) return;
  const action = frozen ? "unfreeze" : "freeze";
  await tfetch(`/api/sessions/${session.id}/control`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ action }),
  });
  // o estado visual confirma-se pelo evento SSE (freeze_screens/unfreeze_screens)
});

function reflectFreeze(state) {
  frozen = state;
  $("freeze-btn").setAttribute("aria-pressed", String(state));
  $("freeze-label").textContent = state ? "Libertar os ecrãs" : "Olhem para o quadro";
}

/* ---------- eventos ---------- */

function handleEvent(type, record, es) {
  const st = record.student_id ? students.get(record.student_id) : null;
  const text = (EVENT_TEXT[type] || (() => type))(record);
  if (st) {
    st.events.push(record);
    if (st.events.length > 300) st.events.shift();
    if (text) st.lastText = text;
    if (type === "joined" || type === "activity_loaded" || type === "heartbeat") st.joined = true;
    if (type === "unit_started") st.currentUnit = record.unit_id || record.payload?.unit_id;
    if (type === "attempt") {
      st.attempts += 1;
      if (record.payload.correct) st.correct += 1;
    }
    if (type === "discovery") st.discoveries += 1;
    if (type === "help_needed" || type === "feedback_timeout") st.help = true;
    if (type === "attempt" || type === "discovery" || type === "ai_feedback") st.help = false;
    if (type === "identity_released") {
      // outro dispositivo pode reclamar esta identidade: não herdar histórico
      st.joined = false;
      st.help = false;
      st.currentUnit = null;
      st.attempts = 0;
      st.correct = 0;
      st.discoveries = 0;
      st.events = [];
      if (messageTarget === record.student_id) {
        messageTarget = null;
        $("msg-target").textContent = "para a turma";
      }
      if (highlightTarget === record.student_id) setHighlightTarget(null);
      if (drawerStudent === record.student_id) {
        $("drawer").classList.remove("open");
        drawerStudent = null;
      }
    }
    blip(record.student_id, type);
  }
  if (type === "freeze_screens") reflectFreeze(true);
  if (type === "unfreeze_screens") reflectFreeze(false);
  if (type !== "heartbeat" && text) {
    const li = document.createElement("li");
    const t = document.createElement("span");
    t.className = "t";
    t.textContent = new Date(record.ts).toLocaleTimeString("pt-PT", { hour: "2-digit", minute: "2-digit" });
    const body = document.createElement("span");
    body.textContent = `${st ? st.name + " · " : ""}${text}`;
    li.append(t, body);
    $("timeline").prepend(li);
  }
  renderStudents();
  renderPulse();
  if (drawerStudent && record.student_id === drawerStudent) fillDrawer(drawerStudent);
  if (type === "session_closed") {
    reflectFreeze(false);
    es.close();
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
  el.innerHTML = "";
  students.forEach((st, id) => {
    const dot = document.createElement("span");
    dot.className = "dot" + (st.help ? " help" : st.joined ? " on" : "");
    dot.id = `dot-${id}`;
    dot.title = st.name;
    el.appendChild(dot);
  });
}

function renderStudents() {
  const grid = $("students");
  grid.innerHTML = "";
  students.forEach((st, id) => {
    const card = document.createElement("button");
    card.type = "button";
    card.className =
      "student-card" + (st.help ? " help" : "") + (st.joined ? " on" : " away");
    card.id = `student-${id}`;
    card.innerHTML = `
      <h3><span class="presence" aria-hidden="true"></span>${esc(st.name)}</h3>
      <div class="counts">
        <span class="pill ok">${st.correct}✓</span>
        <span class="pill">${st.attempts} tent.</span>
        <span class="pill ok">${st.discoveries} desc.</span>
      </div>
      <p class="last"></p>`;
    card.querySelector(".last").textContent = st.currentUnit
      ? `${unitLabel(st.currentUnit)} · ${st.lastText}`
      : st.lastText;
    card.addEventListener("click", () => openDrawer(id));
    grid.appendChild(card);
  });
}

/* ---------- drawer do aluno ---------- */

function openDrawer(studentId) {
  drawerStudent = studentId;
  fillDrawer(studentId);
  $("drawer").classList.add("open");
}

function fillDrawer(studentId) {
  const st = students.get(studentId);
  if (!st) return;
  $("drawer-name").textContent = st.name;
  $("drawer-now").textContent = st.joined
    ? st.currentUnit
      ? `Agora em ${unitLabel(st.currentUnit)}`
      : "Na atividade"
    : "Ainda não entrou";
  $("drawer-counts").innerHTML = `
    <span class="pill ok">${st.correct} certas</span>
    <span class="pill">${st.attempts} tentativas</span>
    <span class="pill ok">${st.discoveries} descobertas</span>
    ${st.help ? '<span class="pill warn">precisa de ajuda</span>' : ""}`;
  const list = $("drawer-events");
  list.innerHTML = "";
  [...st.events].reverse().slice(0, 40).forEach((record) => {
    const text = (EVENT_TEXT[record.type] || (() => record.type))(record);
    if (!text) return;
    const li = document.createElement("li");
    const when = new Date(record.ts).toLocaleTimeString("pt-PT", { hour: "2-digit", minute: "2-digit" });
    li.textContent = `${when} · ${text}`;
    list.appendChild(li);
  });
  if (!list.children.length) list.innerHTML = '<li class="muted">ainda sem atividade</li>';
}

$("drawer-close").addEventListener("click", () => {
  drawerStudent = null;
  $("drawer").classList.remove("open");
});
$("drawer-msg").addEventListener("click", () => {
  const st = students.get(drawerStudent);
  messageTarget = drawerStudent;
  $("msg-target").textContent = st ? `para ${st.name}` : "para a turma";
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
  await tfetch(`/api/sessions/${session.id}/release/${drawerStudent}`, { method: "POST" });
  $("drawer").classList.remove("open");
  drawerStudent = null;
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
