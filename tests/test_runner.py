import asyncio
import json
from dataclasses import replace
from pathlib import Path

import pytest

from server.config import Config
from server.events import EventHub
from server.pipeline.runner import PipelineRunner, ReviewConflict, decide_repair, slugify
from server.storage import Storage

from fakes import FakeProvider

GOOD_HTML = (
    "<!doctype html>\n"
    '<html lang="pt-PT"><head><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width, initial-scale=1">'
    "<style>:focus-visible{outline:3px solid blue} "
    "@media (prefers-reduced-motion: reduce){*{animation:none}}</style></head>"
    '<body><main aria-live="polite"><section id="u1"><aside data-pagecraft-support="u1"></aside>'
    + ("conteúdo pedagógico " * 200)
    + "</section></main></body></html>"
)

DOCSPEC = {
    "topic": "Frações",
    "ageRange": "8-10",
    "duration": 30,
    "objectives": ["Reconhecer metades", "Comparar frações"],
    "curriculum": {
        "ae": [
            {
                "subject": "Matemática",
                "year": "3.º ano",
                "domain": "Números",
                "descriptor": "Reconhecer frações unitárias",
                "source": "AE Matemática 3.º ano (DGE)",
            }
        ],
        "competencies": ["PA-C: Raciocínio e resolução de problemas"],
    },
    "memAlignment": {"modules": [], "instruments": [], "socialOrganization": "pares"},
    "units": [
        {
            "summary": "Metades com pizza",
            "textDescription": "Dividir uma pizza em partes iguais.",
            "interaction": {
                "state": [],
                "render": "pizza dividida",
                "transition": "tocar para dividir",
                "constraint": "partes iguais somam o todo",
                "assessment": "o aluno divide em 2 partes iguais",
            },
            "differentiation": {"support": "2 partes", "standard": "4 partes", "challenge": "8 partes"},
            "duration": 30,
        }
    ],
    "sessionFlow": "exploração",
}

_SUPPORT_EXAMPLE = json.loads((Path(__file__).parent / 'fixtures/support-examples.json').read_text())[0]
DOCSPEC['support'] = _SUPPORT_EXAMPLE['support']
DOCSPEC['units'][0]['support'] = _SUPPORT_EXAMPLE['units'][0]['support']

DESIGN = {"palette": {"bg": "oklch(0.98 0 250)", "surface": "#fff", "primary": "blue", "accent": "amber", "ink": "#222"}}

PROOF_OK = {"pass": True, "issues": [], "summary": "sem problemas"}
EVAL_OK = {"pass": True, "severity": "low", "issues": []}
EVAL_FAIL = {"pass": False, "severity": "high", "issues": ["botões pequenos"], "route": "builder"}

BUILT_OK = {"html": GOOD_HTML, "notes": ""}


def pipeline_responses(*evaluations, built=BUILT_OK):
    """Respostas na ordem do pipeline: architect, designer e depois uma
    ronda builder→proofreader→evaluator por cada avaliação dada."""
    responses = [DOCSPEC, DESIGN]
    for evaluation in evaluations:
        responses += [built, PROOF_OK, evaluation]
    return responses


def phases_called(runner, provider):
    """Sequência de fases pedidas ao provider, inferida pelo schema."""
    by_schema = {id(phase.schema): name for name, phase in runner.phases.items()}
    return [by_schema[id(call["schema"])] for call in provider.calls]


class NoKnowledge:
    available = False

    async def probe(self):
        return False

    async def mem_context(self):
        return ""

    async def topic_context(self, topic, subject=""):
        return ""

    def context_for(self, subject, year):
        return "", ""

    async def context_or_fallback(self, subject, year):
        return "", ""


@pytest.fixture
def env(tmp_path):
    repo = tmp_path / "repo"
    (repo / "activities").mkdir(parents=True)
    (repo / "catalog.json").write_text(
        json.dumps({"generatedAt": "2026-01-01T00:00:00", "count": 0, "items": []}), "utf-8"
    )
    config = Config(
        repo_root=repo,
        data_dir=tmp_path / "data",
        outputs_dir=repo / "outputs" / "lessons",
        activities_dir=repo / "activities",
        catalog_path=repo / "catalog.json",
        prompts_dir=Path(__file__).parent.parent / "server" / "pipeline" / "prompts",
    )
    storage = Storage(config.data_dir)
    return config, storage, EventHub(storage)


