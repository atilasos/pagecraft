/* Estúdio do professor: criação de jobs, progresso SSE, aprovação e catálogo. */

const PHASE_LABELS = {
  architect: "1/5 Plano pedagógico",
  designer: "2/5 Organização visual",
  builder: "3/5 Construção da atividade",
  proofreader: "4/5 Revisão do texto",
  evaluator: "5/5 Verificação final",
};
const PHASE_ORDER = ["architect", "designer", "builder", "proofreader", "evaluator"];

const jobsEl = document.getElementById("jobs");
const streams = new Map();
const jobStates = new Map();
let catalogActivities = [];
let catalogLoaded = false;
let catalogLimit = 8;

async function loadMeta() {
  const response = await tfetch("/api/meta");
  if (!response.ok) throw new Error("Catálogo indisponível");
  const meta = await response.json();
  const subject = document.getElementById("subject");
  if (!subject.options.length) {
    subject.replaceChildren(...meta.subjects.map(value => new Option(value, value)));
    subject.value = "Matemática";
    document.getElementById("year").replaceChildren(...meta.years.map(value => new Option(`${value}.º ano`, value)));
    const names = {minecraft: "Minecraft", lego: "LEGO", "3d-print": "Impressão 3D", robotics: "Robótica", whiteboard: "Quadro interativo", unplugged: "Sem computador"};
    document.getElementById("maker").replaceChildren(new Option("Sem desafio maker", ""),
      ...meta.makers.map(value => new Option(names[value] || value, value)));
  }
  catalogActivities = meta.activities || [];
  catalogLoaded = true;
  const filter = document.getElementById("catalog-subject");
  const selected = filter.value;
  filter.replaceChildren(new Option("Todas", ""), ...[...new Set(catalogActivities.map(a => a.subject).filter(Boolean))]
    .sort((a, b) => a.localeCompare(b, "pt")).map(value => new Option(value, value)));
  filter.value = selected;
  document.getElementById("submit-btn").disabled = false;
  renderCatalog();
}

