"use strict";
/* Roteiro da aula: uma linha por aluno. O roteiro guardado continua a ser uma
   lista de conjuntos; o editor agrupa os alunos com o mesmo plano ao guardar. */
const $ = id => document.getElementById(id);
let classes = [], lessons = [], catalog = [], published = [], current = null, selection;
let hintsRequest = 0; // as pistas só se aplicam à preparação que as pediu
let students = [], plan = new Map(), marked = new Set();
let publicOrigin = location.origin, dirty = false, studentsClass = "";
let words = new Map(); // id -> {id, label, order, codes}
let hints = new Map(); // id do aluno -> resumo factual da aula anterior (só ao preparar a próxima)

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
async function api(path, method = "GET", data) {
  const response = await fetch(path, { method, headers: data ? {"Content-Type": "application/json"} : {}, body: data ? JSON.stringify(data) : undefined });
  if (response.status === 401) { location.href = "/login"; throw Error("É necessário entrar."); }
  if (response.status === 204) return null;
  const result = await response.json();
  if (!response.ok) throw Error(typeof result.detail === "string" ? result.detail : "Revê os alunos e as atividades escolhidas.");
  return result;
}
const titleOf = code => {
  const activity = published.find(a => a.code === code);
  if (!activity) return code;
  return activity.retired ? `${activity.title} (coleção anterior)` : activity.title;
};
/* Atividades distintas: repetir um jogo cria outra realização, não outra atividade. */
function distinctFinished(student) {
  return new Set(student.realizations.filter(r => r.finished && student.assigned.includes(r.code)).map(r => r.code)).size;
}
const wordOf = activity => PageCraftActivitySelection.wordOf(activity);
const today = () => new Date().toLocaleDateString("pt-PT", {weekday: "long", day: "numeric", month: "numeric"});
const plural = (n, one, many) => `${n} ${n === 1 ? one : many}`;
// savedWord/savedWordCodes: os jogos que o roteiro guardou para a palavra, conservados
// enquanto o professor não mudar a palavra (encerrar um roteiro antigo não o altera).
const emptyPlan = () => ({word: "", extras: new Set(), offline: false, note: "", savedWord: "", savedWordCodes: []});
// Uma lista guardada vazia também conta: a palavra guardou zero jogos atuais.
const wordCodesOf = entry => entry.word && entry.word === entry.savedWord
  ? entry.savedWordCodes : (words.get(entry.word)?.codes || []);
// Qualquer escolha explícita da palavra (ou passar a «Fora do PageCraft») usa os jogos atuais.
function setWord(entry, word) {
  Object.assign(entry, {word, savedWord: "", savedWordCodes: []});
}

function buildWords() {
  words = new Map();
  for (const activity of catalog) {
    const word = wordOf(activity);
    if (!word) continue;
    if (!words.has(word.id)) words.set(word.id, {...word, codes: []});
    words.get(word.id).codes.push(activity);
  }
  for (const word of words.values())
    word.codes = word.codes.sort((a, b) => (a.m28p?.kind_order ?? 0) - (b.m28p?.kind_order ?? 0)).map(a => a.code);
  words = new Map([...words.entries()].sort(([, a], [, b]) => (a.order ?? 99) - (b.order ?? 99) || a.label.localeCompare(b.label, "pt")));
}
function wordLabel(id) {
  const word = words.get(id);
  if (!word) return id;
  return `${word.order ? word.order + ". " : ""}${word.label} (${word.codes.length} jogos)`;
}
function wordOptions(select, value) {
  select.replaceChildren(new Option("— sem palavra —", ""));
  for (const [id] of words) select.append(new Option(wordLabel(id), id));
  if (value && !words.has(value)) select.append(new Option(`${value} (sem jogos disponíveis)`, value));
  select.value = value || "";
}
function nextWord(id) {
  const ordered = [...words.keys()];
  const index = ordered.indexOf(id);
  return index >= 0 && index < ordered.length - 1 ? ordered[index + 1] : null;
}

