"""Erros de domínio expostos pelo módulo da Sessão de aula."""


class ClassroomError(Exception):
    """Base dos erros que a camada de transporte pode traduzir."""


class SessionNotFoundError(ClassroomError):
    pass


class SessionClosedError(ClassroomError):
    pass


class StudentNotInRosterError(ClassroomError):
    pass


class IdentityAlreadyClaimedError(ClassroomError):
    pass


class InvalidPitItemError(ClassroomError):
    pass


class InvalidSessionEventError(ClassroomError):
    pass


class CompositionChangedError(ClassroomError):
    def __init__(self, event_ids: list[str], group: dict):
        super().__init__("O professor alterou os participantes. Estas respostas mantêm o grupo anterior.")
        self.event_ids = event_ids
        self.group = group