async def _run_to_end(runner, **kwargs):
    job = await runner.create_job(**kwargs)
    await runner._worker  # nunca termina; em vez disso, espera pelo estado
    return job


async def _wait_status(runner, job_id, statuses, timeout=5.0):
    import asyncio

    async def poll():
        while True:
            job = await runner.get_job(job_id)
            if job and job["status"] in statuses:
                return job
            await asyncio.sleep(0.02)

    return await asyncio.wait_for(poll(), timeout)


async def test_slugify():
    assert slugify("Frações e Décimas!") == "fracoes-e-decimas"


VALIDATION_OK = {"passed": True, "errors": [], "warnings": []}
VALIDATION_BAD = {"passed": False, "errors": ["falta <!doctype html>"], "warnings": []}


def test_decide_repair_passes_when_everything_passes():
    assert decide_repair(VALIDATION_OK, PROOF_OK, EVAL_OK) is None


def test_decide_repair_on_evaluator_fail():
    ticket = decide_repair(VALIDATION_OK, PROOF_OK, EVAL_FAIL)
    assert ticket["route"] == "builder"
    assert ticket["issues"] == ["botões pequenos"]


def test_decide_repair_on_validation_fail_even_with_evaluator_pass():
    ticket = decide_repair(VALIDATION_BAD, PROOF_OK, EVAL_OK)
    assert ticket["validation_errors"] == ["falta <!doctype html>"]


def test_decide_repair_on_proofread_fail():
    proof_bad = {"pass": False, "issues": ["'errado' é punitivo"], "summary": ""}
    ticket = decide_repair(VALIDATION_OK, proof_bad, EVAL_OK)
    assert ticket["proofread_issues"] == ["'errado' é punitivo"]


async def test_pipeline_happy_path_auto_publish(env):
    config, storage, hub = env
    provider = FakeProvider(pipeline_responses(EVAL_OK))
    runner = PipelineRunner(config, storage, hub, provider, NoKnowledge(), NoKnowledge())
    job = await runner.create_job(
        topic="Frações", subject="Matemática", year=3, duration=30, auto_publish=True
    )
    job = await _wait_status(runner, job["id"], {"done", "failed"})
    assert job["status"] == "done", job.get("error")
    assert phases_called(runner, provider) == ["architect", "designer", "builder", "proofreader", "evaluator"]
    slug = job["slug"]
    assert (config.activities_dir / slug / "index.html").exists()
    assert (config.activities_dir / slug / "teacher.md").exists()
    assert "PageCraftSupport.configure(" in (config.activities_dir / slug / "index.html").read_text()
    assert DOCSPEC["support"]["version"] in (config.activities_dir / slug / "index.html").read_text()
    catalog = json.loads(config.catalog_path.read_text("utf-8"))
    assert any(item["slug"] == slug for item in catalog["items"])
    # Todos os artefactos pertencem ao diretório do job.
    assert (config.outputs_dir / job["id"] / f"{slug}-docspec.json").exists()
    assert (config.outputs_dir / job["id"] / f"{slug}-evaluation-v1.json").exists()


async def test_pipeline_repair_loop_then_pass(env):
    config, storage, hub = env
    provider = FakeProvider(pipeline_responses(EVAL_FAIL, EVAL_OK))
    runner = PipelineRunner(config, storage, hub, provider, NoKnowledge(), NoKnowledge())
    job = await runner.create_job(topic="Frações", subject="Matemática", year=3, duration=30)
    job = await _wait_status(runner, job["id"], {"awaiting_review", "done", "failed"})
    assert job["status"] == "awaiting_review"
    assert job["iteration"] == 2
    assert phases_called(runner, provider).count("builder") == 2
    events = await storage.read_jsonl(storage.path("jobs", job["id"], "events.jsonl"))
    assert any(e["type"] == "repair" for e in events)


