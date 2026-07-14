from pathlib import Path

import pytest

from server.knowledge.ae import AEClient, _slugify
from server.knowledge.wiki import WikiClient

VAULT = Path.home() / "vault"

pytestmark = pytest.mark.skipif(not VAULT.exists(), reason="vault não disponível nesta máquina")


def test_slugify():
    assert _slugify("Estudo do Meio") == "estudo-do-meio"
    assert _slugify("Matemática") == "matematica"
    assert _slugify("Português") == "portugues"


def test_ae_find_matematica_3_ano():
    client = AEClient(VAULT)
    doc = client.find("Matemática", 3)
    assert doc is not None
    assert doc.year == 3
    assert "APRENDIZAGENS ESSENCIAIS" in doc.body.upper()
    assert doc.source_url.startswith("http")


def test_ae_context_missing_subject_returns_empty():
    client = AEClient(VAULT)
    excerpt, citation = client.context_for("Astrofísica Quântica", 3)
    assert excerpt == ""
    assert citation == ""


def test_ae_list_subjects_includes_core():
    subjects = AEClient(VAULT).list_subjects()
    joined = " ".join(subjects)
    assert "matematica" in joined
    assert "portugues" in joined


async def test_wiki_read_mem_page():
    client = WikiClient(VAULT)
    assert client.available
    body = await client.read_page("Plano Individual de Trabalho")
    assert "PIT" in body or "trabalho" in body.lower()


async def test_wiki_search_pit():
    client = WikiClient(VAULT)
    out = await client.search("plano individual de trabalho")
    assert out.strip() != ""
