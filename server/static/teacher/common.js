/* Utilitários partilhados das páginas do professor: autenticação e escaping. */

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[c]);
}

async function teacherToken() {
  let token = localStorage.getItem("pagecraft_teacher_token") || "";
  if (!token) {
    // só funciona no browser da máquina do professor (loopback)
    const resp = await fetch("/api/teacher-token");
    if (resp.ok) {
      token = (await resp.json()).token;
      localStorage.setItem("pagecraft_teacher_token", token);
    }
  }
  return token;
}

async function tfetch(url, opts = {}) {
  const token = await teacherToken();
  const headers = { ...(opts.headers || {}), "x-teacher-token": token };
  const resp = await fetch(url, { ...opts, headers });
  if (resp.status === 401) {
    localStorage.removeItem("pagecraft_teacher_token");
    document.body.insertAdjacentHTML(
      "afterbegin",
      '<p class="feedback-warn" style="margin:1rem">Sessão de professor inválida. ' +
        "Abre esta página no computador do professor (localhost) para renovar o acesso.</p>"
    );
  }
  return resp;
}

async function teacherStreamUrl(path) {
  const token = await teacherToken();
  const sep = path.includes("?") ? "&" : "?";
  return `${path}${sep}role=teacher&teacher_token=${encodeURIComponent(token)}`;
}
