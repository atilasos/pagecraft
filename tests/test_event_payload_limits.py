"""As duas fronteiras medem os bytes do JSON que os hosts enviam."""
import json

import pytest
from pydantic import ValidationError

from server.api.classroom import EventsRequest
from server.api.learning import Event


def encoded_size(payload):
    return len(json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))


def payload_with_size(size, alphabet):
    payload = {'text': ''}
    remaining = size - encoded_size(payload)
    width = encoded_size({'text': alphabet}) - encoded_size(payload)
    payload['text'] = alphabet * (remaining // width) + 'x' * (remaining % width)
    assert encoded_size(payload) == size
    return payload


@pytest.mark.parametrize('alphabet', ['ação', '🦉', 'ã🦉', '\n"'])
@pytest.mark.parametrize('kind,limit', [('activity_state', 4096), ('hint_presented', 12000)])
def test_both_boundaries_accept_exact_utf8_limit_and_reject_the_next_byte(alphabet, kind, limit):
    event = {'id': 'unicode-limit', 'type': kind, 'payload': payload_with_size(limit, alphabet)}
    assert Event.model_validate(event).payload == event['payload']
    assert EventsRequest.model_validate({'events': [event]}).events[0]['payload'] == event['payload']
    event['payload']['text'] += 'x'
    for validate, value in [(Event.model_validate, event),
                            (EventsRequest.model_validate, {'events': [event]})]:
        with pytest.raises(ValidationError):
            validate(value)