let droppedCodes = new Set();
function planFromLesson(lesson) {
  const result = new Map(students.map(s => [s.id, emptyPlan()]));
  droppedCodes = new Set();
  for (const assignment of lesson?.assignments || []) {
    const codes = new Set(assignment.activity_codes);
    // Roteiros antigos não guardavam a palavra: reconhece-a quando estão todos os jogos atuais.
    const word = assignment.word || [...words.values()].find(w => w.codes.length && w.codes.every(c => codes.has(c)))?.id || "";
    for (const id of assignment.student_ids) {
      const entry = result.get(id);
      if (!entry) continue;
      if (word && !entry.word) Object.assign(entry, {word, savedWord: word, savedWordCodes: []});
      for (const code of assignment.activity_codes) {
        // Jogos de uma coleção substituída ficam onde estavam: não se oferecem a novas
        // atribuições, mas abrir um roteiro antigo não apaga o que lá está.
        const activity = published.find(a => a.code === code);
        if (!activity) { droppedCodes.add(code); continue; }
        // A coluna da palavra só volta a gravar os jogos atuais dessa palavra; tudo o resto
        // (outra palavra, coleção anterior) fica em outras atividades e não se perde.
        if (entry.word && words.get(entry.word)?.codes.includes(code)) {
          if (entry.savedWord === entry.word && !entry.savedWordCodes.includes(code)) entry.savedWordCodes.push(code);
          continue;
        }
        entry.extras.add(code);
      }
    }
  }
  for (const [id, note] of Object.entries(lesson?.offline || {})) {
    const entry = result.get(id);
    if (entry) Object.assign(entry, {offline: true, note, word: "", extras: new Set()});
  }
  return result;
}
function assignmentsFromPlan() {
  const groups = new Map();
  for (const student of students) {
    const entry = plan.get(student.id);
    if (!entry || entry.offline || (!entry.word && !entry.extras.size)) continue;
    const extras = [...entry.extras].sort();
    const wordCodes = [...wordCodesOf(entry)].sort();
    const key = `${entry.word}|${wordCodes.join(",")}|${extras.join(",")}`;
    if (!groups.has(key)) groups.set(key, {word: entry.word, wordCodes, extras, student_ids: []});
    groups.get(key).student_ids.push(student.id);
  }
  return [...groups.values()].map(group => {
    const parts = [];
    if (group.word) parts.push(`Palavra ${words.get(group.word)?.label || group.word}`);
    if (group.extras.length) parts.push(titleOf(group.extras[0]) + (group.extras.length > 1 ? ` e mais ${group.extras.length - 1}` : ""));
    const codes = [...group.wordCodes, ...group.extras];
    const assignment = {title: parts.join(" + ").slice(0, 120), student_ids: group.student_ids, activity_codes: [...new Set(codes)]};
    if (group.word) assignment.word = group.word;
    return assignment;
  }).filter(a => a.activity_codes.length);
}
function offlineFromPlan() {
  return Object.fromEntries(students.filter(s => plan.get(s.id)?.offline).map(s => [s.id, plan.get(s.id).note.trim().slice(0, 120)]));
}

