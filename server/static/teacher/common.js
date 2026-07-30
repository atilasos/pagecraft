/* Utilitários partilhados das páginas do professor: sessão e escaping. */

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[c]);
}

async function tfetch(url, opts = {}) {
  const resp = await fetch(url, opts);
  if (resp.status === 401) {
    document.body.insertAdjacentHTML(
      "afterbegin",
      '<p class="feedback-warn" style="margin:1rem">Sessão de professor inválida. ' +
        "Abre esta página no computador do professor (localhost) para renovar o acesso.</p>"
    );
  }
  return resp;
}
