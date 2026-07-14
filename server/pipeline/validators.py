"""Validação determinista do HTML gerado (pré-Evaluator).

Verifica os invariantes que não precisam de IA: self-contained, offline,
acessibilidade básica. O resultado alimenta o prompt do Evaluator e o
repair loop.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class ValidationReport:
    passed: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def error(self, msg: str) -> None:
        self.errors.append(msg)
        self.passed = False

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def as_dict(self) -> dict:
        return {"passed": self.passed, "errors": self.errors, "warnings": self.warnings}


EXTERNAL_REF = re.compile(
    r"""(?:src|href)\s*=\s*["'](?:https?:)?//""", re.IGNORECASE
)
EXTERNAL_IMPORT = re.compile(r"""@import\s+(?:url\()?["']?https?://""", re.IGNORECASE)
FETCH_CALL = re.compile(r"""\b(?:fetch|XMLHttpRequest|WebSocket|EventSource)\s*\(""")


def validate_activity_html(html: str) -> ValidationReport:
    report = ValidationReport()
    lower = html.lower()

    if "<!doctype html" not in lower:
        report.error("falta <!doctype html>")
    if not re.search(r"<html[^>]*lang\s*=\s*[\"']pt", lower):
        report.error('falta lang="pt-PT" no <html>')
    if "viewport" not in lower:
        report.error("falta meta viewport")

    if EXTERNAL_REF.search(html):
        report.error("referência externa (src/href para http(s)://) — a atividade tem de ser self-contained")
    if EXTERNAL_IMPORT.search(html):
        report.error("@import remoto no CSS")
    if "fonts.googleapis" in lower or "cdn." in lower or "unpkg.com" in lower or "jsdelivr" in lower:
        report.error("dependência de CDN/fontes remotas")
    if FETCH_CALL.search(html):
        report.error("chamadas de rede no JS (fetch/XHR/WebSocket) — a atividade deve funcionar offline; telemetria só via postMessage")

    if ":focus-visible" not in lower:
        report.warn("sem estilos :focus-visible")
    if "prefers-reduced-motion" not in lower:
        report.warn("sem suporte prefers-reduced-motion")
    if "aria-live" not in lower:
        report.warn("sem aria-live para feedback dinâmico")
    if re.search(r"\bwrong\b|errado[!.]", lower):
        report.warn("possível microcopy punitivo ('errado')")

    if len(html) < 3000:
        report.error(f"HTML demasiado curto ({len(html)} chars) para uma atividade completa")

    return report