function changed() { dirty = true; renderPlan(); }
function renderPlan() {
  const body = $("plan-rows");
  const focusedId = document.activeElement?.dataset?.focusKey;
  body.replaceChildren();
  for (const student of students) {
    const entry = plan.get(student.id) || emptyPlan();
    plan.set(student.id, entry);
    const row = el("tr");
    row.dataset.student = student.id;
    if (entry.offline) row.className = "is-offline";
    const markCell = el("td"), mark = el("input");
    mark.type = "checkbox";
    mark.checked = marked.has(student.id);
    mark.setAttribute("aria-label", `Marcar ${student.display_name}`);
    mark.dataset.focusKey = `mark-${student.id}`;
    mark.onchange = () => { mark.checked ? marked.add(student.id) : marked.delete(student.id); renderToolbar(); };
    markCell.append(mark);
    const name = el("th", student.display_name);
    name.scope = "row";
    if (hints.has(student.id)) name.append(el("span", hints.get(student.id), "row-hint"));

    const wordCell = el("td");
    if (!entry.offline) {
      const select = el("select");
      select.setAttribute("aria-label", `Palavra de ${student.display_name}`);
      select.dataset.focusKey = `word-${student.id}`;
      wordOptions(select, entry.word);
      select.onchange = () => { setWord(entry, select.value); changed(); };
      const next = el("button", "›", "icon-button");
      next.type = "button";
      next.title = "Palavra seguinte";
      next.setAttribute("aria-label", `Palavra seguinte para ${student.display_name}`);
      next.dataset.focusKey = `next-${student.id}`;
      next.disabled = !nextWord(entry.word);
      next.onclick = () => { setWord(entry, nextWord(entry.word)); changed(); };
      const line = el("div", undefined, "word-cell");
      line.append(select, next);
      wordCell.append(line);
      // O seletor mostra os jogos atuais; um roteiro guardado pode conservar outros.
      const kept = wordCodesOf(entry);
      if (entry.word && entry.word === entry.savedWord && kept.length !== (words.get(entry.word)?.codes.length || 0))
        wordCell.append(el("span", `Este roteiro mantém ${plural(kept.length, "jogo guardado", "jogos guardados")} desta palavra. Para usar os jogos atuais, escolhe outra palavra e volta a esta.`, "row-hint"));
    } else wordCell.append(el("span", "—", "muted"));

    const extrasCell = el("td");
    if (!entry.offline && entry.extras.size) {
      const list = el("ul", undefined, "chips");
      for (const code of entry.extras) {
        const item = el("li"), remove = el("button", "×", "chip-remove");
        remove.type = "button";
        remove.setAttribute("aria-label", `Retirar ${titleOf(code)} de ${student.display_name}`);
        remove.dataset.focusKey = `remove-${student.id}-${code}`;
        remove.onclick = () => { entry.extras.delete(code); changed(); };
        item.append(el("span", titleOf(code)), remove);
        list.append(item);
      }
      extrasCell.append(list);
    } else extrasCell.append(el("span", "—", "muted"));

    const offlineCell = el("td"), label = el("label", undefined, "selection-label"), check = el("input");
    check.type = "checkbox";
    check.checked = entry.offline;
    check.dataset.focusKey = `offline-${student.id}`;
    check.setAttribute("aria-label", `${student.display_name} trabalha fora do PageCraft`);
    check.onchange = () => {
      entry.offline = check.checked;
      if (entry.offline) { setWord(entry, ""); entry.extras.clear(); }
      changed();
    };
    label.append(check);
    offlineCell.append(label);
    if (entry.offline) {
      const note = el("input");
      note.maxLength = 120;
      note.value = entry.note;
      note.placeholder = "Ex.: caderno, leitura comigo";
      note.setAttribute("aria-label", `O que ${student.display_name} faz fora do PageCraft`);
      note.dataset.focusKey = `note-${student.id}`;
      note.oninput = () => { entry.note = note.value; dirty = true; };
      offlineCell.append(note);
    }
    row.append(markCell, name, wordCell, extrasCell, offlineCell);
    body.append(row);
  }
  if (!students.length) {
    const row = el("tr"), cell = el("td", "Esta turma ainda não tem alunos.");
    cell.colSpan = 5;
    row.append(cell);
    body.append(row);
  }
  if (focusedId) body.querySelector(`[data-focus-key="${CSS.escape(focusedId)}"]`)?.focus({preventScroll: true});
  renderSummary();
  renderToolbar();
}
function renderSummary() {
  const withWork = [], offline = [], empty = [];
  for (const student of students) {
    const entry = plan.get(student.id);
    if (entry.offline) offline.push(student.display_name);
    else if (entry.word || entry.extras.size) withWork.push(student.display_name);
    else empty.push(student.display_name);
  }
  const parts = [`Com atividades: ${withWork.length}`, `Fora do PageCraft: ${offline.length}`];
  parts.push(empty.length ? `Sem nada atribuído: ${empty.join(", ")}` : "Todos os alunos têm um plano");
  $("plan-summary").textContent = parts.join(" · ") + ".";
}
function renderToolbar() {
  const count = marked.size;
  $("marked-count").textContent = count ? `${count} ${count === 1 ? "aluno marcado" : "alunos marcados"}` : "Nenhum aluno marcado";
  for (const id of ["apply-word", "next-word", "bulk-offline", "bulk-clear", "assign-selected", "pick-activities"]) $(id).disabled = !count;
  if (!count && !$("picker").hidden) closePicker();
  $("assign-selected").textContent = count ? `Atribuir aos ${count} alunos marcados` : "Atribuir aos alunos marcados";
  if (count === 1) $("assign-selected").textContent = "Atribuir ao aluno marcado";
}
function bulk(action, message) {
  if (!marked.size) return;
  for (const id of marked) action(plan.get(id));
  $("bulk-status").textContent = message;
  changed();
}

