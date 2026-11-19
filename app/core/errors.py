"""Error aplikasi: pesan jelas + kode HTTP yang tepat."""


class AppError(Exception):
    status_code = 400

    def __init__(self, detail, extra=None):
        super().__init__(detail)
        self.detail = detail
        self.extra = extra or {}


class BadRequest(AppError):
    status_code = 400


class Unauthorized(AppError):
    status_code = 401


class Forbidden(AppError):
    status_code = 403


class NotFound(AppError):
    status_code = 404


class Conflict(AppError):
    status_code = 409


class ServerError(AppError):
    status_code = 500


class ServiceUnavailable(AppError):
    status_code = 503