function renderCatalog() {
  if (!catalogLoaded) return;
  const search = value => String(value || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("pt");
  const query = search(document.getElementById("catalog-search").value.trim());
  const year = document.getElementById("catalog-year").value;
  const subject = document.getElementById("catalog-subject").value;
  const matches = catalogActivities.filter(a => (!year || a.years.includes(Number(year))) &&
    (!subject || a.subject === subject) && (!query || search(`${a.title} ${a.subject} ${(a.tags || []).join(" ")}`).includes(query)));
  const classId = document.getElementById("dashboard-class").value;
  document.getElementById("catalog").innerHTML = matches.slice(0, catalogLimit).map(a => {
    const params = new URLSearchParams({activity: a.slug});
    if (classId && !document.getElementById("dashboard-class").disabled) params.set("class", classId);
    return `<li class="catalog-entry"><div><h3><a href="/activities/${encodeURIComponent(a.slug)}/" target="_blank" rel="noopener">${esc(a.title || a.slug)}</a></h3>
      <span class="muted">${esc(a.subject || "Disciplina por indicar")} · ${esc(catalogYearLabel(a))}${a.duration ? ` · ${esc(a.duration)} min` : ""}</span></div>
      <a class="button-link ghost" href="/teacher/class.html?${esc(params.toString())}">Preparar aula</a></li>`;
  }).join("") || '<li class="muted">Nenhuma atividade corresponde aos filtros.</li>';
  document.getElementById("catalog-status").textContent = `${Math.min(matches.length, catalogLimit)} de ${matches.length} atividades`;
  document.getElementById("catalog-more").hidden = matches.length <= catalogLimit;
}
for (const id of ["catalog-search", "catalog-year", "catalog-subject"]) {
  document.getElementById(id).addEventListener("input", () => { catalogLimit = 8; renderCatalog(); });
}
document.getElementById("catalog-more").onclick = () => { catalogLimit += 8; renderCatalog(); };
document.getElementById("dashboard-class").addEventListener("change", renderCatalog);
async function refreshMeta() {
  document.getElementById("meta-retry").hidden = true;
  try { await loadMeta(); }
  catch (error) {
    document.getElementById("catalog-status").textContent = "Não foi possível carregar o catálogo. Tenta novamente.";
    document.getElementById("form-status").textContent = "Não foi possível carregar as opções. Tenta novamente no catálogo.";
    document.getElementById("meta-retry").hidden = false;
  }
}
document.getElementById("meta-retry").onclick = refreshMeta;

function orderJobs() {
  const priority = job => ({awaiting_review: 0, failed: 1, done: 3})[job.status] ?? 2;
  const jobs = [...jobStates.values()].sort((a, b) => priority(a) - priority(b) || (b.created_at || "").localeCompare(a.created_at || ""));
  for (const job of jobs) {
    const target = job.status === "done" ? document.getElementById("published-jobs") : jobsEl;
    target.appendChild(document.getElementById(`job-${job.id}`));
  }
  const review = jobs.filter(job => job.status === "awaiting_review").length;
  const failed = jobs.filter(job => job.status === "failed").length;
  const published = jobs.filter(job => job.status === "done").length;
  const running = jobs.length - review - failed - published;
  document.getElementById("jobs-summary").textContent = review + failed + running
    ? `${review} por rever · ${running} em preparação · ${failed} com erro`
    : "Não há atividades em preparação ou à espera de revisão.";
  document.getElementById("job-history").hidden = published === 0;
  document.getElementById("job-history-label").textContent = `Atividades já publicadas (${published})`;
}

function jobCard(job) {
  jobStates.set(job.id, job);
  let el = document.getElementById(`job-${job.id}`);
  if (!el) {
    el = document.createElement("div");
    el.className = "card";
    el.id = `job-${job.id}`;
    jobsEl.prepend(el);
  }
  const previousLog = el.querySelector('[aria-live]')?.textContent || "";
  const phaseIdx = PHASE_ORDER.indexOf(job.current_phase);
  const statusPill = {
    done: '<span class="pill ok">publicada</span>',
    awaiting_review: '<span class="pill warn">a aguardar a tua revisão</span>',
    failed: '<span class="pill warn">falhou</span>',
    queued: '<span class="pill">em fila</span>',
  }[job.status] || `<span class="pill">${esc(PHASE_LABELS[job.current_phase] || job.status)}</span>`;

  const running = !["done", "failed", "awaiting_review"].includes(job.status);
  const canReview = job.artifact_version === 1 && job.review && job.preview_url;
  const canOverride = job.status === "failed" && canReview;
  el.innerHTML = `
    <strong>${esc(job.topic)}</strong> <span class="muted">· ${esc(job.subject)} · ${esc(job.year)}.º ano · ${esc(job.duration)} min</span>
    <p>${statusPill} ${job.iteration > 1 ? `<span class="pill">iteração ${esc(job.iteration)}</span>` : ""}</p>
    ${running ? `<progress aria-label="Preparação da atividade" max="5" value="${phaseIdx + 1}"></progress>` : ""}
    <p class="muted" id="job-${esc(job.id)}-log" aria-live="polite">${esc(previousLog)}</p>
    <p>
      ${canReview ? `<a href="${esc(job.preview_url)}" target="_blank" rel="noopener">pré-visualizar</a> · ` : ""}
      ${job.status === "awaiting_review" && canReview ? `<button data-approve="${esc(job.id)}" data-review="${esc(job.review.id)}">Aprovar e publicar</button>` : ""}
      ${canOverride ? `<button class="ghost" data-approve="${esc(job.id)}" data-review="${esc(job.review.id)}" data-override="true">Publicar mesmo assim (decisão do professor)</button>` : ""}
      ${job.status === "done" ? `<a href="/activities/${encodeURIComponent(job.slug)}/" target="_blank" rel="noopener">abrir atividade publicada</a>` : ""}
      ${job.status === "failed" ? `<span class="feedback-warn">${esc(job.error || "erro desconhecido")}</span>` : ""}
    </p>`;
  orderJobs();
}

async function watchJob(job) {
  jobCard(job);
  if (["done", "failed", "awaiting_review"].includes(job.status) || streams.has(job.id)) return;
  const es = new EventSource(`/api/jobs/${job.id}/stream`);
  streams.set(job.id, es);
  es.onmessage = () => {};
  ["job_created", "knowledge_ready", "phase_started", "phase_done", "phase_retry", "validation", "repair", "resumed_artifact", "awaiting_review", "done", "failed"].forEach((type) => {
    es.addEventListener(type, async (ev) => {
      const data = JSON.parse(ev.data);
      try {
        const response = await tfetch(`/api/jobs/${job.id}`);
        if (!response.ok) throw new Error("Progresso indisponível");
        jobCard(await response.json());
        document.getElementById(`job-${job.id}-log`).textContent = describeEvent(type, data);
        if (["done", "failed", "awaiting_review"].includes(type)) {
          es.close();
          streams.delete(job.id);
          if (type === "done") refreshMeta();
        }
      } catch (error) {
        document.getElementById(`job-${job.id}-log`).textContent = "Não foi possível atualizar o progresso. Atualiza a página para tentar novamente.";
      }
    });
  });
  es.onerror = () => {
    /* EventSource tenta reconectar sozinho */
  };
}

function describeEvent(type, data) {
  const p = data.payload || {};
  switch (type) {
    case "knowledge_ready":
      return p.ae_found
        ? `Aprendizagens Essenciais encontradas: ${p.ae_citation || ""}`
        : "Sem documento AE local para esta disciplina/ano.";
    case "phase_started":
      return `${PHASE_LABELS[p.phase] || p.phase} em curso…`;
    case "phase_done":
      return `${PHASE_LABELS[p.phase] || p.phase} concluída.`;
    case "phase_retry":
      return `A repetir ${p.phase} (tentativa ${p.attempt})…`;
    case "repair":
      return `A avaliação pediu correções, a reparar (iteração ${p.iteration})…`;
    case "validation":
      return p.passed ? "Verificação técnica: ok." : `Verificação técnica: ${(p.errors || []).join("; ")}`;
    case "awaiting_review":
      return "Pronta para a tua revisão.";
    case "done":
      return "Publicada no catálogo.";
    case "failed":
      return `Falhou: ${p.error || ""}`;
    default:
      return type;
  }
}

document.getElementById("job-form").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const form = ev.target;
  const status = document.getElementById("form-status");
  const btn = document.getElementById("submit-btn");
  btn.disabled = true;
  status.textContent = "A lançar geração…";
  try {
    const body = {
      topic: form.topic.value,
      subject: form.subject.value,
      year: Number(form.year.value),
      duration: Number(form.duration.value),
      maker: form.maker.value || null,
    };
    const resp = await tfetch("/api/jobs", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!resp.ok) throw new Error(await resp.text());
    watchJob(await resp.json());
    status.textContent = "Geração lançada.";
    form.topic.value = "";
  } catch (err) {
    status.textContent = `Não foi possível lançar: ${err.message}`;
  } finally {
    btn.disabled = false;
  }
});

