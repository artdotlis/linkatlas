from mpyflow.shared.errors.exception import KnownException


class BootstrapEx(KnownException):
    pass


class DatabaseEx(KnownException):
    pass


class WrongContextEx(KnownException):
    pass


class SessionCreationEx(KnownException):
    pass


class RequestURIEx(KnownException):
    pass


class ValidationEx(KnownException):
    pass
