"""Individual voice, projected from the classroom's canonical event log."""

REFLECTION_LABELS = {
    'alone': 'Consegui com autonomia',
    'help': 'Consegui com ajuda',
    'practising': 'Quero praticar mais',
    'skip': 'Prefiro não responder',
}


def latest_reflections(events):
    """Keep revisions separate for each child and original work group."""
    latest = {}
    for record in events:
        if record.get('type') == 'individual_reflection':
            key = (record['payload']['source_work_group_id'], record['student_id'])
            latest[key] = record
    return list(latest.values())
