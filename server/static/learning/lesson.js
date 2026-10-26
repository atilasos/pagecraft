"use strict";
const $ = id => document.getElementById(id);
const code = location.pathname.split("/").pop().toUpperCase();
const selectedStudent = new URLSearchParams(location.search).get("aluno");
function el(tag, text) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  return node;
}
async function api(path) {
  const response = await fetch(path);
  const result = await response.json();
  if (!response.ok) throw Error(typeof result.detail === "string" ? result.detail : "Não foi possível abrir o roteiro. Pede ajuda ao professor.");
  return result;
}
async function load() {
  $("retry").hidden = true;
  $("entry").hidden = $("work").hidden = true;
  $("status").textContent = "A abrir o roteiro…";
  try {
    const data = await api(`/api/learning/lessons/${code}/${selectedStudent ? `students/${encodeURIComponent(selectedStudent)}` : "entry"}`);
    $("title").textContent = data.title;
    $("class-name").textContent = data.class_name;
    document.body.dataset.year = String(data.year);
    $("status").textContent = "";
    if (!selectedStudent) {
      $("names").replaceChildren();
      for (const student of data.students) {
        const link = el("a", student.display_name);
        link.className = "button primary";
        link.href = `/aula/${code}?aluno=${student.id}`;
        $("names").append(link);
      }
      $("entry").hidden = false;
      return;
    }
    $("change-name").hidden = false;
    $("change-name").href = `/aula/${code}`;
    $("greeting").textContent = `Olá, ${data.student.display_name}!`;
    $("activities").replaceChildren();
    for (const activity of data.activities) {
      const card = el("article");
      card.className = "card";
      const link = el("a", "Começar");
      link.className = "button primary";
      link.href = `/${activity.code}?aula=${code}&aluno=${data.student.id}`;
      card.append(el("h3", activity.title), el("p", `${activity.duration} minutos`), link);
      $("activities").append(card);
    }
    if (!data.activities.length) $("activities").append(el("p", "Ainda não tens atividades neste roteiro. Pede ajuda ao professor."));
    $("work").hidden = false;
  } catch (error) {
    $("status").textContent = error.message;
    $("retry").hidden = false;
  }
}
$("retry").onclick = load;
load();
