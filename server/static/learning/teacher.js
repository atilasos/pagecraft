"use strict";
const $ = (id) => document.getElementById(id);
let reports = [];
let publicOrigin = location.origin;

function showTeacherSection(focus = false) {
  const viewingReports = location.hash === "#registos";
  $("activities-panel").hidden = viewingReports;
  $("reports-panel").hidden = !viewingReports;
  $("page-title").textContent = viewingReports ? "Registos de trabalho" : "Atividades";
  document.title = $("page-title").textContent + " · PageCraft";
  for (const [id, current] of [["nav-activities", !viewingReports], ["nav-reports", viewingReports]]) {
    if (current) $(id).setAttribute("aria-current", "page");
    else $(id).removeAttribute("aria-current");
  }
  if (focus) $("page-title").focus();
}
window.addEventListener("hashchange", () => showTeacherSection(true));
showTeacherSection();
const eventLabels = {
  activity_loaded: "Abriu a atividade",
  unit_started: "Começou uma etapa",
  attempt: "Tentativa",
  discovery: "Descoberta",
  assessment_result: "Trabalho registado",
  help_needed: "Pedido de ajuda",
  share_requested: "Pedido de partilha",
  language_changed: "Mudança de língua",
  level_changed: "Mudança de apoio",
};
function el(tag, text, cls) {
  const e = document.createElement(tag);
  if (text !== undefined) e.textContent = text;
  if (cls) e.className = cls;
  return e;
}
function status(text, error = false) {
  $("status").textContent = text;
  $("status").classList.toggle("error", error);
}
async function api(path, method = "GET", data) {
  const r = await fetch(path, {
    method,
    headers: data ? { "Content-Type": "application/json" } : {},
    body: data ? JSON.stringify(data) : undefined,
  });
  if (r.status === 401) {
    location.href = "/login";
    throw Error("É necessário entrar.");
  }
  if (!r.ok) {
    const d = await r.json().catch(() => ({}));
    throw Error(
      typeof d.detail === "string" ? d.detail : "Não foi possível concluir.",
    );
  }
  return r.status === 204 ? null : r.json();
}
let library = [];
let libraryLoaded = false;
let libraryPage = 1;
const LIBRARY_PAGE_SIZE = 6;
const libraryParams = new URLSearchParams(location.search);
$("library-search").value = libraryParams.get("q") || "";
$("library-state").value = libraryParams.get("estado") || "";
$("library-year").value = libraryParams.get("ano") || "";

