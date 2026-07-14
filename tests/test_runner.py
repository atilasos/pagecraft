import json
from pathlib import Path

import pytest

from server.config import Config
from server.events import EventHub
from server.pipeline.runner import PipelineRunner, slugify
from server.storage import Storage

GOOD_HTML = (
    "<!doctype html>\n"
    '<html lang="pt-PT"><head><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width, initial-scale=1">'
    "<style>:focus-visible{outline:3px solid blue} "
    "@media (prefers-reduced-motion: reduce){*{animation:none}}</style></head>"
    '<body><main aria-live="polite">' + ("conteúdo pedagógico " * 200) + "</main></body></html>"
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
                "year": 3,
                "domain": "Números",
                "descriptor": "Reconhecer frações unitárias",
                "source": "AE Matemática 3.º ano (DGE)",
            }
        ],
        "competencies": ["PA-A"],
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

DESIGN = {"palette": {"bg": "oklch(0.98 0 250)", "surface": "#fff", "primary": "blue", "accent": "amber", "ink": "#222"}}

PROOF_OK = {"pass": True, "issues": [], "summary": "sem problemas"}
EVAL_OK = {"pass": True, "severity": "none", "issues": []}
EVAL_FAIL = {"pass": False, "severity": "major", "issues": ["botões pequenos"], "route": "builder"}


class FakeProvider:
    name = "fake"

    def __init__(self, evaluations):
        self.evaluations = list(evaluations)
        self.calls = []

    async def complete(self, prompt, *, schema=None, system=None, timeout_s=300, workdir=None):
        phase = self._phase_from(system)
        self.calls.append(phase)
        if phase == "architect":
            return DOCSPEC
        if phase == "designer":
            return DESIGN
        if phase == "builder":
            return {"html": GOOD_HTML, "notes": ""}
        if phase == "proofreader":
            return PROOF_OK
        if phase == "evaluator":
            return self.evaluations.pop(0)
        raise AssertionError(f"fase desconhecida: {phase}")

    @staticmethod
    def _phase_from(system):
        for name in ("Architect", "Designer", "Builder", "Proofreader", "Evaluator"):
            if f"Identidade: {name}" in (system or ""):
                return name.lower()
        return "?"


class NoKnowledge:
    available = False

    async def mem_context(self):
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


async def test_pipeline_happy_path_auto_publish(env):
    config, storage, hub = env
    provider = FakeProvider([EVAL_OK])
    runner = PipelineRunner(config, storage, hub, provider, NoKnowledge(), NoKnowledge())
    job = await runner.create_job(
        topic="Frações", subject="Matemática", year=3, duration=30, auto_publish=True
    )
    job = await _wait_status(runner, job["id"], {"done", "failed"})
    assert job["status"] == "done", job.get("error")
    assert provider.calls == ["architect", "designer", "builder", "proofreader", "evaluator"]
    slug = job["slug"]
    assert (config.activities_dir / slug / "index.html").exists()
    assert (config.activities_dir / slug / "teacher.md").exists()
    catalog = json.loads(config.catalog_path.read_text("utf-8"))
    assert any(item["slug"] == slug for item in catalog["items"])
    # artefactos de staging no formato histórico
    assert (config.outputs_dir / f"{slug}-docspec.json").exists()
    assert (config.outputs_dir / f"{slug}-evaluation-v1.json").exists()


async def test_pipeline_repair_loop_then_pass(env):
    config, storage, hub = env
    provider = FakeProvider([EVAL_FAIL, EVAL_OK])
    runner = PipelineRunner(config, storage, hub, provider, NoKnowledge(), NoKnowledge())
    job = await runner.create_job(topic="Frações", subject="Matemática", year=3, duration=30)
    job = await _wait_status(runner, job["id"], {"awaiting_review", "done", "failed"})
    assert job["status"] == "awaiting_review"
    assert job["iteration"] == 2
    assert provider.calls.count("builder") == 2
    events = await storage.read_jsonl(storage.path("jobs", job["id"], "events.jsonl"))
    assert any(e["type"] == "repair" for e in events)


async def test_pipeline_fails_after_max_iterations(env):
    config, storage, hub = env
    provider = FakeProvider([EVAL_FAIL, EVAL_FAIL, EVAL_FAIL])
    runner = PipelineRunner(config, storage, hub, provider, NoKnowledge(), NoKnowledge())
    job = await runner.create_job(topic="Frações", subject="Matemática", year=3, duration=30)
    job = await _wait_status(runner, job["id"], {"failed"}, timeout=10)
    assert job["status"] == "failed"
    assert job["iteration"] == 3


async def test_approve_publishes(env):
    config, storage, hub = env
    provider = FakeProvider([EVAL_OK])
    runner = PipelineRunner(config, storage, hub, provider, NoKnowledge(), NoKnowledge())
    job = await runner.create_job(topic="Sílabas", subject="Português", year=1, duration=20)
    job = await _wait_status(runner, job["id"], {"awaiting_review"})
    job = await runner.approve(job["id"])
    assert job["status"] == "done"
    assert (config.activities_dir / job["slug"] / "index.html").exists()
