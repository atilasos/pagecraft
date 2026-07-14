/* Estúdio do professor: criação de jobs, progresso SSE, aprovação e catálogo. */

const PHASE_LABELS = {
  architect: "1/5 Pedagogia (Architect)",
  designer: "2/5 Design (Designer)",
  builder: "3/5 Construção (Builder)",
  proofreader: "4/5 Revisão de texto (Proofreader)",
  evaluator: "5/5 Avaliação (Evaluator)",
};
const PHASE_ORDER = ["architect", "designer", "builder", "proofreader", "evaluator"];

const jobsEl = document.getElementById("jobs");
const streams = new Map();

async function loadMeta() {
  const meta = await (await fetch("/api/meta")).json();
  const subject = document.getElementById("subject");
  subject.innerHTML = meta.subjects
    .map((s) => `<option value="${s}">${s}</option>`)
    .join("");
  subject.value = "Matemática";
  const year = document.getElementById("year");
  year.innerHTML = meta.years.map((y) => `<option value="${y}">${y}.º ano</option>`).join("");
  const maker = document.getElementById("maker");
  maker.innerHTML =
    '<option value="">— sem maker —</option>' +
    meta.makers.map((m) => `<option value="${m}">${m}</option>`).join("");
  const catalog = document.getElementById("catalog");
  catalog.innerHTML = (meta.activities || [])
    .slice()
    .reverse()
    .map(
      (a) =>
        `<li><a href="/activities/${a.slug}/" target="_blank" rel="noopener">${a.title || a.slug}</a>
         <span class="muted">· ${a.year ? a.year + ".º ano · " : ""}${a.duration || "?"} min</span></li>`
    )
    .join("") || '<li class="muted">Ainda não há atividades publicadas.</li>';
}

function jobCard(job) {
  let el = document.getElementById(`job-${job.id}`);
  if (!el) {
    el = document.createElement("div");
    el.className = "card";
    el.id = `job-${job.id}`;
    jobsEl.prepend(el);
  }
  const phaseIdx = PHASE_ORDER.indexOf(job.current_phase);
  const statusPill = {
    done: '<span class="pill ok">publicada</span>',
    awaiting_review: '<span class="pill warn">a aguardar a tua revisão</span>',
    failed: '<span class="pill warn">falhou</span>',
    queued: '<span class="pill">em fila</span>',
  }[job.status] || `<span class="pill">${PHASE_LABELS[job.current_phase] || job.status}</span>`;

  const running = !["done", "failed", "awaiting_review"].includes(job.status);
  el.innerHTML = `
    <strong>${job.topic}</strong> <span class="muted">· ${job.subject} · ${job.year}.º ano · ${job.duration} min</span>
    <p>${statusPill} ${job.iteration > 1 ? `<span class="pill">iteração ${job.iteration}</span>` : ""}</p>
    ${running ? `<progress max="5" value="${phaseIdx + 1}"></progress>` : ""}
    <p class="muted" id="job-${job.id}-log" aria-live="polite"></p>
    <p>
      ${job.artifacts && job.artifacts.html ? `<a href="/outputs/${job.slug}.html" target="_blank" rel="noopener">pré-visualizar</a> · ` : ""}
      ${job.status === "awaiting_review" ? `<button data-approve="${job.id}">Aprovar e publicar</button>` : ""}
      ${job.status === "done" ? `<a href="/activities/${job.slug}/" target="_blank" rel="noopener">abrir atividade publicada</a>` : ""}
      ${job.status === "failed" ? `<span class="feedback-warn">${job.error || "erro desconhecido"}</span>` : ""}
    </p>`;
}

function watchJob(job) {
  jobCard(job);
  if (["done", "failed"].includes(job.status) || streams.has(job.id)) return;
  const es = new EventSource(`/api/jobs/${job.id}/stream`);
  streams.set(job.id, es);
  es.onmessage = () => {};
  ["job_created", "knowledge_ready", "phase_started", "phase_done", "phase_retry", "validation", "repair", "resumed_artifact", "awaiting_review", "done", "failed"].forEach((type) => {
    es.addEventListener(type, async (ev) => {
      const data = JSON.parse(ev.data);
      const logEl = document.getElementById(`job-${job.id}-log`);
      if (logEl) logEl.textContent = describeEvent(type, data);
      const fresh = await (await fetch(`/api/jobs/${job.id}`)).json();
      jobCard(fresh);
      if (["done", "failed"].includes(type)) {
        es.close();
        streams.delete(job.id);
        loadMeta();
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
    const resp = await fetch("/api/jobs", {
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
  const id = ev.target?.dataset?.approve;
  if (!id) return;
  ev.target.disabled = true;
  const resp = await fetch(`/api/jobs/${id}/approve`, { method: "POST" });
  if (resp.ok) {
    jobCard(await resp.json());
    loadMeta();
  }
});

(async function init() {
  await loadMeta();
  const jobs = await (await fetch("/api/jobs")).json();
  jobs.slice(0, 10).reverse().forEach(watchJob);
})();
