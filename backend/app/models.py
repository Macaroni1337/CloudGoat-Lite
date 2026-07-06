from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenExchangeRequest(BaseModel):
    client_id: str
    client_secret: str


class RoleAssignmentCreate(BaseModel):
    principal_type: str  # "user" or "service_principal"
    principal_id: int
    role: str            # "Reader" | "Contributor" | "Owner"
    scope: str            # resource group name or "subscription"


class LogoImportRequest(BaseModel):
    url: str
