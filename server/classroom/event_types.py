"""Vocabulário único dos Acontecimentos de sessão.

Este módulo descreve o contrato público consultado pela ingestão, emissão,
visibilidade dos streams e relatórios da Sessão de aula.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, Mapping


EVENT_AUTHORS = frozenset({"activity", "student", "teacher", "assistant", "session"})
EVENT_ROLES = frozenset({"teacher", "student"})
_EVIDENCE_AUTHORS = frozenset({"activity", "student"})
_NAME = re.compile(r"^[a-z][a-z0-9_]*$")


@dataclass(frozen=True)
class SessionEventType:
    """Declara um tipo de Acontecimento de sessão."""

    name: str
    authors: frozenset[str]
    student_visible: bool
    is_evidence: bool
    in_timeline: bool
    bridge_name: str | None
    payload_fields: Mapping[str, str]

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not _NAME.fullmatch(self.name):
            raise ValueError("o nome interno tem de ser snake_case não vazio")
        authors = frozenset(self.authors)
        if not authors or not authors <= EVENT_AUTHORS:
            raise ValueError("a entrada tem de declarar pelo menos um autor conhecido")
        object.__setattr__(self, "authors", authors)
        if not all(
            isinstance(flag, bool)
            for flag in (self.student_visible, self.is_evidence, self.in_timeline)
        ):
            raise ValueError("visibilidade, Evidência e linha do tempo têm de ser booleanos")
        if self.is_evidence and (
            not authors <= _EVIDENCE_AUTHORS or not self.in_timeline
        ):
            raise ValueError("Evidência tem de ser trabalho da criança visível na linha do tempo")
        if self.bridge_name is not None:
            if not isinstance(self.bridge_name, str) or not _NAME.fullmatch(self.bridge_name):
                raise ValueError("o nome na ponte tem de ser snake_case")
            if not self.student_visible:
                raise ValueError("um acontecimento invisível ao aluno não pode entrar na atividade")
        if not isinstance(self.payload_fields, Mapping):
            raise ValueError("a documentação do payload tem de ser um mapa")
        for field, description in self.payload_fields.items():
            if (
                not isinstance(field, str)
                or not _NAME.fullmatch(field)
                or not isinstance(description, str)
                or not description.strip()
            ):
                raise ValueError("cada campo do payload precisa de nome e documentação")

    def to_dict(self) -> dict:
        """Representação estável e segura para transportar até ao browser."""
        return {
            "name": self.name,
            "authors": sorted(self.authors),
            "student_visible": self.student_visible,
            "evidence": self.is_evidence,
            "timeline": self.in_timeline,
            "bridge_name": self.bridge_name,
            "payload": dict(self.payload_fields),
        }


class SessionEventRegistry:
    """Interface de consulta, independente da representação do registo."""

    def __init__(self, entries: Iterable[SessionEventType]):
        self._entries = tuple(entries)
        self._by_name = {entry.name: entry for entry in self._entries}
        if len(self._by_name) != len(self._entries):
            raise ValueError("cada acontecimento precisa de um nome interno único")
        bridge_names = [entry.bridge_name for entry in self._entries if entry.bridge_name]
        if len(set(bridge_names)) != len(bridge_names):
            raise ValueError("cada nome na ponte tem de identificar um único acontecimento")

    def all(self) -> tuple[SessionEventType, ...]:
        return self._entries

    def get(self, name: str) -> SessionEventType | None:
        return self._by_name.get(name)

    def by_author(self, author: str) -> tuple[SessionEventType, ...]:
        if author not in EVENT_AUTHORS:
            raise ValueError(f"autor desconhecido: {author}")
        return tuple(entry for entry in self._entries if author in entry.authors)

    def visible_to(self, role: str) -> tuple[SessionEventType, ...]:
        if role not in EVENT_ROLES:
            raise ValueError(f"papel desconhecido: {role}")
        if role == "teacher":
            return self._entries
        return tuple(entry for entry in self._entries if entry.student_visible)

    def evidence(self) -> tuple[SessionEventType, ...]:
        return tuple(entry for entry in self._entries if entry.is_evidence)

    def timeline(self) -> tuple[SessionEventType, ...]:
        return tuple(entry for entry in self._entries if entry.in_timeline)

    def declaration(self) -> list[dict]:
        return [entry.to_dict() for entry in self._entries]


def _event(
    name: str,
    author: str,
    *,
    student_visible: bool = False,
    evidence: bool = False,
    timeline: bool = True,
    bridge_name: str | None = None,
    payload: Mapping[str, str] | None = None,
) -> SessionEventType:
    return SessionEventType(
        name=name,
        authors=frozenset({author}),
        student_visible=student_visible,
        is_evidence=evidence,
        in_timeline=timeline,
        bridge_name=bridge_name,
        payload_fields=payload or {},
    )


SESSION_EVENT_TYPES = SessionEventRegistry(
    (
        _event(
            "joined",
            "session",
            payload={"display_name": "Nome apresentado pela criança nesta sessão."},
        ),
        _event(
            "activity_loaded",
            "activity",
            payload={"title": "Título apresentado pela atividade carregada."},
        ),
        _event("heartbeat", "activity", timeline=False),
        _event("unit_started", "activity", evidence=True),
        _event(
            "attempt",
            "activity",
            evidence=True,
            payload={
                "correct": "Indica se a tentativa corresponde à resposta esperada.",
                "detail": "Descrição curta e opcional da tentativa observada.",
            },
        ),
        _event(
            "discovery",
            "activity",
            evidence=True,
            payload={"message": "Descrição curta da descoberta feita pela criança."},
        ),
        _event(
            "assessment_result",
            "activity",
            evidence=True,
            payload={
                "result": "Resultado observável do item de avaliação.",
                "detail": "Contexto curto e opcional sobre o resultado.",
            },
        ),
        _event(
            "feedback_request",
            "activity",
            evidence=True,
            payload={
                "question": "Pergunta ou tarefa apresentada à criança.",
                "answer": "Resposta dada pela criança.",
                "expected": "Resposta de referência indicada pela atividade.",
            },
        ),
        _event(
            "help_needed",
            "activity",
            evidence=True,
            payload={"note": "Contexto curto e opcional sobre o pedido de ajuda."},
        ),
        _event(
            "share_requested",
            "activity",
            evidence=True,
            payload={"what": "Trabalho que a criança quer levar ao momento de comunicação."},
        ),
        _event(
            "ai_feedback",
            "assistant",
            student_visible=True,
            bridge_name="ai_feedback",
            payload={
                "text": "Feedback formativo apresentado à criança.",
                "unit_id": "Unidade da atividade a que o feedback diz respeito.",
                "source": "Origem do texto: assistente, cache ou resposta de contingência.",
            },
        ),
        _event(
            "feedback_timeout",
            "assistant",
            payload={
                "unit_id": "Unidade cujo pedido excedeu o tempo disponível.",
                "error": "Descrição técnica da falha para diagnóstico.",
                "payload": "Pedido original que não obteve resposta em tempo útil.",
            },
        ),
        _event(
            "feedback_dropped",
            "assistant",
            payload={
                "unit_id": "Unidade do pedido descartado.",
                "reason": "Motivo pelo qual o pedido não foi processado.",
            },
        ),
        _event(
            "feedback_error",
            "assistant",
            payload={
                "error": "Descrição técnica da falha para diagnóstico.",
                "unit_id": "Unidade a que a falha diz respeito.",
            },
        ),
        _event(
            "teacher_message",
            "teacher",
            student_visible=True,
            payload={"text": "Mensagem enviada pelo professor."},
        ),
        _event(
            "teacher_highlight",
            "teacher",
            student_visible=True,
            bridge_name="highlight",
            payload={
                "unit_id": "Unidade para a qual o professor chama a atenção.",
                "unit_label": "Nome legível da unidade apresentado à criança.",
            },
        ),
        _event("freeze_screens", "teacher", student_visible=True),
        _event("unfreeze_screens", "teacher", student_visible=True),
        _event(
            "identity_released",
            "teacher",
            payload={
                "reset_progress": (
                    "Repõe números, Evidência e Plano individual de trabalho quando verdadeiro; "
                    "por omissão mantém o progresso."
                )
            },
        ),
        _event(
            "pit_updated",
            "student",
            student_visible=True,
            evidence=True,
            payload={
                "id": "Identificador estável do item do Plano individual de trabalho.",
                "student_id": "Identificador da criança autora do item.",
                "text": "Formulação do trabalho proposta pela criança.",
                "previous_status": (
                    "Estado anterior do item, ou nulo quando o item é criado."
                ),
                "status": "Estado atual do item no plano.",
                "updated_at": "Instante da alteração, em formato ISO 8601.",
            },
        ),
        _event("session_closed", "session", student_visible=True),
    )
)
