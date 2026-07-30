#!/usr/bin/env python3
"""Invólucro CLI do ato de publicação fornecido pelo repositório PageCraft."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import types
from pathlib import Path
from typing import Any, Callable


PublishActivity = Callable[..., dict[str, Any]]


class PublicationModuleError(RuntimeError):
    """O repositório escolhido não expõe o contrato de publicação esperado."""


def looks_like_pagecraft_repo(path: Path) -> bool:
    return (path / "catalog.json").exists() and (path / "activities").is_dir()


def resolve_default_repo() -> Path:
    for key in ("PAGECRAFT_REPO", "PAGECRAFT_WORKSPACE"):
        value = os.environ.get(key)
        if not value:
            continue
        candidate = Path(value).expanduser().resolve()
        if looks_like_pagecraft_repo(candidate):
            return candidate
        if looks_like_pagecraft_repo(candidate / "pagecraft"):
            return candidate / "pagecraft"

    cwd = Path.cwd().resolve()
    if looks_like_pagecraft_repo(cwd):
        return cwd
    if looks_like_pagecraft_repo(cwd.parent):
        return cwd.parent

    return Path.home() / ".openclaw" / "workspace" / "pagecraft"


def load_publication_act(repo: Path) -> PublishActivity:
    """Carrega o ato canónico diretamente do repositório indicado."""
    server_dir = repo / "server"
    module_path = server_dir / "publish.py"
    if not module_path.is_file():
        raise PublicationModuleError(
            f"módulo de publicação não encontrado em {module_path}"
        )

    package_name = "_pagecraft_repository_server"
    package = types.ModuleType(package_name)
    package.__path__ = [str(server_dir)]  # type: ignore[attr-defined]
    package.__package__ = package_name
    sys.modules[package_name] = package

    module_name = f"{package_name}.publish"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise PublicationModuleError(
            f"não foi possível carregar o módulo de publicação em {module_path}"
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        raise PublicationModuleError(
            f"módulo de publicação desalinhado em {module_path}: {exc}"
        ) from exc

    publish_activity = getattr(module, "publish_activity", None)
    regenerate_catalog = getattr(module, "regenerate_catalog", None)
    if not callable(publish_activity) or not callable(regenerate_catalog):
        raise PublicationModuleError(
            "módulo de publicação desalinhado: são esperadas as operações "
            "publish_activity e regenerate_catalog"
        )
    return publish_activity


def _read_text(path_value: str, label: str) -> str:
    path = Path(path_value).expanduser().resolve()
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"não foi possível ler {label} em {path}: {exc}") from exc


def _read_json(path_value: str, label: str) -> dict[str, Any]:
    path = Path(path_value).expanduser().resolve()
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"não foi possível ler {label} em {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} tem de conter um objeto JSON: {path}")
    return value


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Publica uma atividade aprovada através do repositório PageCraft."
    )
    parser.add_argument("--slug", required=True)
    parser.add_argument("--html", required=True)
    parser.add_argument("--md", required=True)
    parser.add_argument("--docspec", required=True)
    parser.add_argument("--design-spec")
    parser.add_argument("--repo", default=str(resolve_default_repo()))
    parser.add_argument("--maker")
    parser.add_argument("--tags")
    return parser


def main() -> None:
    parser = _parser()
    args = parser.parse_args()
    repo = Path(args.repo).expanduser().resolve()

    try:
        publish_activity = load_publication_act(repo)
        teacher_md = _read_text(args.md, "guia do professor")
        docspec = _read_json(args.docspec, "DocSpec")
        design_spec = (
            _read_json(args.design_spec, "Design Spec") if args.design_spec else None
        )
        html_path = Path(args.html).expanduser().resolve()
        if not html_path.is_file():
            raise ValueError(f"HTML não encontrado em {html_path}")
    except (PublicationModuleError, ValueError) as exc:
        parser.error(str(exc))

    tags = (
        [tag.strip() for tag in args.tags.split(",") if tag.strip()]
        if args.tags is not None
        else None
    )
    publish_activity(
        repo,
        args.slug,
        html_path,
        docspec,
        teacher_md,
        design_spec,
        maker=args.maker,
        tags=tags,
    )
    print(f"Publicada {args.slug} em {repo / 'activities' / args.slug}")


if __name__ == "__main__":
    main()
