from typing import Any, Dict, Optional


class CRMSatiroException(Exception):
    def __init__(
        self,
        message: str,
        error_code: str = "CRM_ERROR",
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}


class NotFoundErrorCRM(CRMSatiroException):
    def __init__(self, entity: str, record_id: str):
        super().__init__(
            message=f"Registro não encontrado em {entity}.",
            error_code="RECORD_NOT_FOUND",
            status_code=404,
            details={"entity": entity, "id": record_id},
        )


class IntegrityErrorCRM(CRMSatiroException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="INTEGRITY_CONSTRAINT_VIOLATION",
            status_code=409,
            details=details or {},
        )


class ValidationErrorCRM(CRMSatiroException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=422,
            details=details or {},
        )


class AuthenticationErrorCRM(CRMSatiroException):
    def __init__(self, message: str = "Credenciais inválidas ou sessão expirada."):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_FAILED",
            status_code=401,
        )


class PermissionDeniedErrorCRM(CRMSatiroException):
    def __init__(self, message: str = "Acesso negado para realizar esta operação."):
        super().__init__(
            message=message,
            error_code="PERMISSION_DENIED",
            status_code=403,
        )


class DBFStorageError(CRMSatiroException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="DBF_STORAGE_ERROR",
            status_code=500,
            details=details or {},
        )

