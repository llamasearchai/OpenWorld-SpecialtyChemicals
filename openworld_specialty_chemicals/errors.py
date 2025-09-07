from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class ErrorCode(IntEnum):
    OK = 0
    GENERIC = 1
    USAGE = 2
    NOT_FOUND = 3
    VALIDATION = 4
    NETWORK = 5
    PERMISSION = 6
    TIMEOUT = 7
    DEPENDENCY_MISSING = 8


class CLIError(Exception):
    code = ErrorCode.GENERIC


class UsageError(CLIError):
    code = ErrorCode.USAGE


class NotFoundError(CLIError):
    code = ErrorCode.NOT_FOUND


class ValidationError(CLIError):
    code = ErrorCode.VALIDATION


class NetworkError(CLIError):
    code = ErrorCode.NETWORK


class PermissionError_(CLIError):
    code = ErrorCode.PERMISSION


class TimeoutError_(CLIError):
    code = ErrorCode.TIMEOUT


class DependencyMissingError(CLIError):
    code = ErrorCode.DEPENDENCY_MISSING


@dataclass
class ErrorInfo:
    code: ErrorCode
    message: str


def map_exception(exc: Exception) -> ErrorInfo:
    if isinstance(exc, CLIError):
        return ErrorInfo(exc.code, str(exc))
    if isinstance(exc, FileNotFoundError):
        return ErrorInfo(ErrorCode.NOT_FOUND, str(exc))
    if isinstance(exc, PermissionError):
        return ErrorInfo(ErrorCode.PERMISSION, str(exc))
    if isinstance(exc, TimeoutError):
        return ErrorInfo(ErrorCode.TIMEOUT, str(exc))
    if isinstance(exc, ImportError):
        return ErrorInfo(ErrorCode.DEPENDENCY_MISSING, str(exc))
    # Fallback
    return ErrorInfo(ErrorCode.GENERIC, str(exc))

