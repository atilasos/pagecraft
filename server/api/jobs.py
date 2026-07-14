"""Endpoints de geração de atividades (jobs do pipeline)."""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


class JobRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=200)
    subject: str = Field(min_length=2, max_length=60)
    year: int = Field(ge=1, le=4)
    duration: int = Field(ge=15, le=50, default=30)
    maker: str | None = None
    auto_publish: bool = False


def _runner(request: Request):
    return request.app.state.runner


@router.post("")
async def create_job(body: JobRequest, request: Request):
    job = await _runner(request).create_job(
        topic=body.topic,
        subject=body.subject,
        year=body.year,
        duration=body.duration,
        maker=body.maker,
        auto_publish=body.auto_publish,
    )
    return job


@router.get("")
async def list_jobs(request: Request):
    return await _runner(request).list_jobs()


@router.get("/{job_id}")
async def get_job(job_id: str, request: Request):
    job = await _runner(request).get_job(job_id)
    if not job:
        raise HTTPException(404, "job não encontrado")
    return job


@router.post("/{job_id}/approve")
async def approve_job(job_id: str, request: Request):
    job = await _runner(request).approve(job_id)
    if not job:
        raise HTTPException(409, "job não está a aguardar revisão")
    return job


@router.get("/{job_id}/stream")
async def stream_job(job_id: str, request: Request):
    runner = _runner(request)
    job = await runner.get_job(job_id)
    if not job:
        raise HTTPException(404, "job não encontrado")

    last_id = request.headers.get("last-event-id") or request.query_params.get("after", "0")
    try:
        after_seq = int(last_id)
    except ValueError:
        after_seq = 0

    log = runner._events_log(job_id)

    async def gen():
        async for record in log.subscribe(after_seq):
            yield f"id: {record['seq']}\nevent: {record['type']}\ndata: {json.dumps(record, ensure_ascii=False)}\n\n"
            if record["type"] in ("done", "failed"):
                break

    return StreamingResponse(gen(), media_type="text/event-stream")
