#!/usr/bin/env python3
import argparse, json, os, shutil
from datetime import datetime, timezone
from pathlib import Path


def now_iso():
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def load_json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text())


def save_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def infer_title_from_html(html_path: Path):
    text = html_path.read_text(errors="ignore")
    start = text.find("<title>")
    end = text.find("</title>")
    if start != -1 and end != -1 and end > start:
        return text[start + 7 : end].strip()
    return html_path.stem


def looks_like_pagecraft_repo(path: Path):
    return (path / "catalog.json").exists() and (path / "activities").is_dir()


def resolve_default_repo():
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


def main():
    p = argparse.ArgumentParser(
        description="Publish approved PageCraft activity to pagecraft catalog repo."
    )
    p.add_argument("--slug", required=True)
    p.add_argument("--html", required=True)
    p.add_argument("--md", required=True)
    p.add_argument("--docspec", required=True)
    p.add_argument("--design-spec")
    p.add_argument("--repo", default=str(resolve_default_repo()))
    p.add_argument("--maker", default="none")
    p.add_argument("--tags", default="")
    args = p.parse_args()

    repo = Path(args.repo)
    activities = repo / "activities"
    activities.mkdir(parents=True, exist_ok=True)
    dst = activities / args.slug
    dst.mkdir(parents=True, exist_ok=True)

    html = Path(args.html)
    md = Path(args.md)
    docspec = Path(args.docspec)
    design_spec = Path(args.design_spec) if args.design_spec else None

    shutil.copy2(html, dst / "index.html")
    shutil.copy2(md, dst / "teacher.md")
    shutil.copy2(docspec, dst / "docspec.json")
    if design_spec and design_spec.exists():
        shutil.copy2(design_spec, dst / "design-spec.json")

    doc = load_json(docspec, {})
    title = doc.get("topic") or infer_title_from_html(html)
    year = doc.get("ageRange") or ""
    duration = doc.get("duration")
    topic = doc.get("topic") or title
    age_range = doc.get("ageRange", "")

    tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    if not tags:
        tags = [args.maker] if args.maker and args.maker != "none" else []

    meta_path = dst / "meta.json"
    existing_meta = load_json(meta_path, {})
    created = existing_meta.get("createdAt") or now_iso()
    updated = now_iso()

    meta = {
        "slug": args.slug,
        "title": title,
        "year": year,
        "ageRange": age_range,
        "duration": duration,
        "topic": topic,
        "maker": args.maker,
        "createdAt": created,
        "updatedAt": updated,
        "status": "published",
        "tags": tags,
        "paths": {
            "activity": "./index.html",
            "teacher": "./teacher.md",
            "docspec": "./docspec.json",
            "designSpec": "./design-spec.json"
            if design_spec and design_spec.exists()
            else None,
        },
    }
    save_json(meta_path, meta)

    catalog_path = repo / "catalog.json"
    catalog = load_json(catalog_path, {"generatedAt": None, "count": 0, "items": []})
    items = catalog.get("items", [])
    item = {
        "slug": args.slug,
        "title": title,
        "year": year,
        "ageRange": age_range,
        "duration": duration,
        "maker": args.maker,
        "tags": tags,
        "createdAt": created,
        "url": f"./activities/{args.slug}/",
        "teacherUrl": f"./activities/{args.slug}/teacher.md",
        "docspecUrl": f"./activities/{args.slug}/docspec.json",
    }

    replaced = False
    for i, it in enumerate(items):
        if it.get("slug") == args.slug:
            items[i] = item
            replaced = True
            break
    if not replaced:
        items.append(item)

    catalog["items"] = sorted(items, key=lambda x: x.get("slug", ""))
    catalog["count"] = len(catalog["items"])
    catalog["generatedAt"] = updated
    save_json(catalog_path, catalog)

    print(f"Published {args.slug} to {dst}")


if __name__ == "__main__":
    main()
