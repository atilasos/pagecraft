"""Transforma acontecimentos de trabalho em descrições para o professor."""
LABELS = {
    'correct': 'Resposta esperada', 'detail': 'Contexto', 'message': 'Descoberta',
    'result': 'Resultado observado', 'before': 'Antes', 'after': 'Depois',
    'textLength': 'Extensão do texto', 'fontSize': 'Tamanho da letra',
    'contrast': 'Contraste', 'reason': 'Justificação', 'scenario': 'Situação',
    'example': 'Exemplo', 'observed': 'Observação', 'audience': 'Destinatários',
    'action': 'Ação proposta', 'prediction': 'O que espera que aconteça',
    'slidePlan': 'Plano dos diapositivos', 'problem': 'Problema',
    'proposal': 'Proposta', 'invitation': 'Convite', 'workMode': 'Forma de trabalho',
    'suggestion': 'Sugestão recebida', 'revision': 'Revisão do trabalho',
    'language': 'Língua', 'level': 'Apoio', 'note': 'Pedido de ajuda',
    'what': 'Trabalho para partilhar', 'title': 'Atividade',
}
VALUES = {
    'pt': 'Português', 'en': 'Inglês', 'support': 'Com pistas',
    'intermediate': 'Passo a passo', 'challenge': 'Mais desafios',
    'short': 'Curto', 'long': 'Longo', 'soft': 'Suave', 'strong': 'Forte',
    'tap': 'Torneira a pingar', 'garden': 'Rega do recreio', 'own': 'Outra ideia',
    'canva': 'Canva', 'paper': 'Papel', 'seen': 'Observado', 'imagined': 'Imaginado',
}


def describe_evidence(event):
    lines = []

    def visit(value, label='', depth=0):
        if depth > 8:
            return
        if isinstance(value, dict):
            for key, item in value.items():
                child = LABELS.get(key, key.replace('_', ' '))
                # These dimensions have their own events; avoid repeating on every field.
                if key in {'language', 'level'} and event['type'] not in {'language_changed', 'level_changed'}:
                    continue
                visit(item, f'{label} · {child}' if label else child, depth+1)
        elif isinstance(value, list):
            for item in value:
                visit(item, label, depth+1)
        elif value is not None and value != '':
            text = ('Sim' if value else 'Não') if isinstance(value, bool) else VALUES.get(str(value), str(value))
            lines.append(f'{label}: {text}' if label else text)

    visit(event['payload'])
    return lines
