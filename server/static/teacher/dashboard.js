/* Entrada pela turma, com ligações explícitas às sessões e aos registos. */
(() => {
  const select = document.getElementById("dashboard-class");
  const content = document.getElementById("overview-content");
  const status = document.getElementById("overview-status");
  const retry = document.getElementById("overview-retry");
  let classes = [];
  let sessions = [];
  let loading = false;

  function sessionRow(item) {
    const live = item.status === "live";
    const date = new Date(item.active_since || item.started_at).toLocaleDateString("pt-PT");
    return `<li class="overview-session">
      <div><span class="pill ${live ? "subject" : ""}">${live ? "Aula aberta" : "Trabalho guardado"}</span>
      <h3>${esc(item.activity_title || item.activity_slug)}</h3>
      <span class="muted">Última abertura: ${esc(date)}</span></div>
      <a class="button-link ${live ? "" : "ghost"}" href="/teacher/class.html?session=${encodeURIComponent(item.id)}">${live ? "Acompanhar aula" : "Continuar trabalho"}</a>
    </li>`;
  }

  function render() {
    const selected = classes.find(item => item.id === select.value);
    if (!selected) {
      content.innerHTML = `<p>Ainda não há turmas. Cria a primeira para começar uma aula e guardar o trabalho.</p>
        <a class="button-link" href="/teacher/class.html?view=classes">Criar a primeira turma</a>`;
      return;
    }
    const own = sessions.filter(item => item.class_id === selected.id);
    const live = own.filter(item => item.status === "live");
    const saved = own.filter(item => item.status !== "live");
    const classQuery = "class=" + encodeURIComponent(selected.id);
    content.innerHTML = `<p class="muted">${esc(selected.year)}.º ano · ${selected.students.length} alunos · ${live.length ? `${live.length} aula${live.length === 1 ? " aberta" : "s abertas"}` : "Sem aula aberta nesta turma"}</p>
      ${own.length ? `<ul class="plain overview-sessions">${[...live, ...saved.slice(0, 2)].map(sessionRow).join("")}</ul>` : "<p>Escolhe uma atividade para começar o primeiro trabalho desta turma.</p>"}
      ${saved.length > 2 ? `<details class="overview-history"><summary>Mais ${saved.length - 2} trabalhos guardados</summary><ul class="plain overview-sessions">${saved.slice(2).map(sessionRow).join("")}</ul></details>` : ""}
      <div class="button-line">
        <a class="button-link ${live.length ? "ghost" : ""}" href="/teacher/class.html?${classQuery}">Escolher atividade para esta turma</a>
        <a href="/teacher/class.html?${classQuery}&view=report">Registo da turma</a>
        <a href="/teacher/class.html?${classQuery}&view=classes">Ver turmas</a>
      </div>`;
  }

  async function refresh() {
    if (loading) return;
    loading = true;
    select.disabled = true;
    retry.hidden = true;
    status.textContent = "A consultar as aulas…";
    try {
      const responses = await Promise.all([tfetch("/api/classes"), tfetch("/api/sessions")]);
      if (responses.some(response => !response.ok)) throw new Error("Aulas indisponíveis");
      const selection = select.value;
      [classes, sessions] = await Promise.all(responses.map(response => response.json()));
      select.innerHTML = classes.map(item => `<option value="${esc(item.id)}">${esc(item.name)}</option>`).join("");
      const requested = new URLSearchParams(location.search).get("class");
      const candidate = [selection, requested, sessions.find(item => item.status === "live")?.class_id]
        .find(id => classes.some(item => item.id === id));
      if (candidate) select.value = candidate;
      select.disabled = !classes.length;
      select.dispatchEvent(new Event("change"));
      status.textContent = "Atualizado às " + new Date().toLocaleTimeString("pt-PT", {hour: "2-digit", minute: "2-digit"});
    } catch (error) {
      content.replaceChildren();
      status.textContent = "Não foi possível consultar as turmas e as aulas. Tenta novamente.";
      retry.hidden = false;
    } finally {
      loading = false;
    }
  }

  select.addEventListener("change", render);
  retry.addEventListener("click", refresh);
  window.addEventListener("pageshow", event => { if (event.persisted) refresh(); });
  document.addEventListener("visibilitychange", () => { if (!document.hidden) refresh(); });
  refresh();
})();