async def test_pipeline_repairs_when_deterministic_validation_fails(env):
    """O repair loop dispara mesmo com o Evaluator a aprovar, quando a
    validação determinista chumba o HTML (ramo nunca antes exercido)."""
    config, storage, hub = env
    bad_build = {"html": "<html><body>" + "conteúdo " * 80 + "</body></html>", "notes": ""}
    provider = FakeProvider(
        [DOCSPEC, DESIGN, bad_build, PROOF_OK, EVAL_OK, BUILT_OK, PROOF_OK, EVAL_OK]
    )
    runner = PipelineRunner(config, storage, hub, provider, NoKnowledge(), NoKnowledge())
    job = await runner.create_job(topic="Frações", subject="Matemática", year=3, duration=30)
    job = await _wait_status(runner, job["id"], {"awaiting_review", "failed"})
    assert job["status"] == "awaiting_review"
    assert job["iteration"] == 2
    events = await storage.read_jsonl(storage.path("jobs", job["id"], "events.jsonl"))
    repair = next(e for e in events if e["type"] == "repair")
    assert repair["payload"]["ticket"]["validation_errors"], "o ticket leva os erros deterministas"


async def test_pipeline_fails_after_max_iterations(env):
    config, storage, hub = env
    provider = FakeProvider(pipeline_responses(EVAL_FAIL, EVAL_FAIL, EVAL_FAIL))
    runner = PipelineRunner(config, storage, hub, provider, NoKnowledge(), NoKnowledge())
    job = await runner.create_job(topic="Frações", subject="Matemática", year=3, duration=30)
    job = await _wait_status(runner, job["id"], {"failed"}, timeout=10)
    assert job["status"] == "failed"
    assert job["iteration"] == 3


async def test_start_requeues_interrupted_jobs(env):
    config, storage, hub = env
    provider = FakeProvider(pipeline_responses(EVAL_OK))
    runner = PipelineRunner(config, storage, hub, provider, NoKnowledge(), NoKnowledge())
    # simular job interrompido a meio (persistido como running_builder)
    import uuid

    from server.events import utcnow

    job = {
        "id": uuid.uuid4().hex[:12],
        "slug": "3ano-interrompido",
        "artifact_version": 1,
        "topic": "Interrompido",
        "subject": "Matemática",
        "year": 3,
        "duration": 30,
        "maker": None,
        "auto_publish": False,
        "provider": "fake",
        "status": "running_builder",
        "current_phase": "builder",
        "iteration": 1,
        "max_iterations": 3,
        "artifacts": {},
        "error": None,
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }
    await storage.write_json(storage.path("jobs", job["id"], "job.json"), job)
    await runner.start()
    fresh = await _wait_status(runner, job["id"], {"awaiting_review", "failed"})
    assert fresh["status"] == "awaiting_review"
    await runner.stop()


async def test_failed_job_can_publish_with_override(env):
    config, storage, hub = env
    provider = FakeProvider(pipeline_responses(EVAL_FAIL, EVAL_FAIL, EVAL_FAIL))
    runner = PipelineRunner(config, storage, hub, provider, NoKnowledge(), NoKnowledge())
    job = await runner.create_job(topic="Difícil", subject="Matemática", year=3, duration=30)
    job = await _wait_status(runner, job["id"], {"failed"}, timeout=10)
    assert await runner.approve(job["id"], review_id=job["review"]["id"]) is None  # sem override não publica
    published = await runner.approve(job["id"], review_id=job["review"]["id"], override=True)
    assert published["status"] == "done"
    assert (config.activities_dir / published["slug"] / "index.html").exists()


async def test_approve_publishes(env):
    config, storage, hub = env
    provider = FakeProvider(pipeline_responses(EVAL_OK))
    runner = PipelineRunner(config, storage, hub, provider, NoKnowledge(), NoKnowledge())
    job = await runner.create_job(topic="Sílabas", subject="Português", year=1, duration=20)
    job = await _wait_status(runner, job["id"], {"awaiting_review"})
    job = await runner.approve(job["id"], review_id=job["review"]["id"])
    assert job["status"] == "done"
    assert (config.activities_dir / job["slug"] / "index.html").exists()


