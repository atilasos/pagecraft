/* Utilitários partilhados das páginas do professor: sessão e escaping. */

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[c]);
}

// Abrir uma página do painel renova a sessão se o pedido for loopback direto.
// O valor da credencial fica num cookie HttpOnly e nunca é entregue a este código.
const teacherBootstrap = fetch("/api/teacher-bootstrap").catch(() => null);

async function ensureTeacherSession() {
  await teacherBootstrap;
}

async function tfetch(url, opts = {}) {
  await ensureTeacherSession();
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

async function teacherEventSource(path) {
  await ensureTeacherSession();
  return new EventSource(path);
}
