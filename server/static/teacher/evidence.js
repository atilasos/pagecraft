/* Projeção de leitura do drawer. Nunca associa registos pela proximidade temporal. */
window.DrawerEvidence = (() => {
  const object = value => value && typeof value === 'object' && !Array.isArray(value) ? value : {};
  const payload = record => object(record.payload);
  const context = record => object(payload(record).context);
  const value = (record, key) => payload(record)[key] ?? context(record)[key];
  const unit = record => record.unit_id || value(record, 'unit_id');
  const actor = record => record.work_group_id ?
    JSON.stringify(['group', record.work_group_id, record.composition_version ?? null, [...(record.participant_ids || [])].sort()]) :
    record.student_id ? JSON.stringify(['student', record.student_id]) : null;

  function sameScope(left, right) {
    if (!actor(left) || actor(left) !== actor(right) || !unit(left) || unit(left) !== unit(right)) return false;
    // Missing metadata never cancels a conflicting task, activity or version.
    return ['activity', 'activity_version', 'task_id'].every(key => {
      const a = value(left, key), b = value(right, key);
      return a == null && b == null || a != null && a === b;
    });
  }

  function pendingHelp(events) {
    const pending = new Map();
    events.forEach((record, index) => {
      const author = actor(record);
      if (!author) return;
      const id = payload(record).help_request_id;
      if (record.type === 'help_needed') {
        pending.set(JSON.stringify([author, id || index]), {request: record, index});
      } else if (record.type === 'help_resolved') {
        for (const [key, entry] of pending) {
          // Older declarations resolved the author's pending help without an ID.
          if (actor(entry.request) === author && (!id || payload(entry.request).help_request_id === id)) pending.delete(key);
        }
      }
    });
    return [...pending.values()].reverse().map(({request, index}) => {
      const earlier = events.slice(0, index).reverse();
      const hintId = payload(request).hint_id;
      const hint = hintId ? earlier.find(record => record.type === 'hint_presented' &&
        payload(record).hint_id === hintId && sameScope(request, record)) : null;
      const feedback = hint ? [...events].reverse().find(record => record.type === 'hint_feedback' &&
        payload(record).hint_id === hintId && sameScope(hint, record) && events.indexOf(record) > events.indexOf(hint)) : null;
      const taskId = value(request, 'task_id');
      const response = taskId ? earlier.find(record => ['attempt', 'assessment_result', 'feedback_request'].includes(record.type) &&
        value(record, 'task_id') === taskId && sameScope(request, record)) : null;
      return {request, hint, feedback, response};
    });
  }

  const labels = {field: 'Campo', value: 'Resposta', note: 'Nota', detail: 'Contexto', question: 'Tarefa',
    answer: 'Resposta', reason: 'Justificação', before: 'Antes', after: 'Depois', observed: 'Observação',
    stage: 'Etapa', stage_objective: 'Objetivo da etapa', objective: 'Objetivo', criteria: 'Critérios',
    product: 'Produto declarado', task_description: 'Descrição da tarefa', observed_difficulties: 'Dificuldades registadas'};

  function readable(input, depth = 0) {
    if (input == null || input === '' || depth > 5) return '';
    if (Array.isArray(input)) return input.map(item => readable(item, depth + 1)).filter(Boolean).join(' · ');
    if (typeof input === 'object') return Object.entries(input).map(([key, item]) => {
      const text = readable(item, depth + 1);
      return text ? `${labels[key] || key.replace(/_/g, ' ')}: ${text}` : '';
    }).filter(Boolean).join(' · ');
    return typeof input === 'boolean' ? input ? 'Sim' : 'Não' : String(input);
  }

  function authors(record, students) {
    if (record.work_group_id) {
      const names = (record.participant_ids || []).map(id => students.get(id)?.display_name || id).join(' + ');
      return `Trabalho conjunto · ${names || 'autores não registados'}`;
    }
    return `Trabalho individual · ${students.get(record.student_id)?.display_name || record.student_id || 'autor não registado'}`;
  }

  function reference(record, students) {
    const date = new Date(record.ts);
    const parts = [Number.isNaN(date.getTime()) ? 'data não registada' : date.toLocaleString('pt-PT'),
      `registo #${record.seq ?? record.event_id ?? 'não registado'}`, authors(record, students)];
    if (unit(record)) parts.push(`etapa ${unit(record)}`);
    if (value(record, 'task_id')) parts.push(`tarefa ${value(record, 'task_id')}`);
    if (payload(record).help_request_id) parts.push(`pedido ${payload(record).help_request_id}`);
    if (payload(record).hint_id) parts.push(`pista ${payload(record).hint_id}`);
    if (value(record, 'activity_version')) parts.push(`versão ${value(record, 'activity_version')}`);
    return parts.join(' · ');
  }

  function describe(record) {
    const p = payload(record);
    switch (record.type) {
      case 'help_needed': return `pediu ajuda · ${readable(p.note) || 'nota não registada'}`;
      case 'help_resolved': return `declarou que já consegue continuar · ${readable(p.note) || 'nota não registada'}`;
      case 'hint_presented': return `pista apresentada · ${readable(p.text) || 'texto não registado'}`;
      case 'hint_feedback': return usefulness(record);
      case 'attempt': return `tentativa · ${p.correct ? 'resposta esperada' : 'resposta diferente da esperada'} · ${readable(p.detail) || 'contexto não registado'}`;
      case 'assessment_result': return `avaliação · ${readable(p.result) || 'resultado não registado'} · ${readable(p.detail) || 'contexto não registado'}`;
      case 'feedback_request': return `pediu feedback · Tarefa: ${readable(p.question) || 'não registado'} · Resposta: ${readable(p.answer) || 'não registado'}`;
      default: return null;
    }
  }

  function usefulness(record) {
    return ({helped: 'Ajudou, segundo o grupo', not_helped: 'Não ajudou, segundo o grupo'})[payload(record).usefulness] || 'não registado';
  }

  function renderHelp(root, events, students) {
    root.replaceChildren();
    const entries = pendingHelp(events);
    if (!entries.length) {
      root.textContent = 'Sem pedidos de ajuda pendentes neste percurso.';
      return;
    }
    for (const {request, hint, feedback, response} of entries) {
      const article = document.createElement('article');
      const heading = document.createElement('h4');
      heading.textContent = 'Pedido de ajuda pendente';
      const source = document.createElement('p');
      source.className = 'muted';
      source.textContent = reference(request, students);
      const fields = document.createElement('dl');
      const ownContext = context(request);
      const responsePayload = response ? payload(response) : {};
      function field(label, content, record = null) {
        const term = document.createElement('dt'), definition = document.createElement('dd');
        term.textContent = label;
        definition.textContent = readable(content) || 'não registado';
        if (record) {
          const ref = document.createElement('p');
          ref.className = 'muted';
          ref.textContent = reference(record, students);
          definition.appendChild(ref);
        }
        fields.append(term, definition);
      }
      field('Nota do pedido', payload(request).note);
      field('Etapa', ownContext.stage || unit(request));
      field('Tarefa', value(request, 'question') || ownContext.activity_characteristics?.task_description || responsePayload.question);
      const answer = value(request, 'answer');
      field('Resposta registada', answer ?? responsePayload.answer ?? object(responsePayload.detail).value,
        answer == null ? response : null);
      const details = Object.fromEntries(['objective', 'stage_objective', 'criteria', 'product', 'observed_difficulties']
        .filter(key => ownContext[key] != null).map(key => [key, ownContext[key]]));
      if (responsePayload.detail != null) details.detail = responsePayload.detail;
      field('Contexto registado', details, responsePayload.detail != null ? response : null);
      field('Pista associada', hint ? payload(hint).text : null, hint);
      field('Utilidade declarada', feedback ? usefulness(feedback) : null, feedback);
      article.append(heading, source, fields);
      root.appendChild(article);
    }
  }

  return Object.freeze({renderHelp, describe, authors, reference});
})();
