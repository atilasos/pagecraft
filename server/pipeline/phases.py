"""Montagem de prompts por fase do pipeline.

Cada fase junta: identidade (system prompt) + referências relevantes +
artefactos das fases anteriores + contexto de conhecimento (AE + MEM).
"""

from __future__ import annotations

import json
from pathlib import Path


def _read(path: Path) -> str:
    return path.read_text("utf-8")


class PromptLibrary:
    def __init__(self, prompts_dir: Path):
        self.dir = Path(prompts_dir)
        self.identities = {
            name: _read(self.dir / f"{name}.md")
            for name in ("architect", "designer", "builder", "proofreader", "evaluator")
        }
        refs = self.dir / "references"
        self.docspec_schema_doc = _read(refs / "docspec-schema.md")
        self.age_adaptation = _read(refs / "age-adaptation.md")
        self.interaction_patterns = _read(refs / "interaction-patterns.md")
        self.maker_patterns = _read(refs / "maker-patterns.md")
        self.srtc_examples = _read(refs / "srtc-examples.md")
        self.bridge_contract = _read(refs / "bridge-contract.md")
        self.template_base = _read(self.dir / "template-base.html")

    # ---- fases ----

    def architect(
        self,
        *,
        topic: str,
        subject: str,
        year: int,
        duration: int,
        maker: str | None,
        ae_excerpt: str,
        ae_citation: str,
        mem_context: str,
    ) -> tuple[str, str]:
        maker_line = f"Inclui um desafio maker do tipo: {maker}." if maker else "Sem componente maker."
        parts = [
            f"# Pedido\n\nCria um DocSpec-AM para uma atividade de {subject}, {year}.º ano, "
            f"sobre «{topic}», com duração de {duration} minutos. {maker_line}",
            "Responde apenas com o JSON do DocSpec-AM.",
            f"# Documentação do schema DocSpec-AM\n\n{self.docspec_schema_doc}",
            f"# Exemplos SRTC-A\n\n{self.srtc_examples}",
            f"# Adaptação à idade\n\n{self.age_adaptation}",
        ]
        if maker:
            parts.append(f"# Padrões maker\n\n{self.maker_patterns}")
        if ae_excerpt:
            parts.append(
                "# Aprendizagens Essenciais oficiais (usa descritores REAIS daqui; "
                f"cita a fonte em curriculum.ae[].source como: {ae_citation})\n\n{ae_excerpt}"
            )
        else:
            parts.append(
                "# Aviso\n\nNão há documento AE local para esta disciplina/ano. Usa apenas AE que "
                "conheças como reais e marca source como 'verificar-DGE'."
            )
        if mem_context:
            parts.append(
                "# Princípios e instrumentos MEM (da wiki do professor — fundamenta memAlignment nisto)\n\n"
                + mem_context
            )
        return self.identities["architect"], "\n\n---\n\n".join(parts)

    def designer(self, docspec: dict) -> tuple[str, str]:
        prompt = (
            "# Pedido\n\nCria o design-spec JSON para a atividade descrita neste DocSpec-AM. "
            "Responde apenas com JSON.\n\n"
            f"# DocSpec-AM\n\n```json\n{json.dumps(docspec, ensure_ascii=False, indent=2)}\n```\n\n"
            f"# Adaptação à idade\n\n{self.age_adaptation}"
        )
        return self.identities["designer"], prompt

    def builder(
        self,
        docspec: dict,
        design_spec: dict,
        *,
        repair_ticket: dict | None = None,
        previous_html: str | None = None,
    ) -> tuple[str, str]:
        parts = [
            "# Pedido\n\nGera a atividade HTML completa (self-contained) para este DocSpec-AM e design-spec. "
            'Responde com JSON: {"html": "<!doctype html>...", "notes": "..."}.',
            f"# DocSpec-AM\n\n```json\n{json.dumps(docspec, ensure_ascii=False, indent=2)}\n```",
            f"# design-spec\n\n```json\n{json.dumps(design_spec, ensure_ascii=False, indent=2)}\n```",
            f"# Template base (usa como esqueleto: estrutura, tokens CSS, bridge de telemetria)\n\n"
            f"```html\n{self.template_base}\n```",
            f"# Padrões de interação\n\n{self.interaction_patterns}",
            f"# Telemetria PageCraftBridge (obrigatório instrumentar)\n\n{self.bridge_contract}",
            f"# Adaptação à idade\n\n{self.age_adaptation}",
        ]
        if repair_ticket:
            parts.insert(
                1,
                "# REPARAÇÃO\n\nA versão anterior falhou a avaliação. Corrige TODOS os problemas "
                f"seguintes sem regredir o resto:\n\n```json\n{json.dumps(repair_ticket, ensure_ascii=False, indent=2)}\n```",
            )
        if previous_html:
            parts.append(f"# HTML anterior (base para reparação)\n\n```html\n{previous_html}\n```")
        return self.identities["builder"], "\n\n---\n\n".join(parts)

    def proofreader(self, docspec: dict, html: str) -> tuple[str, str]:
        prompt = (
            "# Pedido\n\nRevê o texto visível desta atividade (pt-PT AO90, adequação à idade). "
            "Responde apenas com o JSON de proofread.\n\n"
            f"# DocSpec-AM (contexto: idade {docspec.get('ageRange', '?')})\n\n"
            f"```json\n{json.dumps({k: docspec.get(k) for k in ('topic', 'ageRange', 'objectives')}, ensure_ascii=False)}\n```\n\n"
            f"# HTML da atividade\n\n```html\n{html}\n```"
        )
        return self.identities["proofreader"], prompt

    def evaluator(self, docspec: dict, html: str, validation: dict, proofread: dict) -> tuple[str, str]:
        prompt = (
            "# Pedido\n\nAvalia esta atividade contra o DocSpec-AM. Não tens browser: faz análise "
            "estática rigorosa do código (interações implementadas? constraint descoberto? diferenciação real? "
            "acessibilidade?). Considera também o relatório determinista e o proofread. "
            "Responde apenas com o JSON de avaliação.\n\n"
            f"# DocSpec-AM\n\n```json\n{json.dumps(docspec, ensure_ascii=False, indent=2)}\n```\n\n"
            f"# Relatório determinista (self-contained/offline/a11y)\n\n```json\n{json.dumps(validation, ensure_ascii=False)}\n```\n\n"
            f"# Proofread\n\n```json\n{json.dumps(proofread, ensure_ascii=False)}\n```\n\n"
            f"# HTML da atividade\n\n```html\n{html}\n```"
        )
        return self.identities["evaluator"], prompt
