"use strict";
const $ = id => document.getElementById(id);
let classes = [], lessons = [], assignments = [], current = null, editing = null, selection;
let students = [], publicOrigin = location.origin, dirty = false;
function el(tag, text) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
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
  if (!response.ok) throw Error(typeof result.detail === "string" ? result.detail : "Revê os alunos e as atividades selecionadas.");
  return result;
}
function renderStudents(ids = []) {
  $("students").replaceChildren();
  for (const student of students) {
    const label = el("label"), input = el("input");
    input.type = "checkbox";
    input.value = student.id;
    input.checked = ids.includes(student.id);
    label.append(input, document.createTextNode(student.display_name));
    $("students").append(label);
  }
}
function renderAssignments() {
  $("assignments").replaceChildren();
  for (const [index, assignment] of assignments.entries()) {
    const card = el("article");
    card.className = "card";
    card.append(el("h3", assignment.title), el("p", students.filter(s => assignment.student_ids.includes(s.id)).map(s => s.display_name).join(", ")));
    const details = el("details"), list = el("ul");
    details.append(el("summary", `${assignment.activity_codes.length} atividades`));
    for (const code of assignment.activity_codes) list.append(el("li", selection.activities.find(a => a.code === code)?.title || code));
    details.append(list);
    const edit = el("button", "Alterar conjunto"), remove = el("button", "Retirar conjunto");
    edit.type = remove.type = "button";
    edit.onclick = () => {
      editing = index;
      $("assignment-title").value = assignment.title;
      renderStudents(assignment.student_ids);
      selection.selected = new Set(assignment.activity_codes);
      selection.render();
      $("add-assignment").textContent = "Guardar alteração do conjunto";
      $("cancel-assignment").hidden = false;
      $("assignment-title").focus();
    };
    remove.onclick = () => {
      assignments.splice(index, 1);
      dirty = true;
      resetAssignment();
      renderAssignments();
    };
    card.append(details, edit, document.createTextNode(" "), remove);
    $("assignments").append(card);
  }
  if (!assignments.length) $("assignments").append(el("p", "Acrescenta abaixo os alunos e as atividades do primeiro conjunto."));
  const assigned = new Set(assignments.flatMap(a => a.student_ids));
  const remaining = students.filter(s => !assigned.has(s.id));
  $("unassigned").textContent = remaining.length ? `Ainda sem atividades: ${remaining.map(s => s.display_name).join(", ")}.` : "Todos os alunos têm atividades atribuídas.";
}
function resetAssignment() {
  editing = null;
  $("assignment-title").value = "";
  renderStudents();
  selection.selected.clear();
  selection.render();
  $("add-assignment").textContent = "Acrescentar conjunto ao roteiro";
  $("cancel-assignment").hidden = false;
  $("assignment-status").textContent = "";
}
function showLink() {
  $("entry-link").replaceChildren();
  if (!current) return;
  const link = el("a", `${publicOrigin}/aula/${current.code}`);
  link.href = `${publicOrigin}/aula/${current.code}`;
  link.target = "_blank";
  link.rel = "noopener";
  $("entry-link").append(el("strong", `Código da aula: ${current.code}. `), link,
    el("span", current.active ? " · Os alunos entram pelo código e escolhem o nome." : " · Roteiro encerrado."));
  const reports = el("a", "Ver registos deste roteiro");
  reports.href = `/teacher/activities.html?aula=${current.code}#registos`;
  const line = el("p");
  line.append(reports);
  $("entry-link").append(line);
}
function openLesson(lesson) {
  if (dirty && !confirm("Há alterações por guardar. Queres abrir outro roteiro?")) return;
  current = lesson;
  assignments = lesson ? structuredClone(lesson.assignments) : [];
  $("lesson-title").value = lesson?.title || "";
  $("lesson-class").disabled = !!lesson;
  if (lesson) {
    if (![...$("lesson-class").options].some(o => o.value === lesson.class_id))
      $("lesson-class").append(new Option(lesson.class_name, lesson.class_id));
    $("lesson-class").value = lesson.class_id;
  }
  students = lesson?.students || classes.find(c => c.id === $("lesson-class").value)?.students || [];
  studentsClass = $("lesson-class").value;
  $("lesson-active").checked = lesson?.active ?? true;
  $("form-title").textContent = lesson ? "Alterar roteiro da aula" : "Novo roteiro da aula";
  resetAssignment();
  renderAssignments();
  showLink();
  $("save-status").textContent = "";
  dirty = false;
}
async function loadLessons() {
  lessons = await api("/api/learning/lessons");
  $("lessons").replaceChildren();
  for (const lesson of lessons) {
    const row = el("p"), button = el("button", `${lesson.title} · ${lesson.class_name} · ${lesson.active ? "aberto" : "encerrado"}`);
    button.type = "button";
    button.onclick = () => openLesson(lesson);
    row.append(button);
    $("lessons").append(row);
  }
  if (!lessons.length) $("lessons").textContent = "Ainda não há roteiros guardados.";
}
$("new-lesson").onclick = () => openLesson(null);
$("cancel-assignment").onclick = resetAssignment;
$("all-students").onclick = () => { renderStudents(students.map(s => s.id)); dirty = true; };
$("lesson-class").onchange = () => {
  if (assignments.length && !confirm("Mudar de turma retira os conjuntos preparados. Continuar?")) {
    $("lesson-class").value = studentsClass;
    return;
  }
  studentsClass = $("lesson-class").value;
  students = classes.find(c => c.id === studentsClass)?.students || [];
  assignments = [];
  resetAssignment();
  renderAssignments();
  dirty = true;
};
let studentsClass = "";
$("add-assignment").onclick = () => {
  const title = $("assignment-title").value.trim();
  const student_ids = [...$("students").querySelectorAll("input:checked")].map(input => input.value);
  const activity_codes = [...selection.selected];
  if (!title || !student_ids.length || !activity_codes.length) {
    $("assignment-status").textContent = "Indica um nome e seleciona pelo menos um aluno e uma atividade.";
    return;
  }
  const assignment = {title, student_ids, activity_codes};
  if (editing === null) assignments.push(assignment);
  else assignments[editing] = assignment;
  resetAssignment();
  renderAssignments();
  dirty = true;
  $("assignment-status").textContent = "Conjunto incluído. Guarda o roteiro para o disponibilizar aos alunos.";
};
$("lesson-form").oninput = () => { dirty = true; };
$("lesson-form").onsubmit = async event => {
  event.preventDefault();
  if (editing !== null || $("assignment-title").value.trim() || selection.selected.size || $("students").querySelector("input:checked")) {
    status("Acrescenta o conjunto que estás a preparar, ou cancela a alteração, antes de guardar o roteiro.", true);
    return;
  }
  if (!assignments.length) { status("Acrescenta pelo menos um conjunto de alunos e atividades.", true); return; }
  const button = $("save-lesson");
  button.disabled = true;
  $("save-status").textContent = "A guardar…";
  try {
    const data = {title: $("lesson-title").value.trim(), assignments};
    if (current) Object.assign(data, {active: $("lesson-active").checked, revision: current.revision});
    else Object.assign(data, {class_id: $("lesson-class").value, active: $("lesson-active").checked});
    current = await api(current ? `/api/learning/lessons/${current.code}` : "/api/learning/lessons", current ? "PUT" : "POST", data);
    dirty = false;
    openLesson(current);
    await loadLessons();
    $("save-status").textContent = "Roteiro guardado.";
    status("Roteiro guardado. Partilha o código ou o endereço com a turma.");
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
    $("lesson-class").replaceChildren(...classes.map(c => new Option(c.name, c.id)));
    studentsClass = $("lesson-class").value;
    selection = new PageCraftActivitySelection($("activity-selection"), activities.filter(a => a.published), {onchange: () => { dirty = true; }});
    await loadLessons();
    dirty = false;
    openLesson(null);
    $("lesson-form").inert = false;
    if (!classes.length) { status("Cria uma turma com os nomes dos alunos antes de preparar o roteiro."); $("save-lesson").disabled = true; }
  } catch (error) { status(error.message, true); }
})();
