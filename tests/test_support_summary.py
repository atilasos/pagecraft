from server.support_summary import build_support_summary


def record(ref, type_, actor='pair-1', unit='u2', **payload):
    return {'ref': ref, 'type': type_, 'actor': actor, 'actor_label': actor, 'unit_id': unit,
            'at': '2026-10-22T10:00:00Z', 'payload': payload}


def test_summary_uses_distinct_groups_and_links_every_claim_to_records():
    events = [record('1', 'hint_presented', hint_id='h1', text='Apontem a zona.', activity_version='v1'),
              record('2', 'hint_feedback', hint_id='h1', usefulness='not_helped'),
              record('3', 'help_needed', note='Não encontramos o comando', help_request_id='help-1'),
              record('4', 'hint_presented', actor='pair-2', hint_id='h2', text='Apontem a zona.', activity_version='v1'),
              record('5', 'hint_feedback', actor='pair-2', hint_id='h2', usefulness='helped'),
              record('6', 'assessment_result', detail={'field':'plan', 'value':'Dois blocos'}),
              record('7', 'assessment_result', detail={'field':'plan', 'value':'Uma zona por animal', 'after_hint_id':'h1'})]
    summary = build_support_summary(events)
    assert summary['counts'] == {'presented':2, 'helped':1, 'not_helped':1, 'revisions':1, 'unresolved':1}
    assert summary['recurring'][0]['count'] == 2
    assert summary['changes'][0]['before'] == 'Dois blocos'
    assert summary['changes'][0]['evidence'] == ['1','6','7']
    for section in ['recurring','unhelpful','unresolved','changes','proposals']:
        for item in summary[section]:
            assert item['evidence']
            assert all(ref in summary['records'] for ref in item['evidence'])
    assert all(proposal['status'] == 'para revisão do professor' for proposal in summary['proposals'])


def test_help_is_only_resolved_explicitly_and_per_request():
    events = [record('1','help_needed',help_request_id='a'), record('2','help_needed',help_request_id='b'),
              record('3','ai_feedback',text='Uma pista'), record('4','assessment_result',detail={'field':'plan','value':'Sim'}),
              record('5','help_resolved',help_request_id='a')]
    summary=build_support_summary(events)
    assert summary['counts']['unresolved'] == 1
    assert summary['unresolved'][0]['evidence'] == ['2']
    assert not summary['recurring']


def test_missing_data_and_external_declarations_do_not_become_validations():
    summary=build_support_summary([record('1','assessment_result',detail={'field':'revisionResult','value':'Aumentámos o título','external_change':True})])
    assert summary['changes'][0]['kind'] == 'declared_external_change'
    assert summary['counts']['revisions'] == 0
    assert any('Falta indicação' in line for line in summary['limits'])
    assert any('aplicações externas' in line for line in summary['limits'])
    assert not build_support_summary([])['proposals']


def test_same_hint_feedback_is_latest_declaration_not_multiple_votes():
    events=[record('1','hint_presented',hint_id='hint',text='Uma pista'),
            record('2','hint_feedback',hint_id='hint',usefulness='not_helped'),
            record('3','hint_feedback',hint_id='hint',usefulness='helped')]
    result=build_support_summary(events)
    assert result['counts']['helped'] == 1
    assert result['counts']['not_helped'] == 0
    assert not result['unhelpful']


def test_versions_are_not_combined_into_a_recurring_problem():
    events=[record('1','hint_presented',actor='a',hint_id='h1',text='Uma pista',activity_version='v1'),
            record('2','hint_presented',actor='b',hint_id='h2',text='Uma pista nova',activity_version='v2')]
    assert not build_support_summary(events)['recurring']


def test_legacy_context_cannot_break_the_summary():
    events=[record('1','help_needed',actor='a',context='contexto antigo'),
            record('2','help_needed',actor='b',context='contexto antigo')]
    assert build_support_summary(events)['recurring'][0]['count']==2


def test_a_revision_to_zero_is_an_observed_change_in_a_maths_activity():
    summary=build_support_summary([record('1','assessment_result',detail={'field':'quantity','value':3}),
                                   record('2','assessment_result',detail={'field':'quantity','value':0})])
    assert summary['counts']['revisions']==1
    assert summary['changes'][0]['after']==0


def test_modal_acknowledgement_is_not_reported_as_helpfulness_or_understanding():
    summary=build_support_summary([record('1','hint_presented',hint_id='h',text='Uma pista',presentation='modal'),
                                   record('2','hint_acknowledged',hint_id='h',action='continue')])
    assert summary['counts']['presented']==1
    assert summary['counts']['helped']==0
    assert summary['counts']['revisions']==0
    assert '2' in summary['records']
    assert any('não comprova leitura' in limitation for limitation in summary['limits'])
