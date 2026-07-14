from server.api.catalog import _parse_year


def test_parse_year_formats():
    assert _parse_year(3) == 3
    assert _parse_year("3") == 3
    assert _parse_year("3.º ano") == 3
    assert _parse_year("1.º ano (6-7 anos)") == 1
    assert _parse_year("9-10 anos (4.º ano do 1.º CEB)") == 4
    assert _parse_year("8-9 anos (3.º ano)") == 3


def test_parse_year_rejects_ages():
    assert _parse_year("6-8 anos, ajustável") is None
    assert _parse_year("3-4 anos") is None
    assert _parse_year("") is None
    assert _parse_year(None) is None
    assert _parse_year(7) is None
