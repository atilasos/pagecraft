"use strict";
/* Acompanhar um roteiro: estado de cada aluno, quadro e registo da aula.
   Descreve o que foi registado; nunca classifica a criança. */
const $ = id => document.getElementById(id);
const code = (new URLSearchParams(location.search).get("aula") || "").toUpperCase();
const STATES = {
  working: ["A trabalhar", "state-working"],
  idle: ["Sem atividade recente no PageCraft", "state-idle"],
  finished: ["Terminou uma atividade", "state-finished"],
  not_started: ["Ainda não entrou", ""],
  unassigned: ["Sem atividades atribuídas", ""],
  offline: ["Fora do PageCraft", "state-offline"],
};
const ANSWERS = {alone: "com autonomia", help: "com ajuda", practising: "quer praticar", skip: "sem resposta"};
let data = null, rows = new Map(), timer = null, publicOrigin = location.origin;
// Observações: por aluno, o texto confirmado pelo servidor e a fila de gravações.
const notes = new Map(); // id -> {saved, queued, pending, chain}
let refreshRequest = 0; // só a consulta mais recente atualiza o painel e reagenda

function el(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}
function status(text, error = false) {
  $("status").textContent = text;
  $("status").classList.toggle("error", error);
}
async function api(path, method = "GET", body) {
  const response = await fetch(path, {method, headers: body ? {"Content-Type": "application/json"} : {}, body: body ? JSON.stringify(body) : undefined});
  if (response.status === 401) { location.href = "/login"; throw Error("É necessário entrar."); }
  if (response.status === 204) return null;
  const result = await response.json();
  if (!response.ok) throw Error(typeof result.detail === "string" ? result.detail : "Não foi possível concluir o pedido.");
  return result;
}
const titleOf = activityCode => data.activities[activityCode]?.title || activityCode;
const status_of = r => r.completed_at ? `terminada às ${time(r.completed_at)}` : r.finished ? "chegou ao fim do jogo, sem autoavaliação" : `em curso desde ${time(r.started_at)}`;
const plural = (n, one, many) => `${n} ${n === 1 ? one : many}`;
const time = iso => new Date(iso).toLocaleTimeString("pt-PT", {hour: "2-digit", minute: "2-digit"});

/* Respostas somadas de todas as autoavaliações; as contagens de atividades são distintas. */
function assessmentTotals(student) {
  const totals = {alone: 0, help: 0, practising: 0, skip: 0};
  for (const r of student.realizations)
    if (r.assessment) for (const key of Object.keys(totals)) totals[key] += r.assessment[key] || 0;
  const assessed = new Set(student.realizations.filter(r => r.assessment).map(r => r.code));
  const missing = new Set(student.realizations.filter(r => !assessed.has(r.code)).map(r => r.code));
  return {filled: assessed.size, missing: missing.size, totals};
}
/* Atividades distintas: repetir ou reabrir um jogo cria outra realização. */
function activityCounts(student) {
  const assigned = new Set(student.assigned);
  const finished = new Set(student.realizations.filter(r => r.finished && assigned.has(r.code)).map(r => r.code));
  const open = new Set(student.realizations.filter(r => !r.finished && assigned.has(r.code) && !finished.has(r.code)).map(r => r.code));
  return {finished: finished.size, open: open.size};
}
function evidenceTotals(student) {
  return student.realizations.reduce((sum, r) => ({
    correct: sum.correct + r.correct, different: sum.different + r.different, unscored: sum.unscored + r.unscored,
    help: sum.help + r.help,
  }), {correct: 0, different: 0, unscored: 0, help: 0});
}