@pytest.mark.parametrize("restart", [False, True])
async def test_same_topic_failed_job_cannot_replace_approved_job(env, restart):
    config, storage, hub = env
    config = replace(config, max_iterations=1)
    html_a = GOOD_HTML.replace('<main ', '<h1>Geração A revista</h1><main ')
    html_b = GOOD_HTML.replace('<main ', '<h1>Geração B falhada</h1><main ')
    provider = FakeProvider(
        pipeline_responses(EVAL_OK, built={'html': html_a, 'notes': ''})
        + pipeline_responses(EVAL_FAIL, built={'html': html_b, 'notes': ''})
    )
    runner = PipelineRunner(config, storage, hub, provider, NoKnowledge(), NoKnowledge())
    try:
        a = await runner.create_job(topic='Frações', subject='Matemática', year=3, duration=30)
        a = await _wait_status(runner, a['id'], {'awaiting_review'})
        reviewed = Path(a['artifacts']['html']).read_bytes()
        b = await runner.create_job(topic='Frações', subject='Matemática', year=3, duration=30)
        b = await _wait_status(runner, b['id'], {'failed'})
        if restart:
            await runner.stop()
            provider = FakeProvider([])
            runner = PipelineRunner(config, storage, hub, provider, NoKnowledge(), NoKnowledge())
            await runner.start()
        published = await runner.approve(a['id'], review_id=a['review']['id'])
        html = (config.activities_dir / published['slug'] / 'index.html').read_text()
        assert 'Geração A revista' in html and 'Geração B falhada' not in html
        assert Path(a['artifacts']['html']).read_bytes() == reviewed
        assert (config.activities_dir / published['slug'] / 'index.html').read_bytes() == reviewed
        assert a['slug'] != b['slug']
        assert not set(a['artifacts'].values()) & set(b['artifacts'].values())
    finally:
        await runner.stop()


@pytest.mark.parametrize('key', ['html', 'docspec', 'design_spec', 'teacher_md', 'validation', 'proofread', 'evaluation', 'old_report', 'extra_file'])
async def test_review_rejects_any_changed_artifact(env, key):
    config, storage, hub = env
    provider = FakeProvider(pipeline_responses(EVAL_FAIL, EVAL_OK))
    runner = PipelineRunner(config, storage, hub, provider, NoKnowledge(), NoKnowledge())
    try:
        job = await runner.create_job(topic='Frações', subject='Matemática', year=3, duration=30)
        job = await _wait_status(runner, job['id'], {'awaiting_review'})
        review_id = job['review']['id']
        original = await runner.preview(job['id'], review_id)
        assert original == Path(job['artifacts']['html']).read_bytes()
        if key == 'old_report':
            path = runner._artifact_path(job, '-evaluation-v1.json')
        elif key == 'extra_file':
            path = runner._artifact_path(job, '-unexpected.json')
        else:
            path = Path(job['artifacts'][key])
        path.write_text('alterado após a revisão', encoding='utf-8')
        with pytest.raises(ReviewConflict, match='mudaram'):
            await runner.preview(job['id'], review_id)
        with pytest.raises(ReviewConflict, match='mudaram'):
            await runner.approve(job['id'], review_id=review_id, override=True)
        assert not list(config.activities_dir.iterdir())
    finally:
        await runner.stop()


async def test_approval_revalidated_after_persisting_intent(env, monkeypatch):
    config, storage, hub = env
    runner = PipelineRunner(config, storage, hub, FakeProvider(pipeline_responses(EVAL_OK)), NoKnowledge(), NoKnowledge())
    try:
        job = await runner.create_job(topic='Frações', subject='Matemática', year=3, duration=30)
        job = await _wait_status(runner, job['id'], {'awaiting_review'})
        save = runner._save

        async def change_after_approval(current):
            await save(current)
            if current['status'] == 'publishing':
                Path(current['artifacts']['html']).write_text('B depois da aprovação')

        monkeypatch.setattr(runner, '_save', change_after_approval)
        with pytest.raises(ReviewConflict, match='mudaram'):
            await runner.approve(job['id'], review_id=job['review']['id'])
        assert (await runner.get_job(job['id']))['status'] == 'failed'
        assert not list(config.activities_dir.iterdir())
    finally:
        await runner.stop()


