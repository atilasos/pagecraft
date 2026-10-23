import json

import pytest

from scripts import archive_m28p
from server.publish import build_catalog


def test_interrupted_archive_keeps_originals_and_rerun_repairs_catalog(tmp_path, monkeypatch):
    original = {'slug': 'menina', 'tags': ['m28p'], 'status': 'published'}
    folder = tmp_path / 'activities/menina'
    folder.mkdir(parents=True)
    (folder / 'meta.json').write_text(json.dumps(original))
    (folder / 'index.html').write_text('Trabalho preservado')
    real_save = archive_m28p.save_json

    def interrupted(path, value):
        if path.name == 'meta.json':
            raise OSError('Interrupção depois do inventário')
        real_save(path, value)

    monkeypatch.setattr(archive_m28p, 'save_json', interrupted)
    with pytest.raises(OSError):
        archive_m28p.archive(tmp_path, apply=True)
    manifest = tmp_path / 'docs/archives/m28p-2026-10-23.json'
    assert json.loads(manifest.read_text())['activities']['menina'] == original
    monkeypatch.setattr(archive_m28p, 'save_json', real_save)
    archive_m28p.archive(tmp_path, apply=True)
    # Simular um índice antigo depois de todos os metadados já arquivados.
    (tmp_path / 'catalog.json').write_text('{}')
    assert archive_m28p.archive(tmp_path, apply=True) == []
    assert json.loads((tmp_path / 'catalog.json').read_text()) == build_catalog(tmp_path)
    assert not build_catalog(tmp_path)['items']
    assert json.loads(manifest.read_text())['activities']['menina'] == original
    assert (folder / 'index.html').read_text() == 'Trabalho preservado'