function nowCell(student) {
  const cell = el("td");
  const [label, className] = STATES[student.state];
  cell.append(el("span", label, `state ${className}`));
  if (student.current) cell.append(el("p", student.current_title || titleOf(student.current)));
  if (student.state === "offline" && student.offline) cell.append(el("p", student.offline, "muted"));
  if (student.state === "finished") cell.append(el("p", "Pode escolher outra atividade do roteiro.", "muted"));
  if (student.help_pending) {
    const flag = el("p");
    flag.append(el("span", "Pediu ajuda", "state state-help"));
    cell.append(flag);
  }
  return cell;
}
function workCell(student) {
  const cell = el("td");
  if (student.state === "offline" || !student.assigned.length) { cell.append(el("span", "—", "muted")); return cell; }
  const {finished: done, open} = activityCounts(student);
  const parts = [plural(student.assigned.length, "atribuída", "atribuídas")];
  if (done) parts.push(plural(done, "terminada", "terminadas"));
  if (open) parts.push(`${open} em curso`);
  cell.append(el("p", parts.join(" · ")));
  if (student.words.length) cell.append(el("p", `Palavra: ${student.words.map(w => wordLabel(w)).join(", ")}`, "muted"));
  if (student.realizations.length) {
    const details = el("details"), list = el("ul");
    details.append(el("summary", "Ver atividades"));
    for (const r of student.realizations) {
      const item = el("li", `${r.title} — ${status_of(r)}`);
      if (r.strategy) item.append(el("p", `Estratégia: ${r.strategy}`, "muted"));
      if (r.next_step) item.append(el("p", `Próximo passo proposto: ${r.next_step}`, "muted"));
      list.append(item);
    }
    details.append(list);
    cell.append(details);
  }
  return cell;
}
function wordLabel(word) {
  const game = Object.values(data.activities).find(a => a.m28p?.word === word);
  return game?.m28p?.label || word;
}
function assessmentCell(student) {
  const cell = el("td");
  if (!student.realizations.length) { cell.append(el("span", "—", "muted")); return cell; }
  const {filled, missing, totals} = assessmentTotals(student);
  if (filled) {
    cell.append(el("p", `Preenchida em ${plural(filled, "atividade", "atividades")}`));
    const said = Object.entries(totals).filter(([, n]) => n).map(([key, n]) => `${n} ${ANSWERS[key]}`);
    if (said.length) cell.append(el("p", said.join(" · "), "muted"));
  }
  if (missing) cell.append(el("p", `Sem autoavaliação em ${plural(missing, "atividade", "atividades")}`, filled ? "muted" : ""));
  return cell;
}
function evidenceCell(student) {
  const cell = el("td");
  if (!student.realizations.length) { cell.append(el("span", "—", "muted")); return cell; }
  const t = evidenceTotals(student);
  cell.append(el("p", `${plural(t.correct, "resposta certa", "respostas certas")} · ${plural(t.different, "diferente da esperada", "diferentes da esperada")}`));
  if (t.unscored) cell.append(el("p", `${plural(t.unscored, "tentativa sem correção automática", "tentativas sem correção automática")} (ex.: descobertas)`, "muted"));
  if (t.help) cell.append(el("p", plural(t.help, "pedido de ajuda", "pedidos de ajuda"), "muted"));
  const last = student.realizations.map(r => r.last_at).sort().at(-1);
  cell.append(el("p", `Última ação às ${time(last)}`, "muted"));
  return cell;
}
function noteCell(student) {
  const cell = el("td"), area = el("textarea"), line = el("p", "", "note-status muted");
  area.value = student.note;
  area.maxLength = 2000;
  area.setAttribute("aria-label", `Observação sobre ${student.display_name}`);
  area.placeholder = "Ex.: leu sozinho as frases";
  line.setAttribute("role", "status");
  const state = notes.get(student.id) || {saved: student.note, queued: student.note, pending: 0, chain: Promise.resolve()};
  notes.set(student.id, state);
  // As gravações do mesmo aluno seguem em fila: a última escrita é a que fica.
  const save = () => {
    const text = area.value;
    if (text.trim() === state.queued.trim() && !state.pending) return Promise.resolve();
    if (text.trim() === state.queued.trim()) return state.chain;
    state.queued = text;
    state.pending++;
    line.textContent = "A guardar…";
    const request = state.chain.then(() =>
      api(`/api/learning/lessons/${code}/notes/${student.id}`, "PUT", {text})).then(() => {
      state.saved = text;
      if (state.queued === text) line.textContent = "Guardada.";
    }, error => {
      // Só a escrita mais recente decide o que falta guardar e a mensagem mostrada.
      if (state.queued === text) {
        state.queued = state.saved;
        line.textContent = `Não foi possível guardar: ${error.message}`;
      }
      throw error;
    }).finally(() => { state.pending--; });
    state.chain = request.catch(() => {});
    return request;
  };
  area.onblur = () => { save().catch(() => {}); };
  area.dataset.student = student.id;
  area.saveNote = save;
  cell.append(area, line);
  cell.dataset.note = "1";
  return cell;
}