document.addEventListener("click", async (ev) => {
  const button = ev.target.closest("[data-approve]");
  if (!button) return;
  const id = button.dataset.approve;
  const override = button.dataset.override === "true";
  button.disabled = true;
  try {
    const resp = await tfetch(`/api/jobs/${id}/approve${override ? "?override=true" : ""}`, {
      method: "POST", headers: {"content-type": "application/json"},
      body: JSON.stringify({review_id: button.dataset.review}),
    });
    const result = await resp.json().catch(() => ({}));
    if (!resp.ok) throw new Error(result.detail || "Não foi possível publicar esta revisão.");
    jobCard(result);
    document.getElementById("jobs-feedback").textContent = "Atividade publicada. Podes encontrá-la no catálogo e no histórico.";
    document.getElementById("jobs-title").focus();
    refreshMeta();
  } catch (error) {
    document.getElementById(`job-${id}-log`).textContent = error.message || "Não foi possível publicar. Tenta novamente.";
    button.disabled = false;
  }
});

async function loadJobs() {
  document.getElementById("jobs-retry").hidden = true;
  try {
    const resp = await tfetch("/api/jobs");
    if (!resp.ok) throw new Error("Geração indisponível");
    const jobs = await resp.json();
    jobs.forEach(watchJob);
    orderJobs();
    document.getElementById("jobs-feedback").textContent = "";
  } catch (error) {
    document.getElementById("jobs-summary").textContent = "Não foi possível consultar as atividades em preparação.";
    document.getElementById("jobs-retry").hidden = false;
  }
}
document.getElementById("jobs-retry").onclick = loadJobs;
refreshMeta();
loadJobs();