function lessonRow(lesson) {
  const item = el("li", undefined, "lesson-row");
  const copy = el("div");
  const date = new Date(lesson.updated_at).toLocaleDateString("pt-PT");
  copy.append(el("strong", lesson.title), el("span", ` · ${lesson.class_name} · ${lesson.active ? "aberto" : "encerrado"} · ${date}`, "muted"));
  const actions = el("div", undefined, "row");
  const follow = el("a", "Acompanhar e quadro", "button primary");
  follow.href = `/teacher/lesson-live.html?aula=${lesson.code}`;
  const edit = el("button", "Alterar"), next = el("button", "Preparar a próxima aula");
  edit.type = next.type = "button";
  edit.setAttribute("aria-label", `Alterar ${lesson.title}`);
  next.setAttribute("aria-label", `Preparar a próxima aula a partir de ${lesson.title}`);
  edit.onclick = () => openLesson(lesson);
  next.onclick = () => openLesson(lesson, {copy: true});
  actions.append(follow, edit, next);
  item.append(copy, actions);
  return item;
}
function showLink() {
  $("entry-link").replaceChildren();
  if (!current) return;
  const url = `${publicOrigin}/aula/${current.code}`;
  const link = el("a", url);
  link.href = url;
  link.target = "_blank";
  link.rel = "noopener";
  const line = el("p");
  line.append(el("strong", `Código da aula: ${current.code}. `), link,
    el("span", current.active ? " · Os alunos entram pelo código e escolhem o nome." : " · Roteiro encerrado."));
  const more = el("p", undefined, "row");
  const follow = el("a", "Acompanhar a aula e escolher o quadro", "button");
  follow.href = `/teacher/lesson-live.html?aula=${current.code}`;
  const reports = el("a", "Ver registos deste roteiro");
  reports.href = `/teacher/activities.html?aula=${current.code}#registos`;
  more.append(follow, reports);
  $("entry-link").append(line, more);
}
function setStudentsFor(classId) {
  studentsClass = classId;
  students = classes.find(c => c.id === classId)?.students || [];
}
function openLesson(lesson, {copy = false} = {}) {
  if (dirty && !confirm("Há alterações por guardar. Queres abrir outro roteiro?")) return;
  current = copy ? null : lesson;
  const select = $("lesson-class");
  if (lesson && ![...select.options].some(o => o.value === lesson.class_id))
    select.append(new Option(lesson.class_name, lesson.class_id));
  if (lesson) select.value = lesson.class_id;
  select.disabled = !!current;
  // Um roteiro guardado conserva a lista de alunos com que foi criado.
  if (current) { students = current.students; studentsClass = current.class_id; }
  else setStudentsFor(select.value);
  plan = planFromLesson(lesson);
  marked = new Set();
  hints = new Map();
  // A próxima aula começa sem «Fora do PageCraft»: a nota anterior raramente continua a valer.
  const wasOffline = copy ? students.filter(s => plan.get(s.id)?.offline).map(s => s.display_name) : [];
  if (copy) for (const entry of plan.values()) if (entry.offline) Object.assign(entry, emptyPlan());
  // Jogos de uma coleção substituída conservam-se ao editar o roteiro original, mas não passam para uma aula nova.
  // Num roteiro antigo, a palavra só se conhece pelos jogos retirados: quando é uma só,
  // passa para a coluna da palavra com os jogos atuais.
  let retiredLeft = 0;
  const needsWord = [];
  if (copy) for (const [id, entry] of plan) {
    // Uma aula nova usa sempre os jogos atuais de cada palavra.
    Object.assign(entry, {savedWord: "", savedWordCodes: []});
    const retired = [...entry.extras].map(c => published.find(a => a.code === c)).filter(a => a?.retired);
    const retiredWords = new Set(retired.map(a => wordOf(a)?.id).filter(Boolean));
    retired.forEach(a => entry.extras.delete(a.code));
    retiredLeft += retired.length;
    if (!entry.word && retiredWords.size === 1 && words.has([...retiredWords][0])) entry.word = [...retiredWords][0];
    else if (retired.length && !entry.word) needsWord.push(students.find(s => s.id === id)?.display_name);
  }
  $("lesson-title").value = copy || !lesson ? `Aula de ${today()}` : lesson.title;
  $("lesson-active").checked = current?.active ?? true;
  $("form-title").textContent = current ? "Alterar roteiro da aula" : copy ? "Próxima aula a partir de um roteiro" : "Novo roteiro da aula";
  const notes = [];
  if (copy) notes.push("Por baixo de cada nome está o que aconteceu na aula anterior. Marca os alunos que avançam e carrega em «Avançar para a palavra seguinte».");
  if (retiredLeft) notes.push("Os jogos da coleção anterior não foram copiados; cada palavra traz os jogos atuais.");
  if (needsWord.length === 1) notes.push(`${needsWord[0]} perdeu jogos da coleção anterior e está sem palavra. Escolhe a palavra na linha.`);
  else if (needsWord.length) notes.push(`Perderam jogos da coleção anterior e estão sem palavra: ${needsWord.join(", ")}. Escolhe a palavra na linha.`);
  if (wasOffline.length) notes.push(`Na aula anterior estiveram fora do PageCraft: ${wasOffline.join(", ")}. Marca-os de novo se for o caso.`);
  if (droppedCodes.size) notes.push(droppedCodes.size === 1
    ? "1 atividade deixou de estar disponível e não é atribuída ao guardar."
    : `${droppedCodes.size} atividades deixaram de estar disponíveis e não são atribuídas ao guardar.`);
  $("bulk-status").textContent = notes.join(" ");
  closePicker();
  renderPlan();
  showLink();
  $("save-status").textContent = "";
  dirty = !!copy;
  if (lesson) $("form-title").focus();
  const request = ++hintsRequest;
  if (copy) loadHints(lesson, request);
}
async function loadHints(source, request) {
  try {
    const progress = await api(`/api/learning/lessons/${source.code}/progress`);
    if (request !== hintsRequest) return;
    for (const student of progress.students) {
      const parts = [];
      if (student.state === "offline") parts.push(`fora do PageCraft${student.offline ? ` (${student.offline})` : ""}`);
      else if (!student.realizations.length) parts.push(student.assigned.length ? "não começou atividades" : "sem atividades");
      else {
        if (student.words.length) parts.push(student.words.map(w => words.get(w)?.label || w).join(", "));
        parts.push(`${distinctFinished(student)} de ${student.assigned.length} terminadas`);
        const assessed = new Set(student.realizations.filter(r => r.assessment).map(r => r.code)).size;
        parts.push(assessed ? `autoavaliação em ${assessed}` : "sem autoavaliação");
      }
      if (student.note) parts.push(`«${student.note.slice(0, 60)}${student.note.length > 60 ? "…" : ""}»`);
      hints.set(student.id, `Aula anterior: ${parts.join(" · ")}`);
    }
    renderPlan();
  } catch { /* As pistas são uma ajuda; o roteiro prepara-se sem elas. */ }
}
async function loadLessons() {
  lessons = await api("/api/learning/lessons");
  $("lessons").replaceChildren(...lessons.map(lessonRow));
  if (!lessons.length) $("lessons").append(el("li", "Ainda não há roteiros guardados.", "muted"));
}
function openPicker() {
  // As palavras têm coluna própria: a seleção abre nas outras atividades, sem impedir mudar.
  if (!selection.collection.value && catalog.some(a => !wordOf(a))) { selection.collection.value = "other"; selection.render(); }
  $("picker").hidden = false;
  $("pick-activities").setAttribute("aria-expanded", "true");
  $("picker").querySelector("input")?.focus();
}
function closePicker() {
  $("picker").hidden = true;
  $("pick-activities").setAttribute("aria-expanded", "false");
  selection?.selected.clear();
  selection?.render();
}

