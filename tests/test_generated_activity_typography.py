"""Typography survives generation, repair, review and teacher publication."""
import asyncio
import base64
from pathlib import Path
import re
import shutil

import httpx

from server import app as app_module
from fakes import FakeProvider
from test_runner import EVAL_FAIL, EVAL_OK, pipeline_responses

ROOT = Path(__file__).resolve().parents[1]


async def test_generated_activity_bundles_the_offline_font_before_review_and_publication(tmp_path, monkeypatch):
    for name, path in {
        "DATA_DIR": tmp_path / "data",
        "REPO_ROOT": tmp_path,
        "OUTPUTS_DIR": tmp_path / "outputs",
        "ACTIVITIES_DIR": tmp_path / "activities",
        "CATALOG_PATH": tmp_path / "catalog.json",
        "VAULT_PATH": tmp_path / "empty-vault",
    }.items():
        monkeypatch.setenv(f"PAGECRAFT_{name}", str(path))
    monkeypatch.setenv("PAGECRAFT_WIKI_API_URL", "http://127.0.0.1:9")
    (tmp_path / "activities").mkdir()
    shutil.copytree(ROOT / "server/static", tmp_path / "server/static")
    provider = FakeProvider(pipeline_responses(EVAL_FAIL, EVAL_OK))
    monkeypatch.setattr(app_module, "build_generation_provider", lambda config: provider)
    app = app_module.create_app()
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as teacher:
            await teacher.get("/api/teacher-bootstrap")
            created = await teacher.post("/api/jobs", json={"topic": "Frações", "subject": "Matemática", "year": 2})
            assert created.status_code == 200
            job_id = created.json()["id"]

            async def wait_review():
                while True:
                    response = await teacher.get(f"/api/jobs/{job_id}")
                    job = response.json()
                    if job["status"] in {"awaiting_review", "failed"}:
                        return job
                    await asyncio.sleep(0.01)

            job = await asyncio.wait_for(wait_review(), timeout=5)
            assert job["status"] == "awaiting_review", job.get("error")
            assert job["iteration"] == 2
            preview = await teacher.get(f"/outputs/{job['slug']}.html")
            assert preview.status_code == 200
            font_urls = re.findall(r"data:font/woff2;base64,([A-Za-z0-9+/=]+)", preview.text)
            assert len(font_urls) == 1, "a revisão tem de incluir a alternativa offline"
            expected_font = (ROOT / "assets/fonts/didact-gothic/DidactGothic-Regular.woff2").read_bytes()
            assert base64.b64decode(font_urls[0]) == expected_font
            license_text = (ROOT / "assets/fonts/didact-gothic/OFL.txt").read_text().strip()
            assert license_text in preview.text
            assert '"Century Gothic", "Didact Gothic"' in preview.text
            # As duas rondas de revisão receberam o artefacto com a fonte real.
            for call in (provider.calls[3], provider.calls[6]):
                assert font_urls[0] in call["prompt"]
            approved = await teacher.post(f"/api/jobs/{job_id}/approve")
            assert approved.status_code == 200
            published = await teacher.get(f"/activities/{job['slug']}/")
            assert published.status_code == 200
            assert published.text.count(f"data:font/woff2;base64,{font_urls[0]}") == 1
            assert license_text in published.text
            assert "font-src data:" in published.headers["content-security-policy"]