function searchText(value) {
  return String(value || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("pt");
}

async function loadActivities() {
  const all = await api("/api/learning/activities?include_archived=true");
  library = all.filter((a) => !a.archived_at)
    .sort((a, b) => (b.created_at || "").localeCompare(a.created_at || ""));
  libraryLoaded = true;
  const selected = $("filter-activity").value;
  $("filter-activity").replaceChildren(new Option("Todas", ""));
  for (const a of all) {
    $("filter-activity").append(new Option(a.title + (a.archived_at ? " (retirada)" : ""), a.code));
  }
  $("filter-activity").value = selected;
  renderLibrary();
}

function renderLibrary() {
  if (!libraryLoaded) return;
  const query = searchText($("library-search").value.trim());
  const state = $("library-state").value;
  const year = $("library-year").value;
  const matches = library.filter(a =>
    (!query || searchText(a.title + " " + a.code).includes(query)) &&
    (!year || String(a.year) === year) &&
    (!state || (state === "published" ? a.published : !a.published)));
  const pages = Math.max(1, Math.ceil(matches.length / LIBRARY_PAGE_SIZE));
  libraryPage = Math.min(libraryPage, pages);
  const start = (libraryPage - 1) * LIBRARY_PAGE_SIZE;
  const drafts = library.filter(a => !a.published).length;
  $("library-total").textContent = `${library.length} atividades · ${drafts} por rever · ${library.length - drafts} disponíveis`;
  $("activity-count").textContent = matches.length
    ? `${start + 1} a ${Math.min(start + LIBRARY_PAGE_SIZE, matches.length)} de ${matches.length} atividades`
    : "Sem atividades para estes filtros.";
  $("activities").replaceChildren(...matches.slice(start, start + LIBRARY_PAGE_SIZE).map(activityRow));
  if (!matches.length) $("activities").append(el("p", library.length
    ? "Experimenta outro título, código ou ano, ou limpa os filtros."
    : "Ainda não há atividades registadas para revisão.", "muted"));
  $("library-pagination").hidden = pages < 2;
  $("library-page").textContent = `Página ${libraryPage} de ${pages}`;
  $("library-previous").disabled = libraryPage === 1;
  $("library-next").disabled = libraryPage === pages;
}

function activityRow(a) {
  const row = el("article", undefined, "activity-row");
  row.dataset.code = a.code;
  const main = el("div", undefined, "activity-row-main");
  const copy = el("div", undefined, "activity-row-copy");
  const heading = el("div", undefined, "activity-row-title");
  heading.append(el("h3", a.title), el("span", a.published ? "Disponível" : "Por rever", "tag"));
  copy.append(heading,
    el("p", `${a.year}.º ano · ${a.duration} min · ${a.languages.includes("en") ? "PT/EN" : "Português"} · ${a.code}`, "muted"));
  const actions = el("div", undefined, "activity-row-actions");
  const preview = el("a", a.published ? "Abrir atividade" : "Pré-visualizar", "button");
  preview.href = (a.published ? publicOrigin : "") + "/" + a.code;
  preview.target = "_blank";
  preview.rel = "noopener";
  const records = el("button", "Ver registos");
  records.onclick = () => {
    $("filter-activity").value = a.code;
    render();
    location.hash = "registos";
  };
  actions.append(preview, records);
  main.append(copy, actions);
  const details = el("details");
  details.append(el("summary", a.published ? "Endereço da atividade" : "Revisão e publicação"));
  details.append(el("p", a.published ? publicOrigin + "/" + a.code
    : "Experimenta a atividade antes de a disponibilizar aos alunos.", "muted"));
  if (!a.published) {
    const publish = el("button", "Aprovar e publicar", "primary");
    const feedback = el("p");
    feedback.setAttribute("role", "status");
    publish.onclick = async () => {
      if (!confirm("Já reveste a atividade? Ao publicar, qualquer pessoa com o endereço pode abri-la.")) return;
      publish.disabled = true;
      feedback.textContent = "A publicar…";
      try {
        Object.assign(a, await api(`/api/learning/activities/${a.code}/publish`, "POST"));
        renderLibrary();
        $("library-load-status").textContent = "Atividade publicada. Já podes partilhar o endereço com os alunos.";
        $("activity-count").focus();
      } catch (error) {
        feedback.textContent = error.message;
        feedback.className = "error";
        publish.disabled = false;
      }
    };
    details.append(publish, feedback);
  }
  row.append(main, details);
  return row;
}

function filterLibrary() {
  libraryPage = 1;
  const url = new URL(location.href);
  for (const [key, id] of [["q", "library-search"], ["estado", "library-state"], ["ano", "library-year"]]) {
    const value = $(id).value.trim();
    if (value) url.searchParams.set(key, value);
    else url.searchParams.delete(key);
  }
  history.replaceState(null, "", url);
  renderLibrary();
}
for (const id of ["library-search", "library-state", "library-year"]) $(id).addEventListener("input", filterLibrary);
$("library-clear").onclick = () => {
  for (const id of ["library-search", "library-state", "library-year"]) $(id).value = "";
  filterLibrary();
  $("library-search").focus();
};
for (const [id, step] of [["library-previous", -1], ["library-next", 1]]) $(id).onclick = () => {
  libraryPage += step;
  renderLibrary();
  $("activity-count").focus();
};
async function refreshActivities() {
  $("library-retry").hidden = true;
  $("library-load-status").textContent = "A carregar as atividades…";
  try {
    await loadActivities();
    $("library-load-status").textContent = "";
  } catch (error) {
    $("library-total").textContent = "Biblioteca indisponível";
    $("library-load-status").textContent = "Não foi possível carregar as atividades. " + error.message;
    $("library-retry").hidden = false;
  }
}
$("library-retry").onclick = refreshActivities;
function field(title, value, multi = false) {
  const label = el("label", title),
    input = el(multi ? "textarea" : "input");
  input.value = value || "";
  label.append(input);
  return { label, input };
}
function render() {
  $("support-summary").replaceChildren();
  const name = $("filter-name").value.trim().toLocaleLowerCase("pt"),
    group = $("filter-group").value.trim().toLocaleLowerCase("pt"),
    code = $("filter-activity").value,
    from = $("filter-from").value,
    to = $("filter-to").value;
  const filtered = reports.filter(
    (r) =>
      r.name.toLocaleLowerCase("pt").includes(name) &&
      r.group.toLocaleLowerCase("pt").includes(group) &&
      (!code || r.code === code) &&
      (!from || r.started_at.slice(0, 10) >= from) &&
      (!to || r.started_at.slice(0, 10) <= to),
  );
  $("reports").replaceChildren();
  $("summary").textContent =
    `${filtered.length} realizações · ${filtered.filter((r) => r.completed_at).length} terminadas`;
  for (const r of filtered) {
    const card = el("article", undefined, "card");
    card.append(
      el("span", r.completed_at ? "Terminada" : "Em curso", "tag"),
      el("h3", `${r.name} · ${r.title}`),
      el(
        "p",
        `${r.group || "Turma por indicar"} · ${new Date(r.started_at).toLocaleString("pt-PT")} · ${r.mode === "home" ? "Em casa" : "Na aula"}`,
        "muted",
      ),
    );
    const evidence = el("details");
    evidence.append(
      el("summary", `Evidências no PageCraft (${r.events.length})`),
    );
    for (const event of r.evidence || []) {
      evidence.append(el("p", eventLabels[event.type] || "Trabalho registado"));
      const list = el("ul");
      for (const line of event.text) list.append(el("li", line));
      evidence.append(list);
    }
    card.append(evidence, el("h3", "A voz do aluno"));
    if (r.assessment) {
      const labels = {
        alone: "Consegui com autonomia",
        help: "Consegui com ajuda",
        practising: "Quero praticar mais",
        skip: "Sem resposta",
      };
      for (const c of r.criteria)
        card.append(
          el(
            "p",
            `${c.pt}: ${labels[r.assessment.answers[c.id]] || "Sem resposta"}`,
          ),
        );
      card.append(
        el("p", "Estratégia: " + (r.assessment.strategy || "Sem resposta")),
        el(
          "p",
          "Próximo passo proposto: " +
            (r.assessment.next_step || "Sem resposta"),
        ),
      );
    } else card.append(el("p", "Autoavaliação ainda não submetida."));
    const edit = el("details");
    edit.append(el("summary", "Observação do professor e identificação"));
    const n = field("Nome para reunir os registos", r.name),
      g = field("Turma", r.group),
      note = field(
        "O que observaste e qual é o próximo passo?",
        r.teacher_note,
        true,
      );
    n.input.maxLength = 120;
    g.input.maxLength = 80;
    note.input.maxLength = 5000;
    const save = el("button", "Guardar observação");
    save.onclick = async () => {
      save.disabled = true;
      try {
        const updated = await api(`/api/learning/reports/${r.id}`, "PATCH", {
          name: n.input.value,
          group: g.input.value,
          teacher_note: note.input.value,
        });
        Object.assign(r, updated);
        status("Observação guardada.");
      } catch (e) {
        status(e.message, true);
      } finally {
        save.disabled = false;
      }
    };
    edit.append(n.label, g.label, note.label, save);
    card.append(edit);
    const download = el("a", "Descarregar relatório", "button");
    download.href = `/api/learning/reports/${r.id}/download`;
    card.append(download);
    $("reports").append(card);
  }
  if (!filtered.length)
    $("reports").append(
      el(
        "p",
        "Não há registos para estes filtros. Os ensaios de rascunhos ficam fora dos relatórios.",
      ),
    );
}
async function loadReports() {
  reports = await api("/api/learning/reports");
  render();
}
for (const id of [
  "filter-name",
  "filter-group",
  "filter-activity",
  "filter-from",
  "filter-to",
])
  $(id).addEventListener("input", render);
async function refreshReports() {
  $("refresh").disabled = true;
  $("report-load-status").textContent = "A atualizar os registos…";
  try {
    await loadReports();
    $("report-load-status").textContent = "";
  } catch (error) {
    $("report-load-status").textContent = "Não foi possível atualizar os registos. Tenta novamente em Atualizar. " + error.message;
  } finally {
    $("refresh").disabled = false;
  }
}
$("refresh").onclick = refreshReports;
$("support-summary-btn").onclick = async () => {
  const code = $("filter-activity").value;
  if (!code) { $("support-summary").textContent = "Escolhe uma atividade e as datas da aula para preparar o resumo."; return; }
  const params = new URLSearchParams({code, group:$("filter-group").value, name:$("filter-name").value,
    date_from:$("filter-from").value, date_to:$("filter-to").value});
  const root = $("support-summary");
  root.textContent = "A preparar o resumo…";
  try { PageCraftSupportSummary.render(root, await api('/api/learning/support-summary?'+params)); }
  catch(error) {root.textContent = error.message;}
};
$("logout").onclick = () => { location.href = "/logout"; };
(async () => {
  try {
    await api("/api/teacher-bootstrap");
    const info = await api("/api/access-info");
    publicOrigin = info.public_origin || location.origin;
    await Promise.all([refreshActivities(), refreshReports()]);
  } catch (e) {
    status(e.message, true);
  }
})();
