from __future__ import annotations


class AppError(Exception):
    status_code = 500

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class BadRequestError(AppError):
    status_code = 400


class NotFoundError(AppError):
    status_code = 404


class UpstreamTimeoutError(AppError):
    status_code = 408


class UpstreamBadResponseError(AppError):
    status_code = 502
