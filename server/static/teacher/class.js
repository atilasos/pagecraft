/* Dashboard do professor: turmas, lançamento de sessão e acompanhamento vivo. */

const $ = (id) => document.getElementById(id);
const students = new Map(); // student_id → {name, joined, attempts, correct, discoveries, help, lastText, pit}
let session = null;

const EVENT_TEXT = {
  joined: (e) => `entrou na aula`,
  activity_loaded: () => `abriu a atividade`,
  unit_started: (e) => `começou a unidade ${e.unit_id || ""}`,
  attempt: (e) => (e.payload.correct ? "acertou uma tentativa" : "fez uma tentativa"),
  discovery: (e) => `descobriu: ${e.payload.message || ""}`,
  assessment_result: (e) => `avaliação: ${e.payload.result || ""}`,
  feedback_request: (e) => `pediu feedback: «${(e.payload.answer || "").slice(0, 60)}»`,
  help_needed: () => `pediu ajuda 🙋`,
  share_requested: (e) => `quer partilhar: ${e.payload.what || ""}`,
  ai_feedback: (e) => `assistente respondeu (${e.payload.source}): «${(e.payload.text || "").slice(0, 80)}»`,
  feedback_timeout: () => `feedback IA demorou — vê a resposta manualmente`,
  pit_updated: (e) => `plano: ${e.payload.text} → ${e.payload.status}`,
  teacher_message: (e) => `mensagem enviada: ${e.payload.text}`,
  session_closed: () => `sessão terminada`,
};

async function loadClasses() {
  const classes = await (await fetch("/api/classes")).json();
  $("classes-list").innerHTML = classes.length
    ? `<ul class="plain">${classes
        .map((c) => `<li><strong>${c.name}</strong> <span class="muted">· ${c.year}.º ano · ${c.students.length} alunos</span></li>`)
        .join("")}</ul>`
    : '<p class="muted">Ainda não há turmas.</p>';
  $("launch-class").innerHTML = classes
    .map((c) => `<option value="${c.id}">${c.name}</option>`)
    .join("");
}

async function loadActivities() {
  const meta = await (await fetch("/api/meta")).json();
  $("launch-activity").innerHTML = (meta.activities || [])
    .slice()
    .reverse()
    .map((a) => `<option value="${a.slug}">${a.title || a.slug}</option>`)
    .join("");
}

$("class-form").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  await fetch("/api/classes", {
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

$("launch-btn").addEventListener("click", async () => {
  const select = $("launch-activity");
  const resp = await fetch("/api/sessions", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      class_id: $("launch-class").value,
      activity_slug: select.value,
      activity_title: select.options[select.selectedIndex]?.text || select.value,
    }),
  });
  if (!resp.ok) return;
  startLive(await resp.json());
});

function startLive(s) {
  session = s;
  $("live").hidden = false;
  $("live-title").textContent = `${s.class_name} · ${s.activity_title}`;
  $("live-code").textContent = s.join_code;
  $("live-url").textContent = `${location.origin}/student/`;
  $("export-link").href = `/api/sessions/${s.id}`;
  $("export-link").download = `sessao-${s.id}.json`;
  students.clear();
  Object.entries(s.roster).forEach(([id, e]) => {
    students.set(id, {
      name: e.display_name, joined: false, attempts: 0, correct: 0,
      discoveries: 0, help: false, lastText: "ainda não entrou", pit: [],
    });
  });
  renderStudents();
  const es = new EventSource(`/api/sessions/${s.id}/stream`);
  es.onmessage = () => {};
  Object.keys(EVENT_TEXT).forEach((type) => {
    es.addEventListener(type, (ev) => handleEvent(type, JSON.parse(ev.data), es));
  });
}

function handleEvent(type, record, es) {
  const st = record.student_id ? students.get(record.student_id) : null;
  const text = (EVENT_TEXT[type] || (() => type))(record);
  if (st) {
    st.lastText = text;
    if (type === "joined" || type === "activity_loaded") st.joined = true;
    if (type === "attempt") {
      st.attempts += 1;
      if (record.payload.correct) st.correct += 1;
    }
    if (type === "discovery") st.discoveries += 1;
    if (type === "help_needed" || type === "feedback_timeout") st.help = true;
    if (type === "attempt" || type === "discovery" || type === "ai_feedback") st.help = false;
  }
  if (type !== "heartbeat") {
    const li = document.createElement("li");
    const when = new Date(record.ts).toLocaleTimeString("pt-PT", { hour: "2-digit", minute: "2-digit" });
    li.textContent = `${when} · ${st ? st.name : "—"} · ${text}`;
    $("timeline").prepend(li);
  }
  renderStudents();
  if (type === "session_closed") es.close();
}

function renderStudents() {
  const grid = $("students");
  grid.innerHTML = "";
  students.forEach((st, id) => {
    const card = document.createElement("div");
    card.className = "student-card" + (st.help ? " help" : "");
    card.innerHTML = `
      <h3>${st.name} ${st.joined ? "" : '<span class="muted">(fora)</span>'}</h3>
      <div class="counts">
        <span class="pill ok">${st.correct}✓</span>
        <span class="pill">${st.attempts} tentativas</span>
        <span class="pill ok">${st.discoveries} descobertas</span>
      </div>
      <p class="last">${st.lastText}</p>`;
    const actions = document.createElement("p");
    const msgBtn = document.createElement("button");
    msgBtn.className = "ghost";
    msgBtn.textContent = "mensagem";
    msgBtn.addEventListener("click", () => sendMessage(id, st.name));
    const freeBtn = document.createElement("button");
    freeBtn.className = "ghost";
    freeBtn.textContent = "libertar";
    freeBtn.title = "libertar identidade (se o aluno trocou de dispositivo)";
    freeBtn.addEventListener("click", async () => {
      await fetch(`/api/sessions/${session.id}/release/${id}`, { method: "POST" });
    });
    actions.append(msgBtn, document.createTextNode(" "), freeBtn);
    card.appendChild(actions);
    grid.appendChild(card);
  });
}

let messageTarget = null; // null = turma toda

function sendMessage(studentId, name) {
  messageTarget = studentId;
  $("msg-target").textContent = name ? `(para ${name})` : "(para a turma)";
  $("msg-text").focus();
}

$("msg-btn").addEventListener("click", async () => {
  const text = $("msg-text").value.trim();
  if (!text || !session) return;
  await fetch(`/api/sessions/${session.id}/message`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ text, student_id: messageTarget }),
  });
  $("msg-text").value = "";
  sendMessage(null, null);
});
$("close-btn").addEventListener("click", async () => {
  if (!session) return;
  await fetch(`/api/sessions/${session.id}/close`, { method: "POST" });
});

(async function init() {
  await Promise.all([loadClasses(), loadActivities()]);
  // retomar sessão live existente, se houver
  const sessions = await (await fetch("/api/sessions")).json();
  const live = sessions.find((s) => s.status === "live");
  if (live) startLive(live);
})();
