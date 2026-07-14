"""Runner do pipeline de geração: architect → designer → builder →
proofreader → evaluator → repair loop → (aprovação) → publish.

Estado persistido em data/jobs/<id>/job.json após cada fase; artefactos no
formato histórico em outputs/lessons/<slug>-*. Progresso via EventLog
(data/jobs/<id>/events.jsonl) consumido por SSE.
"""

from __future__ import annotations

import asyncio
import json
import re
import unicodedata
import uuid
from pathlib import Path
from typing import Any

from ..config import Config
from ..events import EventHub, utcnow
from ..knowledge import AEClient, WikiClient
from ..providers import AIProvider, ProviderError, SchemaError
from ..storage import Storage
from .phases import PromptLibrary
from .validators import validate_activity_html

PHASES = ("architect", "designer", "builder", "proofreader", "evaluator")


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")[:60]


def _load_schema(schemas_dir: Path, name: str) -> dict:
    return json.loads((schemas_dir / f"{name}.schema.json").read_text("utf-8"))


class PipelineRunner:
    def __init__(
        self,
        config: Config,
        storage: Storage,
        hub: EventHub,
        provider: AIProvider,
        wiki: WikiClient,
        ae: AEClient,
    ):
        self.config = config
        self.storage = storage
        self.hub = hub
        self.provider = provider
        self.wiki = wiki
        self.ae = ae
        self.prompts = PromptLibrary(config.prompts_dir)
        schemas_dir = Path(__file__).parent / "schemas"
        self.schemas = {
            "architect": _load_schema(schemas_dir, "docspec"),
            "designer": _load_schema(schemas_dir, "design-spec"),
            "builder": _load_schema(schemas_dir, "builder-output"),
            "proofreader": _load_schema(schemas_dir, "proofread"),
            "evaluator": _load_schema(schemas_dir, "evaluation"),
        }
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._worker: asyncio.Task | None = None

    # ---- API pública ----

    async def create_job(
        self,
        *,
        topic: str,
        subject: str,
        year: int,
        duration: int,
        maker: str | None = None,
        auto_publish: bool = False,
    ) -> dict:
        slug = f"{year}ano-{slugify(topic)}"
        job = {
            "id": uuid.uuid4().hex[:12],
            "slug": slug,
            "topic": topic,
            "subject": subject,
            "year": year,
            "duration": duration,
            "maker": maker,
            "auto_publish": auto_publish,
            "provider": self.provider.name,
            "status": "queued",
            "current_phase": None,
            "iteration": 0,
            "max_iterations": self.config.max_iterations,
            "artifacts": {},
            "error": None,
            "created_at": utcnow(),
            "updated_at": utcnow(),
        }
        await self._save(job)
        await self._emit(job, "job_created", {"slug": slug})
        await self._queue.put(job["id"])
        self.ensure_worker()
        return job

    def ensure_worker(self) -> None:
        if self._worker is None or self._worker.done():
            self._worker = asyncio.create_task(self._work_loop())

    async def start(self) -> None:
        """Recupera jobs interrompidos por um restart e liga o worker."""
        requeued = 0
        for job in await self.list_jobs():
            status = job.get("status", "")
            if status == "queued" or status.startswith("running") or status == "publishing":
                await self._queue.put(job["id"])
                requeued += 1
        if requeued:
            self.ensure_worker()

    async def stop(self) -> None:
        if self._worker is not None:
            self._worker.cancel()
            try:
                await self._worker
            except (asyncio.CancelledError, Exception):
                pass
            self._worker = None

    async def get_job(self, job_id: str) -> dict | None:
        return await self.storage.read_json(self._job_path(job_id))

    async def list_jobs(self) -> list[dict]:
        jobs_dir = self.storage.root / "jobs"
        if not jobs_dir.is_dir():
            return []
        jobs = []
        for job_file in sorted(jobs_dir.glob("*/job.json")):
            data = await self.storage.read_json(job_file)
            if data:
                jobs.append(data)
        jobs.sort(key=lambda j: j.get("created_at", ""), reverse=True)
        return jobs

    async def approve(self, job_id: str, *, override: bool = False) -> dict | None:
        """Publica um job em revisão. Com override=True, o professor pode
        publicar um job que falhou a avaliação (o Evaluator aconselha; a
        decisão final é do professor), desde que exista HTML gerado."""
        job = await self.get_job(job_id)
        if not job:
            return None
        publishable = job["status"] == "awaiting_review" or (
            override and job["status"] == "failed" and job["artifacts"].get("html")
        )
        if not publishable:
            return None
        job["status"] = "publishing"
        job["published_with_override"] = override and job.get("error") is not None
        await self._save(job)
        await self._publish(job)
        return job

    # ---- internals ----

    def _job_path(self, job_id: str) -> Path:
        return self.storage.path("jobs", job_id, "job.json")

    def _events_log(self, job_id: str):
        return self.hub.log_for("jobs", job_id, "events.jsonl")

    async def _save(self, job: dict) -> None:
        job["updated_at"] = utcnow()
        await self.storage.write_json(self._job_path(job["id"]), job)

    async def _emit(self, job: dict, type_: str, payload: dict | None = None) -> None:
        await self._events_log(job["id"]).append(
            {"type": type_, "job_id": job["id"], "status": job["status"], "payload": payload or {}}
        )

    def _artifact_path(self, job: dict, suffix: str) -> Path:
        self.config.outputs_dir.mkdir(parents=True, exist_ok=True)
        return self.config.outputs_dir / f"{job['slug']}{suffix}"

    async def _write_artifact(self, job: dict, key: str, suffix: str, data: Any) -> None:
        path = self._artifact_path(job, suffix)
        if isinstance(data, str):
            await asyncio.to_thread(path.write_text, data, "utf-8")
        else:
            await self.storage.write_json(path, data)
        job["artifacts"][key] = str(path)
        await self._save(job)

    async def _work_loop(self) -> None:
        while True:
            job_id = await self._queue.get()
            job = await self.get_job(job_id)
            if not job:
                continue
            try:
                if job["status"] == "publishing" and job["artifacts"].get("html"):
                    await self._publish(job)
                else:
                    await self._run_job(job)
            except Exception as exc:  # nunca matar o worker
                job = await self.get_job(job_id) or job
                job["status"] = "failed"
                job["error"] = f"{type(exc).__name__}: {exc}"
                await self._save(job)
                await self._emit(job, "failed", {"error": job["error"]})

    async def _call_phase(self, job: dict, phase: str, system: str, prompt: str) -> Any:
        """Chama o provider com retry: 1 retry direto, depois erro."""
        timeout = self.config.builder_timeout_s if phase == "builder" else self.config.generation_timeout_s
        schema = self.schemas[phase]
        prompt_path = self.storage.path("jobs", job["id"], f"{phase}-v{job['iteration']}-prompt.md")
        await asyncio.to_thread(prompt_path.write_text, f"# system\n\n{system}\n\n# prompt\n\n{prompt}", "utf-8")

        last_error: Exception | None = None
        for attempt in (1, 2):
            try:
                return await self.provider.complete(
                    prompt, schema=schema, system=system, timeout_s=timeout
                )
            except SchemaError as exc:
                last_error = exc
                prompt = (
                    prompt
                    + "\n\n---\n\nATENÇÃO: a tua resposta anterior não cumpriu o schema JSON "
                    + f"({exc}). Responde APENAS com JSON válido contra o schema."
                )
                await self._emit(job, "phase_retry", {"phase": phase, "attempt": attempt, "error": str(exc)})
            except ProviderError as exc:
                last_error = exc
                await self._emit(job, "phase_retry", {"phase": phase, "attempt": attempt, "error": str(exc)})
        raise last_error or RuntimeError("falha desconhecida")

    async def _run_job(self, job: dict) -> None:
        job["status"] = "running"
        await self._save(job)

        # contexto de conhecimento (uma vez por job)
        ae_excerpt, ae_citation = await self.ae.context_or_fallback(job["subject"], job["year"])
        mem_context = ""
        if self.wiki.available:
            try:
                mem_context = await self.wiki.mem_context()
            except (RuntimeError, TimeoutError):
                mem_context = ""
        await self._emit(
            job,
            "knowledge_ready",
            {"ae_found": bool(ae_excerpt), "ae_citation": ae_citation, "mem_pages": bool(mem_context)},
        )

        artifacts = job["artifacts"]

        # architect
        docspec = await self._maybe_resume(job, "docspec")
        if docspec is None:
            docspec = await self._phase(
                job,
                "architect",
                *self.prompts.architect(
                    topic=job["topic"],
                    subject=job["subject"],
                    year=job["year"],
                    duration=job["duration"],
                    maker=job["maker"],
                    ae_excerpt=ae_excerpt,
                    ae_citation=ae_citation,
                    mem_context=mem_context,
                ),
            )
            await self._write_artifact(job, "docspec", "-docspec.json", docspec)

        # designer
        design_spec = await self._maybe_resume(job, "design_spec")
        if design_spec is None:
            design_spec = await self._phase(job, "designer", *self.prompts.designer(docspec))
            await self._write_artifact(job, "design_spec", "-design-spec.json", design_spec)

        # builder + repair loop
        repair_ticket: dict | None = None
        previous_html: str | None = None
        evaluation: dict = {}
        while job["iteration"] < job["max_iterations"]:
            job["iteration"] += 1
            await self._save(job)

            built = await self._phase(
                job,
                "builder",
                *self.prompts.builder(
                    docspec, design_spec, repair_ticket=repair_ticket, previous_html=previous_html
                ),
            )
            html = built["html"]
            await self._write_artifact(job, "html", ".html", html)

            validation = validate_activity_html(html).as_dict()
            await self._emit(job, "validation", validation)

            proofread = await self._phase(job, "proofreader", *self.prompts.proofreader(docspec, html))
            await self._write_artifact(job, "proofread", f"-proofread-v{job['iteration']}.json", proofread)

            evaluation = await self._phase(
                job, "evaluator", *self.prompts.evaluator(docspec, html, validation, proofread)
            )
            await self._write_artifact(job, "evaluation", f"-evaluation-v{job['iteration']}.json", evaluation)

            eval_pass = bool(evaluation.get("pass")) and validation["passed"]
            proof_ok = bool(proofread.get("pass", True))
            if eval_pass and proof_ok:
                break

            previous_html = html
            repair_ticket = {
                "route": evaluation.get("route", "builder"),
                "validation_errors": validation["errors"],
                "critical": evaluation.get("critical", []),
                "issues": evaluation.get("issues", []),
                "proofread_issues": proofread.get("issues", []),
            }
            await self._emit(job, "repair", {"iteration": job["iteration"], "ticket": repair_ticket})
        else:
            job["status"] = "failed"
            job["error"] = "avaliação não passou dentro de max_iterations"
            await self._save(job)
            await self._emit(job, "failed", {"error": job["error"], "last_evaluation": evaluation})
            return

        # markdown do professor
        from ..markdown_export import docspec_to_markdown

        teacher_md = docspec_to_markdown(docspec)
        await self._write_artifact(job, "teacher_md", ".md", teacher_md)

        if job["auto_publish"]:
            job["status"] = "publishing"
            await self._save(job)
            await self._publish(job)
        else:
            job["status"] = "awaiting_review"
            await self._save(job)
            await self._emit(job, "awaiting_review", {"preview": f"/outputs/{job['slug']}.html"})

    async def _phase(self, job: dict, phase: str, system: str, prompt: str) -> Any:
        job["current_phase"] = phase
        job["status"] = f"running_{phase}"
        await self._save(job)
        await self._emit(job, "phase_started", {"phase": phase, "iteration": job["iteration"]})
        result = await self._call_phase(job, phase, system, prompt)
        await self._emit(job, "phase_done", {"phase": phase, "iteration": job["iteration"]})
        return result

    async def _maybe_resume(self, job: dict, key: str) -> Any | None:
        """Retoma: se o artefacto já existe de uma run interrompida, reutiliza."""
        path_str = job["artifacts"].get(key)
        if not path_str:
            return None
        path = Path(path_str)
        if not path.exists():
            return None
        await self._emit(job, "resumed_artifact", {"artifact": key})
        return await self.storage.read_json(path)

    async def _publish(self, job: dict) -> None:
        from ..markdown_export import docspec_to_markdown
        from ..publish import publish_activity

        docspec = await self.storage.read_json(Path(job["artifacts"]["docspec"]))
        design_spec = await self.storage.read_json(Path(job["artifacts"].get("design_spec", "")), default=None)
        teacher_md_path = job["artifacts"].get("teacher_md")
        teacher_md = (
            Path(teacher_md_path).read_text("utf-8") if teacher_md_path else docspec_to_markdown(docspec)
        )
        meta = await asyncio.to_thread(
            publish_activity,
            self.config.repo_root,
            job["slug"],
            Path(job["artifacts"]["html"]),
            docspec,
            teacher_md,
            design_spec,
        )
        job["status"] = "done"
        job["published"] = meta
        await self._save(job)
        await self._emit(job, "done", {"activity_url": f"/activities/{job['slug']}/"})