function renderRows() {
  for (const student of data.students) {
    let row = rows.get(student.id);
    if (!row) {
      row = el("tr");
      const name = el("th", student.display_name);
      name.scope = "row";
      row.append(name, el("td"), el("td"), el("td"), el("td"), noteCell(student));
      rows.set(student.id, row);
      $("rows").append(row);
    }
    // A observação em edição nunca é substituída pela atualização periódica.
    const cells = [nowCell(student), workCell(student), assessmentCell(student), evidenceCell(student)];
    cells.forEach((cell, index) => {
      const old = row.children[index + 1];
      const open = old.querySelector("details")?.open;
      if (open) cell.querySelector("details")?.setAttribute("open", "");
      old.replaceWith(cell);
    });
  }
}
function renderCounts() {
  const counts = {};
  for (const student of data.students) counts[student.state] = (counts[student.state] || 0) + 1;
  const help = data.students.filter(s => s.help_pending).length;
  const items = Object.keys(STATES).filter(state => counts[state]).map(state => {
    const item = el("li");
    item.append(el("span", `${STATES[state][0]}: ${counts[state]}`, `state ${STATES[state][1]}`));
    return item;
  });
  if (help) {
    const item = el("li");
    item.append(el("span", `Pediram ajuda: ${help}`, "state state-help"));
    items.unshift(item);
  }
  $("counts").replaceChildren(...items);
}
function renderBoard() {
  const focus = data.board, elsewhere = data.board_elsewhere;
  $("board-now").textContent = focus ? `O quadro mostra: ${focus.activity_title}`
    : elsewhere?.kind === "session" ? `O quadro mostra a aula ao vivo «${elsewhere.title}». Escolhe uma atividade para voltar a este roteiro.`
    : elsewhere?.kind === "lesson" ? `O quadro mostra outro roteiro: «${elsewhere.title}».`
    : "O quadro não mostra nenhuma atividade deste roteiro.";
  // Só conta quem está a trabalhar agora numa atividade que ainda está no roteiro.
  const working = new Map();
  for (const student of data.students)
    if (student.state === "working" && data.activities[student.current]) working.set(student.current, (working.get(student.current) || 0) + 1);
  const buttons = [...working.entries()].sort((a, b) => b[1] - a[1] || titleOf(a[0]).localeCompare(titleOf(b[0]), "pt")).map(([activityCode, n]) => {
    const button = el("button", `${titleOf(activityCode)} · ${plural(n, "aluno", "alunos")}`);
    button.type = "button";
    button.setAttribute("aria-pressed", String(focus?.activity_code === activityCode));
    button.onclick = () => showOnBoard(activityCode);
    button.disabled = !data.active;
    return button;
  });
  if (!buttons.length) buttons.push(el("p", "Ainda ninguém está a trabalhar numa atividade. Podes escolher uma abaixo.", "muted"));
  $("board-choices").replaceChildren(...buttons);
  const select = $("board-other"), chosen = select.value;
  const all = Object.values(data.activities).sort((a, b) =>
    (a.m28p ? 0 : 1) - (b.m28p ? 0 : 1) || (a.m28p?.order ?? 0) - (b.m28p?.order ?? 0) ||
    (a.m28p?.kind_order ?? 0) - (b.m28p?.kind_order ?? 0) || a.title.localeCompare(b.title, "pt"));
  select.replaceChildren(...all.map(a => new Option(a.title, a.code)));
  if (chosen) select.value = chosen;
  $("board-off").disabled = !focus;
  for (const id of ["board-show-other", "board-off"]) if (!data.active) $(id).disabled = true;
  $("board-show-other").disabled = !data.active || !all.length;
}
async function showOnBoard(activityCode) {
  try {
    await api(`/api/learning/lessons/${code}/board`, "PUT", {activity_code: activityCode});
    await refresh();
    status(activityCode ? `No quadro: ${titleOf(activityCode)}.` : "O quadro deixou de mostrar este roteiro.");
  } catch (error) { status(error.message, true); }
}

async function refresh() {
  clearTimeout(timer);
  const request = ++refreshRequest;
  try {
    const fresh = await api(`/api/learning/lessons/${code}/progress`);
    if (request !== refreshRequest) return;
    data = fresh;
    // Uma atualização que saiu antes de uma gravação não repõe a observação antiga.
    for (const student of data.students) if (notes.has(student.id)) student.note = notes.get(student.id).saved.trim();
    $("title").textContent = data.title;
    document.title = `${data.title} · Acompanhar · PageCraft`;
    $("class-name").textContent = `Acompanhar a aula · ${data.class_name}`;
    $("code").textContent = data.code;
    $("entry").textContent = data.active ? `Os alunos abrem ${new URL(publicOrigin).host}/aula/${data.code} e escolhem o nome.` : "Roteiro encerrado: os alunos já não podem entrar. O registo continua disponível.";
    renderCounts();
    renderRows();
    renderBoard();
    if ($("status").classList.contains("error")) status("");
  } catch (error) { if (request === refreshRequest) status(error.message, true); }
  if (request === refreshRequest && !document.hidden) timer = setTimeout(refresh, 10000);
}
document.addEventListener("visibilitychange", () => { if (!document.hidden) refresh(); });

