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
