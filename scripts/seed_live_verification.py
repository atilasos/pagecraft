#!/usr/bin/env python3
"""Cria dados descartáveis e previsíveis para a verificação da aula ao vivo."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


CLASS_ID = "verify25"
SESSION_ID = "verify25"
JOIN_CODE = "PC2525"
ACTIVITY_SLUG = "arvore-frases-vivas"
ACTIVITY_TITLE = "Árvore de frases vivas"

STUDENTS = (
    ("alice001", "Alice"),
    ("beatriz1", "Beatriz"),
    ("carlos01", "Carlos"),
    ("diana001", "Diana"),
    ("eva00001", "Eva"),
    ("fabio001", "Fábio"),
)


def iso_at(now: datetime, seconds_ago: int) -> str:
    return (now - timedelta(seconds=seconds_ago)).isoformat()


def event(
    seq: int,
    now: datetime,
    seconds_ago: int,
    type_: str,
    student_id: str,
    payload: dict | None = None,
) -> dict:
    return {
        "event_id": f"verify25-{seq:02d}",
        "type": type_,
        "student_id": student_id,
        "unit_id": None,
        "payload": payload or {},
        "seq": seq,
        "ts": iso_at(now, seconds_ago),
    }


def build_fixture(now: datetime) -> tuple[dict, dict, list[dict], dict]:
    started_at = iso_at(now, 600)
    classroom = {
        "id": CLASS_ID,
        "name": "Turma de verificação",
        "year": 3,
        "students": [
            {"id": student_id, "display_name": display_name}
            for student_id, display_name in STUDENTS
        ],
        "created_at": started_at,
    }
    session = {
        "id": SESSION_ID,
        "class_id": CLASS_ID,
        "class_name": classroom["name"],
        "activity_slug": ACTIVITY_SLUG,
        "activity_title": ACTIVITY_TITLE,
        "status": "live",
        "join_code": JOIN_CODE,
        "started_at": started_at,
        "closed_at": None,
        "roster": {
            student_id: {
                "display_name": display_name,
                "token": None if student_id == "fabio001" else f"token-{student_id}",
                "claimed_at": None if student_id == "fabio001" else iso_at(now, 400),
            }
            for student_id, display_name in STUDENTS
        },
        "pit_items": [],
    }
    events = [
        # Sem sinal: a última presença de Alice foi há quatro minutos.
        event(1, now, 400, "joined", "alice001", {"display_name": "Alice"}),
        event(2, now, 240, "heartbeat", "alice001"),
        # Precisa de ti: Beatriz pediu ajuda e espera mais tempo do que Carlos.
        event(3, now, 400, "joined", "beatriz1", {"display_name": "Beatriz"}),
        event(4, now, 350, "attempt", "beatriz1", {"correct": False}),
        event(5, now, 320, "help_needed", "beatriz1", {"note": "ajuda explícita"}),
        event(6, now, 10, "heartbeat", "beatriz1"),
        # Precisa de ti: Carlos está parado, sem pedido explícito.
        event(7, now, 400, "joined", "carlos01", {"display_name": "Carlos"}),
        event(8, now, 240, "discovery", "carlos01", {"message": "último trabalho"}),
        event(9, now, 10, "heartbeat", "carlos01"),
        # A tropeçar: três tentativas falhadas consecutivas.
        event(10, now, 200, "joined", "diana001", {"display_name": "Diana"}),
        event(11, now, 70, "attempt", "diana001", {"correct": False}),
        event(12, now, 60, "attempt", "diana001", {"correct": False}),
        event(13, now, 50, "attempt", "diana001", {"correct": False}),
        event(14, now, 10, "heartbeat", "diana001"),
        # A fluir: trabalho recente.
        event(15, now, 80, "joined", "eva00001", {"display_name": "Eva"}),
        event(16, now, 20, "discovery", "eva00001", {"message": "trabalho recente"}),
        event(17, now, 10, "heartbeat", "eva00001"),
    ]
    manifest = {
        "generated_at": now.isoformat(),
        "class_id": CLASS_ID,
        "session_id": SESSION_ID,
        "join_code": JOIN_CODE,
        "tablet_student_id": "fabio001",
        "expected": {
            "Sem sinal": ["Alice", "Fábio"],
            "Precisa de ti": ["Beatriz", "Carlos"],
            "A tropeçar": ["Diana"],
            "A fluir": ["Eva"],
            "explicit_help": "Beatriz",
        },
    }
    return classroom, session, events, manifest


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def seed(data_dir: Path, now: datetime) -> dict:
    if data_dir.exists() and any(data_dir.iterdir()):
        raise ValueError(f"o diretório de dados não está vazio: {data_dir}")
    classroom, session, events, manifest = build_fixture(now)
    write_json(data_dir / "classes" / f"{CLASS_ID}.json", classroom)
    write_json(data_dir / "sessions" / SESSION_ID / "session.json", session)
    events_path = data_dir / "sessions" / SESSION_ID / "events.jsonl"
    events_path.parent.mkdir(parents=True, exist_ok=True)
    events_path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in events),
        encoding="utf-8",
    )
    write_json(data_dir / "verification.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        required=True,
        help="Diretório novo ou vazio a usar em PAGECRAFT_DATA_DIR.",
    )
    args = parser.parse_args()
    now = datetime.now(timezone.utc).replace(microsecond=0)
    manifest = seed(args.data_dir.resolve(), now)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
