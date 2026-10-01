"use strict";
const $ = (id) => document.getElementById(id);
let reports = [];
let publicOrigin = location.origin;
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
async function loadActivities() {
  const activities = await api("/api/learning/activities");
  $("activities").replaceChildren();
  $("filter-activity").replaceChildren(new Option("Todas", ""));
  for (const a of activities) {
    const card = el("article", undefined, "card"),
      state = el("span", a.published ? "Disponível" : "Rascunho", "tag");
    card.append(
      state,
      el("h3", a.title),
      el(
        "p",
        `${a.year}.º ano · ${a.duration} min · ${a.languages.includes("en") ? "PT/EN" : "Português"}`,
        "muted",
      ),
    );
    const link = el(
      "a",
      a.published ? "Abrir atividade" : "Pré-visualizar",
      "button",
    );
    link.href = (a.published ? publicOrigin : "") + "/" + a.code;
    link.target = "_blank";
    link.rel = "noopener";
    card.append(
      link,
      el(
        "p",
        (a.published ? "Endereço: " : "Endereço reservado: ") +
          publicOrigin +
          "/" +
          a.code,
        "muted",
      ),
    );
    if (!a.published) {
      const publish = el("button", "Aprovar e publicar", "primary");
      publish.onclick = async () => {
        if (
          !confirm(
            "Já reveste a atividade? Ao publicar, qualquer pessoa com o endereço pode abri-la.",
          )
        )
          return;
        publish.disabled = true;
        try {
          await api(`/api/learning/activities/${a.code}/publish`, "POST");
          await loadActivities();
          status("Atividade publicada.");
        } catch (e) {
          status(e.message, true);
          publish.disabled = false;
        }
      };
      card.append(publish);
    }
    $("activities").append(card);
    $("filter-activity").append(new Option(a.title, a.code));
  }
  if (!activities.length)
    $("activities").append(
      el(
        "p",
        "Ainda não há atividades registadas. A skill PageCraft prepara aqui os rascunhos para revisão.",
      ),
    );
}
function field(title, value, multi = false) {
  const label = el("label", title),
    input = el(multi ? "textarea" : "input");
  input.value = value || "";
  label.append(input);
  return { label, input };
}
function render() {
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
$("refresh").onclick = () =>
  loadReports().catch((e) => status(e.message, true));
$("logout").onclick = () => { location.href = "/logout"; };
(async () => {
  try {
    await api("/api/teacher-bootstrap");
    const info = await api("/api/access-info");
    publicOrigin = info.public_origin || location.origin;
    await loadActivities();
    await loadReports();
  } catch (e) {
    status(e.message, true);
  }
})();
