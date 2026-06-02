"""
Role-Based Access Control (RBAC)
Defines roles, permissions, and FastAPI dependency for authorization.
"""
from enum import Enum
from typing import Set
from fastapi import Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.security import decode_token
from app.core.exceptions import AuthenticationException, AuthorizationException

security_scheme = HTTPBearer()


class Role(str, Enum):
    ADMIN = "admin"
    CLINICIAN = "clinician"
    RESEARCHER = "researcher"
    PATIENT = "patient"
    READONLY = "readonly"


# Permission definitions
class Permission(str, Enum):
    # Predictions
    PREDICT_READ = "predict:read"
    PREDICT_WRITE = "predict:write"
    # Patients
    PATIENT_READ = "patient:read"
    PATIENT_WRITE = "patient:write"
    PATIENT_DELETE = "patient:delete"
    # Models
    MODEL_READ = "model:read"
    MODEL_TRAIN = "model:train"
    MODEL_DEPLOY = "model:deploy"
    # Explanations
    EXPLAIN_READ = "explain:read"
    # RAG / LLM
    RAG_QUERY = "rag:query"
    RAG_INGEST = "rag:ingest"
    # Admin
    USER_MANAGE = "user:manage"
    AUDIT_READ = "audit:read"


# Role → Permission mapping
ROLE_PERMISSIONS: dict[Role, Set[Permission]] = {
    Role.ADMIN: set(Permission),  # All permissions
    Role.CLINICIAN: {
        Permission.PREDICT_READ,
        Permission.PREDICT_WRITE,
        Permission.PATIENT_READ,
        Permission.PATIENT_WRITE,
        Permission.EXPLAIN_READ,
        Permission.RAG_QUERY,
        Permission.MODEL_READ,
    },
    Role.RESEARCHER: {
        Permission.PREDICT_READ,
        Permission.PATIENT_READ,
        Permission.EXPLAIN_READ,
        Permission.RAG_QUERY,
        Permission.RAG_INGEST,
        Permission.MODEL_READ,
        Permission.MODEL_TRAIN,
    },
    Role.PATIENT: {
        Permission.PREDICT_READ,
        Permission.EXPLAIN_READ,
        Permission.RAG_QUERY,
    },
    Role.READONLY: {
        Permission.PREDICT_READ,
        Permission.EXPLAIN_READ,
    },
}


def get_permissions_for_role(role: Role) -> Set[Permission]:
    return ROLE_PERMISSIONS.get(role, set())


def has_permission(role: Role, permission: Permission) -> bool:
    return permission in get_permissions_for_role(role)


# ── FastAPI Dependencies ──────────────────────────────────────────────

class TokenData:
    def __init__(self, user_id: str, email: str, role: Role):
        self.user_id = user_id
        self.email = email
        self.role = role
        self.permissions = get_permissions_for_role(role)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security_scheme),
) -> TokenData:
    """Decode JWT and return current user token data."""
    payload = decode_token(credentials.credentials)
    user_id = payload.get("sub")
    email = payload.get("email", "")
    role_str = payload.get("role", Role.READONLY.value)

    if not user_id:
        raise AuthenticationException("Token missing subject claim.")

    try:
        role = Role(role_str)
    except ValueError:
        role = Role.READONLY

    return TokenData(user_id=user_id, email=email, role=role)


def require_permission(permission: Permission):
    """FastAPI dependency factory — enforces a specific permission."""
    async def _check(current_user: TokenData = Depends(get_current_user)) -> TokenData:
        if permission not in current_user.permissions:
            raise AuthorizationException(
                f"Role '{current_user.role}' lacks permission '{permission}'."
            )
        return current_user
    return _check


def require_role(*roles: Role):
    """FastAPI dependency factory — enforces one of the given roles."""
    async def _check(current_user: TokenData = Depends(get_current_user)) -> TokenData:
        if current_user.role not in roles:
            raise AuthorizationException(
                f"Access restricted. Required roles: {[r.value for r in roles]}"
            )
        return current_user
    return _check
