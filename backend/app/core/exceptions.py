"""
Domain Exceptions — Typed error hierarchy for the platform.
"""
from fastapi import status


class HealthRiskException(Exception):
    """Base exception for all domain errors."""
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, detail: str = "An error occurred."):
        self.detail = detail
        super().__init__(detail)


class AuthenticationException(HealthRiskException):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "AUTHENTICATION_FAILED"


class AuthorizationException(HealthRiskException):
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "AUTHORIZATION_FAILED"


class NotFoundException(HealthRiskException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "NOT_FOUND"


class ValidationException(HealthRiskException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code = "VALIDATION_ERROR"


class ModelNotReadyException(HealthRiskException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code = "MODEL_NOT_READY"


class PredictionException(HealthRiskException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = "PREDICTION_FAILED"


class RAGException(HealthRiskException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = "RAG_PIPELINE_ERROR"