async def test_publish_uses_verified_bytes_without_rereading_paths(env, monkeypatch):
    from server import publish
    config, storage, hub = env
    runner = PipelineRunner(config, storage, hub, FakeProvider(pipeline_responses(EVAL_OK)), NoKnowledge(), NoKnowledge())
    try:
        job = await runner.create_job(topic='Frações', subject='Matemática', year=3, duration=30)
        job = await _wait_status(runner, job['id'], {'awaiting_review'})
        reviewed = Path(job['artifacts']['html']).read_bytes()
        original = publish.publish_activity

        def change_source_before_copy(*args, **kwargs):
            Path(job['artifacts']['html']).write_text('ficheiro alterado durante a cópia')
            return original(*args, **kwargs)

        monkeypatch.setattr(publish, 'publish_activity', change_source_before_copy)
        await runner.approve(job['id'], review_id=job['review']['id'])
        assert (config.activities_dir / job['slug'] / 'index.html').read_bytes() == reviewed
    finally:
        await runner.stop()


@pytest.mark.parametrize('crash_point', ['before_publish', 'after_install'])
async def test_restart_publishing_and_repeated_approvals_are_idempotent(env, monkeypatch, crash_point):
    config, storage, hub = env
    provider = FakeProvider(pipeline_responses(EVAL_OK))
    runner = PipelineRunner(config, storage, hub, provider, NoKnowledge(), NoKnowledge())
    job = await runner.create_job(topic='Frações', subject='Matemática', year=3, duration=30)
    job = await _wait_status(runner, job['id'], {'awaiting_review'})
    reviewed = Path(job['artifacts']['html']).read_bytes()
    review_id = job['review']['id']

    async def crash(*args):
        raise asyncio.CancelledError()

    if crash_point == 'before_publish':
        monkeypatch.setattr(runner, '_publish', crash)
    else:
        save = runner._save

        async def crash_before_marking_done(current):
            if current['status'] == 'done':
                raise asyncio.CancelledError()
            await save(current)
        monkeypatch.setattr(runner, '_save', crash_before_marking_done)
    with pytest.raises(asyncio.CancelledError):
        await runner.approve(job['id'], review_id=review_id)
    assert (await runner.get_job(job['id']))['status'] == 'publishing'
    await runner.stop()

    no_ai = FakeProvider([])
    restarted = PipelineRunner(config, storage, hub, no_ai, NoKnowledge(), NoKnowledge())
    try:
        await restarted.start()
        done = await _wait_status(restarted, job['id'], {'done', 'failed'})
        assert done['status'] == 'done', done.get('error')
        assert done['approval']['review_id'] == review_id
        assert no_ai.calls == []
        dst = config.activities_dir / job['slug']
        assert (dst / 'index.html').read_bytes() == reviewed
        before = {p.name: p.read_bytes() for p in dst.iterdir()}
        catalog = config.catalog_path.read_bytes()
        results = await asyncio.gather(*[restarted.approve(job['id'], review_id=review_id) for _ in range(3)])
        assert all(result['status'] == 'done' for result in results)
        assert before == {p.name: p.read_bytes() for p in dst.iterdir()}
        assert catalog == config.catalog_path.read_bytes()
        with pytest.raises(ReviewConflict):
            await restarted.approve(job['id'], review_id='0' * 64)
    finally:
        await restarted.stop()


