"""Exercise the drawer's real JavaScript with the server's author declarations."""
import json
from pathlib import Path
import subprocess

import pytest

from server.classroom.event_types import SESSION_EVENT_TYPES


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = """
const fs = require('node:fs');
global.window = {};
eval(fs.readFileSync('server/static/teacher/evidence.js', 'utf8'));
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const students = new Map([['ana', {display_name:'Ana'}], ['bruno', {display_name:'Bruno'}]]);
const declarations = new Map(input.declarations.map(entry => [entry.name, entry]));
console.log(window.DrawerEvidence.reference(input.record, students, declarations));
"""


@pytest.mark.parametrize('record, expected', [
    ({'type': 'teacher_message', 'student_id': 'ana'}, 'Professor · Destinatário: Ana'),
    ({'type': 'teacher_message'}, 'Professor · Destinatários: turma'),
    ({'type': 'teacher_highlight', 'student_id': 'ana'}, 'Professor · Destinatário: Ana'),
    ({'type': 'teacher_highlight'}, 'Professor · Destinatários: turma'),
    ({'type': 'ai_feedback', 'student_id': 'ana'}, 'Assistente · Destinatário: Ana'),
    ({'type': 'ai_feedback', 'work_group_id': 'g', 'participant_ids': ['ana', 'bruno']},
     'Assistente · Destinatários: Ana + Bruno'),
    ({'type': 'joined', 'student_id': 'ana'}, 'Sessão'),
    ({'type': 'work_group_joined', 'work_group_id': 'g', 'participant_ids': ['ana', 'bruno']}, 'Sessão'),
    ({'type': 'session_closed'}, 'Sessão'),
    ({'type': 'attempt', 'student_id': 'ana'}, 'Trabalho individual · Ana'),
    ({'type': 'help_needed', 'work_group_id': 'g', 'participant_ids': ['ana', 'bruno']},
     'Trabalho conjunto · Ana + Bruno'),
    ({'type': 'individual_reflection', 'student_id': 'ana', 'payload': {'source_work_group_id': 'g'}},
     'Trabalho individual · Ana'),
    ({'type': 'attempt'}, 'Autor não registado'),
    ({'type': 'unknown', 'student_id': 'ana'}, 'Autor não registado'),
])
def test_reference_uses_declared_author_and_separates_recipient(record, expected):
    text = reference(record, SESSION_EVENT_TYPES.declaration())
    assert expected in text
    if not expected.startswith('Trabalho'):
        assert 'Trabalho individual' not in text
        assert 'Trabalho conjunto' not in text


@pytest.mark.parametrize('declarations', [
    [],
    [{'name': 'attempt', 'authors': ['activity', 'teacher']}],
    [{'name': 'attempt', 'authors': ['unknown']}],
])
def test_missing_or_ambiguous_declaration_does_not_invent_authorship(declarations):
    text = reference({'type': 'attempt', 'student_id': 'ana'}, declarations)
    assert 'Autor não registado' in text
    assert 'Trabalho' not in text


def reference(record, declarations):
    return subprocess.run(
        ['node', '-e', REFERENCE], cwd=ROOT, check=True, capture_output=True, text=True,
        input=json.dumps({'record': record, 'declarations': declarations}),
    ).stdout.strip()