function markdown() {
  const lines = [`# ${data.title} — ${data.class_name}`, "", `Roteiro ${data.code} · registo de ${new Date(data.now).toLocaleString("pt-PT")}`, "",
    "Os números são acontecimentos registados no PageCraft, não classificações. O trabalho fora do PageCraft não é observado automaticamente.", ""];
  for (const student of data.students) {
    lines.push(`## ${student.display_name}`, "", `- Estado: ${STATES[student.state][0]}${student.offline ? ` — ${student.offline}` : ""}`);
    if (student.words.length) lines.push(`- Palavra: ${student.words.map(wordLabel).join(", ")}`);
    if (student.state !== "offline") lines.push(`- Atividades atribuídas: ${student.assigned.length}`);
    for (const r of student.realizations) {
      const said = r.assessment ? Object.entries(r.assessment).filter(([, n]) => n).map(([k, n]) => `${n} ${ANSWERS[k]}`).join(", ") || "sem respostas" : "sem autoavaliação";
      const unscored = r.unscored ? `, ${r.unscored} sem correção automática` : "";
      lines.push(`- ${r.title}: ${status_of(r)} · ${r.correct} respostas certas, ${r.different} diferentes da esperada${unscored}, ${r.help} pedidos de ajuda · autoavaliação: ${said}`);
      if (r.strategy) lines.push(`  - Estratégia: ${r.strategy}`);
      if (r.next_step) lines.push(`  - Próximo passo proposto: ${r.next_step}`);
    }
    if (!student.realizations.length && student.state !== "offline") lines.push("- Sem atividades começadas no PageCraft.");
    lines.push(`- Observação do professor: ${student.note || "por registar"}`, "");
  }
  return lines.join("\n");
}
async function flushNotes() {
  // Grava a observação em edição e espera pela fila de cada aluno antes de exportar.
  const saves = [...document.querySelectorAll("#rows textarea")].map(area => area.saveNote?.());
  const results = await Promise.allSettled(saves);
  if (results.some(result => result.status === "rejected")) {
    status("Há uma observação por guardar. Tenta novamente antes de descarregar ou imprimir.", true);
    return false;
  }
  for (const student of data.students) if (notes.has(student.id)) student.note = notes.get(student.id).saved.trim();
  return true;
}
addEventListener("beforeunload", event => {
  const unsaved = [...document.querySelectorAll("#rows textarea")].some(area => {
    const state = notes.get(area.dataset.student);
    return state?.pending || area.value.trim() !== (state?.saved || "").trim();
  });
  if (unsaved) { event.preventDefault(); event.returnValue = ""; }
});
$("download").onclick = async () => {
  if (!data || !(await flushNotes())) return;
  const link = el("a");
  link.href = URL.createObjectURL(new Blob([markdown()], {type: "text/markdown"}));
  link.download = `roteiro-${data.code}.md`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(link.href), 1000);
};
$("print").onclick = async () => {
  if (!data || !(await flushNotes())) return;
  document.querySelectorAll(".live-table details").forEach(d => { d.open = true; });
  print();
};
$("board-show-other").onclick = () => showOnBoard($("board-other").value);
$("board-off").onclick = () => showOnBoard(null);

(async () => {
  if (!/^[A-Z2-9]{7}$/.test(code)) { status("Abre um roteiro a partir de «Roteiros da aula».", true); return; }
  $("reports-link").href = `/teacher/activities.html?aula=${code}#registos`;
  $("edit-link").href = `/teacher/lesson.html?aula=${code}`;
  try {
    const [info, pairing] = await Promise.all([api("/api/access-info"), api("/api/board/pairing")]);
    publicOrigin = info.public_origin || location.origin;
    if (!pairing.paired) {
      $("board-pairing").append("Ainda não há quadro emparelhado. ");
      const link = el("a", "Emparelhar o quadro em «Aula ao vivo»");
      link.href = "/teacher/class.html";
      $("board-pairing").append(link);
    }
  } catch (error) { status(error.message, true); }
  await refresh();
})();