$("new-lesson").onclick = () => openLesson(null);
$("mark-all").onclick = () => { marked = new Set(students.map(s => s.id)); renderPlan(); };
$("mark-none").onclick = () => { marked.clear(); renderPlan(); };
$("apply-word").onclick = () => {
  const word = $("bulk-word").value;
  let changedCount = 0;
  bulk(entry => { if (!entry.offline) { setWord(entry, word); changedCount++; } }, "");
  const skipped = marked.size - changedCount;
  const done = !changedCount ? "Nenhum aluno marcado pode receber a palavra: estão fora do PageCraft."
    : word ? `Palavra ${words.get(word)?.label} dada a ${plural(changedCount, "aluno", "alunos")}.` : `Palavra retirada a ${plural(changedCount, "aluno", "alunos")}.`;
  $("bulk-status").textContent = done + (changedCount && skipped ? ` ${plural(skipped, "aluno fora do PageCraft ficou", "alunos fora do PageCraft ficaram")} sem palavra.` : "");
};
$("next-word").onclick = () => {
  let moved = 0;
  bulk(entry => { const next = nextWord(entry.word); if (next && !entry.offline) { setWord(entry, next); moved++; } }, "");
  $("bulk-status").textContent = moved ? `${moved} ${moved === 1 ? "aluno avançou" : "alunos avançaram"} para a palavra seguinte.` : "Os alunos marcados não têm uma palavra seguinte.";
};
$("bulk-offline").onclick = () => bulk(entry => { entry.offline = true; setWord(entry, ""); entry.extras.clear(); },
  "Alunos marcados fora do PageCraft nesta aula. Podes escrever o que vão fazer.");
