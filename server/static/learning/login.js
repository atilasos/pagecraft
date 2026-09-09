"use strict";
document.getElementById("login").onsubmit = async (e) => {
  e.preventDefault();
  e.submitter.disabled = true;
  try {
    const r = await fetch("/api/teacher-login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code: document.getElementById("code").value }),
    });
    if (!r.ok)
      throw Error(
        "Código inválido ou expirado. Gera um novo no computador do PageCraft.",
      );
    location.href = "/teacher/activities.html";
  } catch (e) {
    document.getElementById("status").textContent = e.message;
  } finally {
    e.submitter.disabled = false;
  }
};
