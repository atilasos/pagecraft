from pathlib import Path

import httpx
import pytest

from server.knowledge.ae import AEClient, _slugify
from server.knowledge.wiki import WikiAPIError, WikiClient

VAULT = Path.home() / "obsidian-vault"

requires_vault = pytest.mark.skipif(
    not VAULT.exists(), reason="vault não disponível nesta máquina"
)


def test_slugify():
    assert _slugify("Estudo do Meio") == "estudo-do-meio"
    assert _slugify("Matemática") == "matematica"
    assert _slugify("Português") == "portugues"


@requires_vault
def test_ae_find_matematica_3_ano():
    client = AEClient(VAULT)
    doc = client.find("Matemática", 3)
    assert doc is not None
    assert doc.year == 3
    assert "APRENDIZAGENS ESSENCIAIS" in doc.body.upper()
    assert doc.source_url.startswith("http")


@requires_vault
def test_ae_context_missing_subject_returns_empty():
    client = AEClient(VAULT)
    excerpt, citation = client.context_for("Astrofísica Quântica", 3)
    assert excerpt == ""
    assert citation == ""


@requires_vault
def test_ae_list_subjects_includes_core():
    subjects = AEClient(VAULT).list_subjects()
    joined = " ".join(subjects)
    assert "matematica" in joined
    assert "portugues" in joined


@requires_vault
async def test_wiki_read_mem_page():
    client = WikiClient(VAULT)
    assert await client.probe()
    body = await client.read_page("Plano Individual de Trabalho")
    assert "PIT" in body or "trabalho" in body.lower()


@requires_vault
async def test_wiki_search_pit():
    client = WikiClient(VAULT)
    out = await client.search("plano individual de trabalho")
    assert out.strip() != ""


# ---- testes independentes do vault (API Sebenta simulada) ----


def _client_without_vault() -> WikiClient:
    return WikiClient(Path("/nao-existe"), api_url="http://127.0.0.1:1")


async def test_topic_context_formats_pages(monkeypatch):
    client = _client_without_vault()

    async def fake_search_pages(query, *, limit=8):
        return [
            {"title": "Avaliação Formativa", "summary": "x"},
            {"title": "Método das 28 Palavras", "summary": "y"},
        ]

    async def fake_read_page(title):
        return f"corpo de {title}"

    monkeypatch.setattr(client, "search_pages", fake_search_pages)
    monkeypatch.setattr(client, "read_page", fake_read_page)
    out = await client.topic_context("leitura global", "Português")
    # "Avaliação Formativa" é página MEM nuclear — excluída para não duplicar
    assert "## Avaliação Formativa" not in out
    assert "## Método das 28 Palavras" in out
    assert "corpo de Método das 28 Palavras" in out


async def test_topic_context_empty_query_returns_empty():
    client = _client_without_vault()
    assert await client.topic_context("", "") == ""


async def test_search_pages_returns_empty_when_api_down():
    client = _client_without_vault()
    assert await client.search_pages("qualquer coisa") == []
    assert client.available is False


async def test_read_page_raises_runtime_error_when_all_down():
    client = _client_without_vault()
    with pytest.raises(RuntimeError, match="indisponível"):
        await client.read_page("Página Inexistente")


async def test_circuit_breaker_skips_api_after_failure(monkeypatch):
    client = _client_without_vault()
    client._api_ok = False

    def explode(*args, **kwargs):
        raise AssertionError("a API não devia ser contactada com o breaker aberto")

    monkeypatch.setattr(httpx, "AsyncClient", explode)
    with pytest.raises(WikiAPIError):
        await client._api_get("/api/health")


async def test_search_pages_falls_back_to_cli_json(tmp_path, monkeypatch):
    from server.knowledge.wiki import WIKI_TOOL_REL

    tool = tmp_path / WIKI_TOOL_REL
    tool.parent.mkdir(parents=True)
    tool.write_text("# fake", "utf-8")
    client = WikiClient(tmp_path, api_url="http://127.0.0.1:1")

    async def fake_run(*args, timeout_s=30):
        assert args[0] == "bm25-search" and "--json" in args
        return '[{"title": "Texto Livre", "summary": "s"}, "lixo"]'

    monkeypatch.setattr(client, "_run", fake_run)
    results = await client.search_pages("texto livre")
    assert results == [{"title": "Texto Livre", "summary": "s"}]


async def test_api_get_rejects_invalid_json(monkeypatch):
    client = _client_without_vault()

    class FakeResponse:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            raise ValueError("not json")

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def get(self, url, params=None):
            return FakeResponse()

    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)
    with pytest.raises(WikiAPIError):
        await client._api_get("/api/search")
    assert client._api_ok is False


async def test_probe_reports_api(monkeypatch):
    client = _client_without_vault()

    class FakeResponse:
        status_code = 200

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def get(self, url, params=None):
            return FakeResponse()

    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)
    assert await client.probe() is True
    assert client.available is True
