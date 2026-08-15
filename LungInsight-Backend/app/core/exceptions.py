"""Custom application exceptions, mapped to HTTP responses in main.py."""


class AppError(Exception):
    """Base class for all application-level errors."""
    status_code = 500
    detail = "An unexpected error occurred."

    def __init__(self, detail: str | None = None):
        self.detail = detail or self.detail
        super().__init__(self.detail)


class EmailAlreadyRegisteredError(AppError):
    status_code = 409
    detail = "An account with this email already exists."


class InvalidCredentialsError(AppError):
    status_code = 401
    detail = "Incorrect email or password."


class InactiveUserError(AppError):
    status_code = 403
    detail = "This account has been deactivated."


class InvalidTokenError(AppError):
    status_code = 401
    detail = "Invalid or expired token."


class NotFoundError(AppError):
    status_code = 404
    detail = "Resource not found."


class ForbiddenError(AppError):
    status_code = 403
    detail = "You do not have permission to access this resource."


class InvalidFileError(AppError):
    status_code = 422
    detail = "Invalid file upload."


class InferenceServiceError(AppError):
    """Raised when the AI model-serving microservice is unreachable, times
    out, or returns an error. Mapped to 503 — this is a dependency being
    down, not a client mistake."""
    status_code = 503
    detail = "The AI prediction service is temporarily unavailable. Please try again shortly."


class RagServiceError(AppError):
    """Raised when the RAG chat microservice is unreachable, times out, or
    returns an error. Mapped to 503 for the same reason as InferenceServiceError."""
    status_code = 503
    detail = "The clinical assistant is temporarily unavailable. Please try again shortly."