$("bulk-clear").onclick = () => bulk(entry => Object.assign(entry, emptyPlan()), "Atribuição dos alunos marcados limpa.");
$("pick-activities").onclick = () => $("picker").hidden ? openPicker() : closePicker();
$("close-picker").onclick = () => { closePicker(); $("pick-activities").focus(); };
$("assign-selected").onclick = () => {
  const codes = [...selection.selected];
  if (!codes.length) { $("bulk-status").textContent = "Escolhe pelo menos uma atividade."; return; }
  bulk(entry => { entry.offline = false; codes.forEach(code => entry.extras.add(code)); },
    `${codes.length} ${codes.length === 1 ? "atividade atribuída" : "atividades atribuídas"} aos alunos marcados.`);
  closePicker();
  $("pick-activities").focus();
};
$("lesson-class").onchange = () => {
  const assigned = [...plan.values()].some(e => e.offline || e.word || e.extras.size);
  if (assigned && !confirm("Mudar de turma retira o que já atribuíste. Continuar?")) {
    $("lesson-class").value = studentsClass;
    return;
  }
  setStudentsFor($("lesson-class").value);
  hintsRequest++;
  hints = new Map();
  plan = planFromLesson(null);
  marked.clear();
  changed();
};
$("lesson-title").oninput = $("lesson-active").onchange = () => { dirty = true; };
$("lesson-form").onsubmit = async event => {
  event.preventDefault();
  const assignments = assignmentsFromPlan(), offline = offlineFromPlan();
  if (!assignments.length && !Object.keys(offline).length) { status("Atribui uma palavra ou atividades a pelo menos um aluno.", true); return; }
  const button = $("save-lesson");
  button.disabled = true;
  $("save-status").textContent = "A guardar…";
  try {
    const data = {title: $("lesson-title").value.trim(), assignments, offline, active: $("lesson-active").checked};
    if (current) data.revision = current.revision;
    else data.class_id = $("lesson-class").value;
    const saved = await api(current ? `/api/learning/lessons/${current.code}` : "/api/learning/lessons", current ? "PUT" : "POST", data);
    dirty = false;
    await loadLessons();
    openLesson(saved);
    $("save-status").textContent = "Roteiro guardado.";
    status("Roteiro guardado. Partilha o código com a turma e abre «Acompanhar a aula».");
  } catch (error) { status(error.message, true); $("save-status").textContent = "Não foi possível guardar."; }
  finally { button.disabled = false; }
};
addEventListener("beforeunload", event => { if (dirty) { event.preventDefault(); event.returnValue = ""; } });
(async () => {
  try {
    await api("/api/teacher-bootstrap");
    const [info, roster, activities] = await Promise.all([api("/api/access-info"), api("/api/classes"), api("/api/learning/activities")]);
    publicOrigin = info.public_origin || location.origin;
    classes = roster;
    // Só a coleção atual: jogos substituídos por coleções novas não se atribuem.
    published = activities.filter(a => a.published);
    catalog = published.filter(a => !a.retired);
    buildWords();
    wordOptions($("bulk-word"), "");
    $("lesson-class").replaceChildren(...classes.map(c => new Option(`${c.name} · ${c.students.length} alunos`, c.id)));
    selection = new PageCraftActivitySelection($("activity-selection"), catalog);
    await loadLessons();
    const requested = new URLSearchParams(location.search).get("aula")?.toUpperCase();
    openLesson(lessons.find(l => l.code === requested) || null);
    $("lesson-form").inert = false;
    if (!classes.length) { status("Cria uma turma com os nomes dos alunos antes de preparar o roteiro."); $("save-lesson").disabled = true; }
  } catch (error) { status(error.message, true); }
})();
