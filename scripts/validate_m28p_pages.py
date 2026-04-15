from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ACTIVITIES_DIR = ROOT / "activities"
EXPECTED_FILES = ["index.html", "page-2.html", "page-3.html", "page-4.html"]
VARIANTS = {
    item["filename"]: item
    for item in json.loads(
        (ROOT / "scripts" / "m28p_page_variants.json").read_text(encoding="utf-8")
    )
}
AO90_DENYLIST = [
    "objectivo",
    "objectivos",
    "actividade",
    "actividades",
    "activação",
    "interactiva",
    "interactivo",
    "selecção",
    "selecciona",
    "seleccionando",
    "correctamente",
    "direcção",
]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def word_from_meta(title: str) -> str:
    return title.split("—")[-1].strip().lower()


def ordered_dirs() -> list[Path]:
    found = []
    for meta_path in ACTIVITIES_DIR.glob("*/meta.json"):
        meta = read_json(meta_path)
        if isinstance(meta.get("order"), int) and 1 <= meta["order"] <= 28:
            found.append((meta["order"], meta_path.parent))
    found.sort(key=lambda item: item[0])
    return [path for _, path in found]


def main() -> int:
    errors: list[str] = []
    dirs = ordered_dirs()
    if len(dirs) != 28:
        errors.append(f"Expected 28 M28P folders, found {len(dirs)}")

    html_count = 0
    for activity_dir in dirs:
        meta = read_json(activity_dir / "meta.json")
        word = word_from_meta(meta["title"])
        expected_title = f"<title>M28P #{meta['order']} — {word} | PageCraft</title>"
        page_signatures = []
        for filename in EXPECTED_FILES:
            page_path = activity_dir / filename
            if not page_path.exists():
                errors.append(f"Missing {page_path.relative_to(ROOT)}")
                continue
            html_count += 1
            contents = page_path.read_text(encoding="utf-8")
            page_signatures.append(contents)
            if '<html lang="pt-PT">' not in contents:
                errors.append(f"lang missing in {page_path.relative_to(ROOT)}")
            if expected_title not in contents:
                errors.append(f"title mismatch in {page_path.relative_to(ROOT)}")
            if (
                "fonts.googleapis.com" in contents
                or "fonts.gstatic.com" in contents
                or "@import url(" in contents
            ):
                errors.append(
                    f"external font reference in {page_path.relative_to(ROOT)}"
                )
            if "http://" in contents or "https://" in contents:
                errors.append(f"external URL found in {page_path.relative_to(ROOT)}")
            if "skip-link" not in contents:
                errors.append(f"skip link missing in {page_path.relative_to(ROOT)}")
            if "--touch-size: 48px" not in contents:
                errors.append(
                    f"touch size token missing in {page_path.relative_to(ROOT)}"
                )
            if "prefers-reduced-motion" not in contents:
                errors.append(
                    f"reduced motion rule missing in {page_path.relative_to(ROOT)}"
                )
            variant = VARIANTS.get(filename)
            if variant:
                expected_visible = f'data-visible-units="{",".join(str(i) for i in variant["visibleUnits"])}"'
                expected_variant = f'data-page-variant="{filename}"'
                if expected_visible not in contents:
                    errors.append(
                        f"visible unit marker mismatch in {page_path.relative_to(ROOT)}"
                    )
                if expected_variant not in contents:
                    errors.append(
                        f"page variant marker missing in {page_path.relative_to(ROOT)}"
                    )
            lower_contents = contents.lower()
            for bad in AO90_DENYLIST:
                if bad in lower_contents:
                    errors.append(
                        f"AO90 denylist hit '{bad}' in {page_path.relative_to(ROOT)}"
                    )
                    break

        if len(set(page_signatures)) != len(EXPECTED_FILES):
            errors.append(f"duplicate page output in {activity_dir.relative_to(ROOT)}")

    if html_count != 112:
        errors.append(f"Expected 112 M28P HTML files, found {html_count}")

    report = {
        "folders": len(dirs),
        "htmlFiles": html_count,
        "errors": errors,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
