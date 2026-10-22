"""Síntese de apoio derivada de registos, sem inferir aprendizagem ou trabalho externo."""
from __future__ import annotations

import hashlib
from collections import defaultdict


def build_support_summary(events):
    """Recebe registos com ref/actor/actor_label/unit_id/type/payload e preserva as fontes."""
    records = {e['ref']: e for e in events if e['type'] in {'hint_presented', 'hint_feedback', 'hint_listened', 'help_needed', 'help_resolved', 'feedback_request', 'assessment_result', 'work_location'}}
    stages, unhelpful, pending, values = defaultdict(list), defaultdict(list), {}, {}
    hints, feedback, changes = {}, {}, []
    for e in events:
        p, actor, unit = e.get('payload') or {}, e['actor'], e.get('unit_id') or 'sem etapa'
        if e['type'] in {'hint_presented', 'feedback_request', 'help_needed'}:
            context = p.get('context') if isinstance(p.get('context'), dict) else p
            stages[(p.get('activity') or context.get('activity') or '', p.get('activity_version') or context.get('activity_version') or '', unit)].append(e)
        if e['type'] == 'hint_presented':
            hints[(actor, p.get('hint_id'))] = e
        elif e['type'] == 'hint_feedback':
            feedback[(actor, p.get('hint_id'))] = e
        elif e['type'] == 'help_needed':
            pending[(actor, p.get('help_request_id') or unit)] = e
        elif e['type'] == 'help_resolved':
            request_id = p.get('help_request_id')
            pending = {key: record for key, record in pending.items()
                       if key[0] != actor or (request_id and key[1] != request_id)}
        elif e['type'] == 'assessment_result':
            detail = p.get('detail') or {}
            if not isinstance(detail, dict) or not detail.get('field'):
                continue
            key = (actor, detail['field'])
            previous = values.get(key)
            value = detail.get('value')
            if previous and previous['payload']['detail'].get('value') not in (None, '') and value is not None and value != previous['payload']['detail'].get('value'):
                changes.append({'text': f"{e['actor_label']}: reviu a resposta «{detail.get('note') or detail['field']}» no PageCraft.",
                                'kind': 'pagecraft_revision', 'before': previous['payload']['detail']['value'], 'after': value,
                                'evidence': ([hints[(actor, detail['after_hint_id'])]['ref']] if (actor, detail.get('after_hint_id')) in hints else []) + [previous['ref'], e['ref']]})
            elif detail.get('external_change') is True and value:
                changes.append({'text': f"{e['actor_label']}: declarou uma alteração no produto, sem verificação do trabalho externo.",
                                'kind': 'declared_external_change', 'after': value, 'evidence': [e['ref']]})
            values[key] = e
    for key, e in feedback.items():
        if e['payload'].get('usefulness') == 'not_helped':
            hint = hints.get(key)
            text = hint['payload'].get('text', '') if hint else 'Pista sem apresentação registada'
            version = (hint['payload'].get('activity_version') if hint else None) or 'versão não indicada'
            unhelpful[(version, text)].append((e, hint))
    recurring = []
    for (activity, version, unit), rows in stages.items():
        actors = {e['actor'] for e in rows}
        if len(actors) < 2:
            continue
        title = unit
        for row in rows:
            context = row['payload'].get('context')
            if not isinstance(context, dict):
                context = row['payload']
            if context.get('stage'):
                title = context['stage']
                break
        recurring.append({'unit_id': unit, 'text': f'{title}: {len(actors)} grupos ou realizações pediram apoio.',
                          'count': len(actors), 'version': version, 'activity': activity, 'evidence': [e['ref'] for e in rows]})
    recurring.sort(key=lambda row: (-row['count'], row['unit_id']))
    rejected = [{'text': f'«{text}» recebeu indicação de que não ajudou em {len(rows)} percurso(s).',
                 'version': version, 'count': len(rows),
                 'evidence': [r['ref'] for row in rows for r in row if r]}
                for (version, text), rows in unhelpful.items()]
    rejected.sort(key=lambda row: -row['count'])
    unresolved = [{'text': f"{e['actor_label']} · {e.get('unit_id') or 'sem etapa'}: {e['payload'].get('note') or 'pediu ajuda'}",
                   'evidence': [e['ref']]} for e in pending.values()]
    proposals = []
    for row in recurring[:2]:
        proposals.append({'text': f"Rever a instrução de {row['unit_id']}: acrescentar um exemplo da primeira ação e ensaiar a sua interpretação com um grupo.",
                          'problem': row['text']+' Pode haver um obstáculo no guião.', 'evidence': row['evidence']})
    for row in rejected[:1]:
        proposals.append({'text': 'Preparar uma alternativa com uma pequena comparação ou pergunta que distinga a causa do bloqueio. Rever esta pista antes de a reutilizar.',
                          'problem': row['text'], 'evidence': row['evidence']})
    for proposal in proposals:
        proposal['id'] = hashlib.sha256('|'.join(proposal['evidence']).encode()).hexdigest()[:12]
        proposal['status'] = 'para revisão do professor'
    limits = ['Apresentação de uma pista, utilidade declarada e revisão de uma resposta são evidências diferentes.',
              'Não foram observados produtos em aplicações externas. Respostas conjuntas não demonstram compreensão individual.',
              'Menos pedidos de ajuda, isoladamente, não demonstram sucesso.']
    if not hints:
        limits.append('Não há pistas apresentadas nesta seleção. A ausência de registos não prova ausência de trabalho.')
    if not feedback:
        limits.append('Falta indicação dos alunos sobre a utilidade das pistas.')
    if not recurring:
        limits.append('Os registos não permitem identificar uma etapa com pedidos de vários grupos ou realizações.')
    if not changes:
        limits.append('Não há exemplos de alterações nas respostas nem declarações de revisão do produto nesta seleção.')
    return {'counts': {'presented': len(hints), 'helped': sum(e['payload'].get('usefulness') == 'helped' for e in feedback.values()),
                       'not_helped': sum(e['payload'].get('usefulness') == 'not_helped' for e in feedback.values()),
                       'revisions': sum(c['kind'] == 'pagecraft_revision' for c in changes), 'unresolved': len(unresolved)},
            'recurring': recurring, 'unhelpful': rejected[:5], 'unresolved': unresolved,
            'changes': changes[-3:], 'proposals': proposals, 'limits': limits, 'records': records}


def session_support_events(events, roster):
    labels = {sid: value.get('display_name', sid) for sid, value in roster.items()}
    for e in events:
        if e['type'] in {'work_group_joined', 'work_group_changed'}:
            labels[e['work_group_id']] = e['payload']['display_name']
    return [dict(ref=str(e['seq']), actor=e.get('work_group_id') or e.get('student_id') or 'session',
                 actor_label=labels.get(e.get('work_group_id') or e.get('student_id'), 'Sessão'),
                 unit_id=e.get('unit_id') or (e.get('payload') or {}).get('unit_id'),
                 type=e['type'], payload=e.get('payload') or {}, at=e.get('ts')) for e in events]


def realization_support_events(attempts):
    return [dict(ref=a['id']+':'+e['id'], actor=a['id'], actor_label=a['name'], unit_id=e.get('unitId'),
                 type=e['type'], payload=e.get('payload') or {}, at=e.get('received_at'))
            for a in attempts for e in a['events']]
