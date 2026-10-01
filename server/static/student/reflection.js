/* Individual reflection on the group's shared computer. The HTML never chooses authors. */
const groupReflection = (() => {
  const element = id => document.getElementById(id);
  const labels = {alone:'Consegui com autonomia', help:'Consegui com ajuda', practising:'Quero praticar mais', skip:'Prefiro não responder'};
  const icons = {alone:'✓', help:'🤝', practising:'↻', skip:'○'};
  let context = null, current = null, criteria = [], saved = {}, drafts = {}, archived = [], generation = 0, sending = false;
  const endpoint = () => `/api/sessions/${context.session}/groups/me/reflections`;
  const key = () => `pc-group-reflections:${context.session}:${context.group.device_id}`;
  const status = text => { element('reflection-status').textContent = text; };

  function persist() {
    try { sessionStorage.setItem(key(), JSON.stringify({drafts, archived})); }
    catch { status('Mantém esta página aberta para não perderes a reflexão por guardar.'); }
  }

  function reset() {
    generation++;
    context = null; current = null; criteria = []; saved = {}; drafts = {}; archived = []; sending = false;
    element('group-reflection').hidden = true;
    element('reflection-form').hidden = true;
    element('activity-frame').hidden = false;
    element('group-reflect-btn').hidden = true;
    element('pending-group-reflections').hidden = true;
  }

  async function mount() {
    reset();
    if (!state.workGroup) return;
    context = {session:state.session.id, group:state.workGroup};
    try {
      const stored = JSON.parse(sessionStorage.getItem(key()) || '{}');
      drafts = stored.drafts || stored;
      archived = stored.archived || [];
    } catch { drafts = {}; archived = []; }
    element('group-reflect-btn').hidden = false;
    renderPendingReflections();
  }

  async function read() {
    const version = generation;
    const response = await fetch(endpoint());
    if (version !== generation) return false;
    if (response.status === 401) { invalidateStudentIdentity(); return false; }
    if (!response.ok) throw new Error('Não foi possível abrir as reflexões. Tenta novamente.');
    const data = await response.json();
    if (version !== generation) return false;
    criteria = data.criteria;
    saved = data.reflections;
    renderPendingReflections();
    return true;
  }

  function isOldDraft(draft) {
    return !!draft && (draft.composition_version || draft.pending?.composition_version || 1) !== context.group.composition_version;
  }

  function renderPendingReflections() {
    const old = [...archived, ...Object.values(drafts).filter(isOldDraft)];
    element('pending-group-reflections').hidden = !old.length;
    const list = element('pending-reflection-list');
    list.replaceChildren();
    old.forEach(draft => {
      const detail = document.createElement('details');
      const summary = document.createElement('summary');
      summary.textContent = `${draft.owner_name || 'Um colega'} · ${draft.group_caption || 'Grupo anterior'} · Reflexão por guardar`;
      const answer = draft.pending || draft;
      const text = document.createElement('p');
      text.textContent = answer.skipped ? 'Preferiu não responder.' : [
        ...Object.entries(answer.answers || {}).map(([id,value]) => `${criteria.find(c=>c.id===id)?.pt || id}: ${labels[value] || value}`),
        answer.strategy ? `O que te ajudou? ${answer.strategy}` : '',
        answer.next_step ? `O que queres experimentar a seguir? ${answer.next_step}` : '',
      ].filter(Boolean).join(' · ') || 'Sem respostas.';
      detail.append(summary, text); list.append(detail);
    });
  }

  function participants() {
    const list = element('reflection-members');
    list.replaceChildren();
    context.group.members.forEach(member => {
      const button = document.createElement('button');
      const voice = saved[member.student_id]?.payload;
      const pending = drafts[member.student_id];
      const progress = pending ? 'Por guardar' : voice ? (voice.skipped ? 'Preferiu não responder' : 'Guardada') : 'Por responder';
      button.type = 'button';
      button.textContent = `${member.display_name} · ${progress}`;
      button.setAttribute('aria-pressed', String(current === member.student_id));
      button.disabled = sending;
      button.onclick = () => openChild(member.student_id);
      list.append(button);
    });
  }

  function capture() {
    if (!current || sending || drafts[current]?.pending) return;
    const answers = {};
    element('reflection-criteria').querySelectorAll('input:checked').forEach(input => {
      answers[input.name] = input.value;
    });
    drafts[current] = {
      composition_version: drafts[current]?.composition_version ?? context.group.composition_version,
      group_caption: drafts[current]?.group_caption || context.group.display_name,
      owner_name: context.group.members.find(member=>member.student_id===current).display_name,
      expected_revision: drafts[current]?.expected_revision ?? saved[current]?.payload.revision ?? 0,
      answers, strategy:element('reflection-strategy').value, next_step:element('reflection-next').value,
    };
    persist();
    renderPendingReflections();
    participants();
  }

  function openChild(studentId) {
    if (sending) return;
    current = studentId;
    const member = context.group.members.find(member => member.student_id === studentId);
    const draft = drafts[studentId];
    const voice = draft?.pending || draft || saved[studentId]?.payload || {};
    element('reflection-child').textContent = `A reflexão de ${member.display_name}`;
    element('reflection-form').hidden = false;
    const list = element('reflection-criteria');
    list.replaceChildren();
    criteria.forEach(criterion => {
      const fieldset = document.createElement('fieldset');
      const legend = document.createElement('legend');
      legend.textContent = criterion.pt;
      const hear = document.createElement('button');
      hear.type = 'button'; hear.className = 'ghost'; hear.textContent = 'Ouvir';
      hear.setAttribute('aria-label', `Ouvir: ${criterion.pt}`);
      hear.onclick = () => {
        if (!window.speechSynthesis) { status('Pede a um colega para ler contigo.'); return; }
        speechSynthesis.cancel();
        const speech = new SpeechSynthesisUtterance(criterion.pt); speech.lang = 'pt-PT'; speechSynthesis.speak(speech);
      };
      fieldset.append(legend, hear);
      const choices = document.createElement('div'); choices.className = 'reflection-choices';
      Object.entries(labels).forEach(([value, text]) => {
        const label = document.createElement('label');
        const input = document.createElement('input');
        input.type = 'radio'; input.name = criterion.id; input.value = value;
        input.checked = voice.answers?.[criterion.id] === value;
        const icon = document.createElement('span'); icon.textContent = icons[value]; icon.setAttribute('aria-hidden','true');
        label.append(input, icon, document.createTextNode(text));
        choices.append(label);
      });
      fieldset.append(choices); list.append(fieldset);
    });
    element('reflection-strategy').value = voice.strategy || '';
    element('reflection-next').value = voice.next_step || '';
    element('reflection-reload').hidden = !isOldDraft(draft);
    status(isOldDraft(draft) ? 'O professor alterou os participantes. Revê a versão guardada antes de responder no novo grupo.' : draft?.pending ? 'Há uma reflexão por guardar. Carrega em guardar para tentar novamente.' : '');
    lockForm(!!draft?.pending || isOldDraft(draft));
    participants();
    element('reflection-child').focus();
  }

  function lockForm(pending) {
    element('reflection-form').querySelectorAll('input, textarea').forEach(input => { input.disabled = sending || pending; });
    element('reflection-skip').disabled = sending || pending;
    element('reflection-save').disabled = sending || isOldDraft(drafts[current]);
    element('reflection-reload').disabled = sending;
    element('reflection-back').disabled = sending;
  }

  async function open() {
    if (!context) return;
    current = null;
    element('reflection-form').hidden = true;
    element('group-reflection').hidden = false;
    element('activity-frame').hidden = true;
    status('A abrir…');
    try {
      if (!await read()) return;
      participants(); status('');
      element('reflection-heading').focus();
      element('group-reflection').scrollIntoView({block:'start'});
    } catch (error) { status(error.message); }
  }

  async function save(skipped = false) {
    if (!context || !current || sending || isOldDraft(drafts[current])) return;
    if (!drafts[current]?.pending) {
      capture();
      const draft = drafts[current];
      draft.pending = {
        student_id:current, event_id:crypto.randomUUID(), expected_revision:draft.expected_revision, composition_version:context.group.composition_version,
        answers:skipped ? {} : draft.answers, strategy:skipped ? '' : draft.strategy,
        next_step:skipped ? '' : draft.next_step, skipped,
      };
      persist();
    }
    const studentId = current, version = generation, pending = drafts[studentId].pending;
    sending = true; lockForm(true); participants(); status('A guardar…');
    try {
      const response = await studentTransport.post(endpoint(), pending);
      if (version !== generation) return;
      if (!response) throw new Error('Não foi possível guardar. Mantém esta página aberta e tenta novamente.');
      if (!response.ok) {
        if ([400,404,409,422].includes(response.status)) element('reflection-reload').hidden = false;
        const error = await response.json();
        if (version !== generation) return;
        throw new Error(error.detail?.message || error.detail || 'Não foi possível guardar. Tenta novamente.');
      }
      const record = await response.json();
      if (version !== generation) return;
      saved[studentId] = record;
      delete drafts[studentId]; persist(); renderPendingReflections();
      current = null; element('reflection-form').hidden = true;
      status('Reflexão guardada. Agora pode responder outro colega.');
      element('reflection-heading').focus();
    } catch (error) {
      if (version === generation) status(error.message || 'Não foi possível guardar. Mantém esta página aberta e tenta novamente.');
    } finally {
      if (version === generation) { sending = false; lockForm(!!drafts[studentId]?.pending); participants(); }
    }
  }

  element('group-reflect-btn').onclick = open;
  element('reflection-form').addEventListener('input', capture);
  element('reflection-form').onsubmit = event => { event.preventDefault(); save(); };
  element('reflection-skip').onclick = () => save(true);
  element('reflection-back').onclick = () => {
    element('group-reflection').hidden = true;
    element('activity-frame').hidden = false;
    element('group-reflect-btn').focus();
  };
  element('reflection-reload').onclick = async () => {
    const studentId = current;
    try {
      if (!await read()) return;
      if (isOldDraft(drafts[studentId])) archived.push(drafts[studentId]);
      delete drafts[studentId]; persist(); renderPendingReflections(); openChild(studentId);
    } catch (error) { status(error.message); }
  };
  return {mount, reset, open};
})();
