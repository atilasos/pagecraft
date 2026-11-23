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


def _activity(root, slug, tags):
    folder = root / 'activities' / slug
    folder.mkdir(parents=True)
    (folder / 'meta.json').write_text(json.dumps({'slug': slug, 'title': slug, 'tags': tags, 'status': 'published'}))
    (folder / 'index.html').write_text('Conteúdo ' + slug)


def test_v3_archive_keeps_cycle_and_other_collections_and_feeds_archive_zone(tmp_path):
    from server.publish import build_archive

    _activity(tmp_path, 'm28p-v3-uva-gap', ['m28p', 'm28p-v3'])
    _activity(tmp_path, 'm28p-ciclo-uva-discover', ['m28p', 'm28p-v3'])
    _activity(tmp_path, 'canva-agua-4ano', ['canva'])
    # O arquivo de 23/10 nunca apanha a v3 nem o ciclo, mesmo repetido.
    assert archive_m28p.archive(tmp_path, apply=True) == []
    assert archive_m28p.archive(tmp_path, apply=True, collection='m28p-v3-2026-11-23') == ['m28p-v3-uva-gap']
    catalog = json.loads((tmp_path / 'catalog.json').read_text())
    assert [item['slug'] for item in catalog['items']] == ['canva-agua-4ano', 'm28p-ciclo-uva-discover']
    zone = json.loads((tmp_path / 'archive.json').read_text())
    assert zone == build_archive(tmp_path)
    [item] = zone['items']
    assert item['slug'] == 'm28p-v3-uva-gap' and item['url'] == './activities/m28p-v3-uva-gap/'
    assert item['archivedAt'] == '2026-11-23' and 'ciclo completo' in item['archiveReason']
    assert item['archiveCollection'].startswith('Coleção v3')
    assert (tmp_path / 'activities/m28p-v3-uva-gap/index.html').read_text() == 'Conteúdo m28p-v3-uva-gap'
    manifest = json.loads((tmp_path / 'docs/archives/m28p-v3-2026-11-23.json').read_text())
    assert manifest['activities']['m28p-v3-uva-gap']['status'] == 'published'
    assert archive_m28p.archive(tmp_path, apply=True, collection='m28p-v3-2026-11-23') == []
