"use strict";
// A seleção mantém-se quando mudam os filtros. Os botões indicam o seu alcance.
window.PageCraftActivitySelection = class {
  constructor(root, activities, { eligible = () => true, renderItem, onchange = () => {} } = {}) {
    this.root = root;
    this.activities = activities;
    this.eligible = eligible;
    this.renderItem = renderItem;
    this.onchange = onchange;
    this.selected = new Set();
    const make = (tag, text) => {
      const node = document.createElement(tag);
      if (text) node.textContent = text;
      return node;
    };
    this.make = make;
    const filters = make("div");
    filters.className = "row";
    const label = (text, input) => {
      const node = make("label", text);
      node.append(input);
      filters.append(node);
    };
    this.search = make("input");
    this.search.type = "search";
    label("Procurar atividades", this.search);
    this.collection = make("select");
    this.collection.append(new Option("Todas", ""), new Option("28 palavras", "m28p"), new Option("Outras atividades", "other"));
    label("Coleção", this.collection);
    this.year = make("select");
    this.year.append(new Option("Todos", ""), ...[1, 2, 3, 4].map(n => new Option(`${n}.º ano`, String(n))));
    label("Ano", this.year);
    for (const input of [this.search, this.collection, this.year]) input.oninput = () => this.render();
    this.words = make("fieldset");
    this.words.className = "word-selection";
    const controls = make("div");
    controls.className = "row";
    this.all = make("button", "Selecionar resultados");
    const clear = make("button", "Limpar seleção");
    for (const button of [this.all, clear]) button.type = "button";
    this.all.onclick = () => { this.filtered().filter(this.eligible).forEach(a => this.selected.add(a.code)); this.render(); };
    clear.onclick = () => { this.selected.clear(); this.render(); };
    this.count = make("p");
    this.count.setAttribute("role", "status");
    controls.append(this.all, clear, this.count);
    this.list = make("div");
    this.list.className = "grid activity-selection-list";
    root.replaceChildren(filters, this.words, controls, this.list);
    this.render();
  }

  // Identifica a palavra M28P de um jogo; partilhado com a biblioteca do professor.
  static wordOf(activity) {
    const match = (activity.slug || "").match(/^m28p-v3-(.+)-(match|pairs|syllables|gap|recall|hunt)$/);
    return match ? { id: match[1], label: activity.title.split(" · ").pop() } : null;
  }

  word(activity) { return this.constructor.wordOf(activity); }

  filtered() {
    const query = this.search.value.trim().toLocaleLowerCase("pt");
    return this.activities.filter(a =>
      (!query || `${a.title} ${a.slug}`.toLocaleLowerCase("pt").includes(query)) &&
      (!this.year.value || String(a.year) === this.year.value) &&
      (!this.collection.value || (this.collection.value === "m28p") === !!this.word(a)));
  }

  chosen() { return this.activities.filter(a => this.selected.has(a.code)); }

  update(activities) {
    this.activities = activities;
    const eligible = new Set(activities.filter(this.eligible).map(a => a.code));
    this.selected.forEach(code => { if (!eligible.has(code)) this.selected.delete(code); });
    this.render();
  }

  render() {
    const make = this.make;
    const filtered = this.filtered();
    const words = new Map();
    for (const activity of filtered.filter(this.eligible)) {
      const word = this.word(activity);
      if (!word) continue;
      if (!words.has(word.id)) words.set(word.id, { ...word, codes: [] });
      words.get(word.id).codes.push(activity.code);
    }
    this.words.replaceChildren(make("legend", "Selecionar todos os jogos de uma palavra"));
    this.words.hidden = !words.size;
    for (const word of [...words.values()].sort((a, b) => a.label.localeCompare(b.label, "pt"))) {
      const label = make("label");
      const check = make("input");
      check.type = "checkbox";
      check.checked = word.codes.every(code => this.selected.has(code));
      check.indeterminate = !check.checked && word.codes.some(code => this.selected.has(code));
      check.onchange = () => {
        word.codes.forEach(code => check.checked ? this.selected.add(code) : this.selected.delete(code));
        this.render();
      };
      label.append(check, document.createTextNode(`${word.label} (${word.codes.length})`));
      this.words.append(label);
    }
    this.count.textContent = `${this.selected.size} selecionadas · ${filtered.length} nos filtros`;
    this.all.disabled = !filtered.some(this.eligible);
    this.list.replaceChildren();
    for (const activity of filtered) {
      const card = this.renderItem ? this.renderItem(activity) : make("article");
      card.classList.add("card");
      if (this.eligible(activity)) {
        const label = make("label");
        label.className = "selection-label";
        const check = make("input");
        check.type = "checkbox";
        check.checked = this.selected.has(activity.code);
        check.onchange = () => {
          check.checked ? this.selected.add(activity.code) : this.selected.delete(activity.code);
          // Refresh mixed word states without losing focus on the checkbox.
          const index = filtered.indexOf(activity);
          this.render();
          this.list.children[index]?.querySelector("input")?.focus({ preventScroll: true });
        };
        label.append(check, document.createTextNode(`Selecionar ${activity.title}`));
        card.prepend(label);
      }
      if (!this.renderItem) card.append(make("h3", activity.title), make("p", `${activity.year}.º ano · ${activity.duration} min`));
      this.list.append(card);
    }
    if (!filtered.length) this.list.append(make("p", "Não há atividades para estes filtros."));
    this.onchange(this.chosen());
  }
};