@pytest.mark.parametrize('status', ['queued', 'running_builder', 'awaiting_review', 'publishing', 'failed', 'done'])
async def test_legacy_jobs_are_explicitly_blocked_without_touching_shared_files(env, status):
    config, storage, hub = env
    provider = FakeProvider([])
    runner = PipelineRunner(config, storage, hub, provider, NoKnowledge(), NoKnowledge())
    config.outputs_dir.mkdir(parents=True)
    shared = config.outputs_dir / '3ano-fracoes.html'
    shared.write_text('conteúdo de origem incerta')
    job = {'id': 'legacy', 'slug': '3ano-fracoes', 'status': status, 'artifacts': {'html': str(shared)},
           'review': {'id': '0' * 64}, 'preview_url': '/outputs/3ano-fracoes.html'}
    await runner._save(job)
    await runner.start()
    await runner.start()  # a migração também converge
    fresh = await runner.get_job(job['id'])
    if status == 'done':
        assert fresh['status'] == 'done'
    else:
        assert fresh['status'] == 'failed'
        assert fresh['legacy_blocked']
        assert 'Job antigo' in fresh['error']
        assert 'review' not in fresh and 'preview_url' not in fresh
        with pytest.raises(ReviewConflict):
            await runner.approve(job['id'], review_id='0' * 64, override=True)
    assert provider.calls == []
    assert runner._queue.empty()
    assert shared.read_text() == 'conteúdo de origem incerta'
    assert not list(config.activities_dir.iterdir())
    await runner.stop()


async def test_restart_never_publishes_without_persisted_approval(env):
    config, storage, hub = env
    runner = PipelineRunner(config, storage, hub, FakeProvider(pipeline_responses(EVAL_OK)), NoKnowledge(), NoKnowledge())
    job = await runner.create_job(topic='Frações', subject='Matemática', year=3, duration=30)
    job = await _wait_status(runner, job['id'], {'awaiting_review'})
    await runner.stop()
    job['status'] = 'publishing'
    await runner._save(job)
    restarted = PipelineRunner(config, storage, hub, FakeProvider([]), NoKnowledge(), NoKnowledge())
    try:
        await restarted.start()
        failed = await _wait_status(restarted, job['id'], {'failed', 'done'})
        assert failed['status'] == 'failed'
        assert 'Revisão ausente' in failed['error']
        assert not list(config.activities_dir.iterdir())
    finally:
        await restarted.stop()


async def test_preview_and_approval_api_require_exact_review_and_teacher(env, monkeypatch):
    import httpx
    import shutil
    from server import app as app_module

    config, storage, hub = env
    shutil.copytree(Path(__file__).parents[1] / 'server/static', config.repo_root / 'server/static')
    monkeypatch.setattr(app_module, 'load_config', lambda: config)
    monkeypatch.setattr(app_module, 'build_generation_provider', lambda _: FakeProvider(pipeline_responses(EVAL_OK)))
    app = app_module.create_app()
    async with app.router.lifespan_context(app):
        app.state.runner.wiki = NoKnowledge()
        app.state.runner.ae = NoKnowledge()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            await client.get('/api/teacher-bootstrap')
            response = await client.post('/api/jobs', json={'topic': 'Frações', 'subject': 'Matemática', 'year': 3})
            job = await _wait_status(app.state.runner, response.json()['id'], {'awaiting_review'})
            preview = await client.get(job['preview_url'])
            assert preview.status_code == 200
            assert preview.content == Path(job['artifacts']['html']).read_bytes()
            assert preview.headers['cache-control'] == 'no-store'
            assert 'sandbox allow-scripts;' in preview.headers['content-security-policy']
            assert 'connect-src \'none\'' in preview.headers['content-security-policy']
            assert (await client.get(f"/api/jobs/{job['id']}/preview", params={'review_id': '0' * 64})).status_code == 409
            assert (await client.post(f"/api/jobs/{job['id']}/approve")).status_code == 422
            assert (await client.post(f"/api/jobs/{job['id']}/approve", json={'review_id': '0' * 64})).status_code == 409
            # Continua disponível o mount existente; esta branch não muda /outputs.
            raw_url = f"/outputs/{job['id']}/{Path(job['artifacts']['html']).name}"
            client.cookies.clear()
            assert (await client.get(job['preview_url'])).status_code == 401
            assert (await client.post(f"/api/jobs/{job['id']}/approve", json={'review_id': job['review']['id']})).status_code == 401
            assert (await client.get(raw_url)).status_code == 200
            await client.get('/api/teacher-bootstrap')
            Path(job['artifacts']['evaluation']).unlink()
            assert (await client.get(job['preview_url'])).status_code == 409
            conflict = await client.post(f"/api/jobs/{job['id']}/approve?override=true", json={'review_id': job['review']['id']})
            assert conflict.status_code == 409
            assert not list(config.activities_dir.iterdir())
