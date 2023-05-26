from typing import Optional, Union
from pydantic import BaseModel

# Conceptual schemas

class Contract(BaseModel):
    trade_id: str
    contract_url: str
    contract_type: str

class Policies(BaseModel):
    user: Union[str, None]
    org: Union[str, None]
    aal: Union[int, None]
    extras: Union[str, None]

class Permission(BaseModel):
    target: str
    assigner: str
    assignee: Policies

class ContractToDelete(BaseModel):
    trade_id: str

class PermissionToDelete(BaseModel):
    target: str
    assigner: str
    assignee: Optional[Policies]

class RealmSettings(BaseModel):
    access_token_lifespan: int

class IdpSettings(BaseModel):
    auth_url: str
    token_url: str
    userinfo_url: str
    client_id: str
    client_secret: str

class ClientSettings(BaseModel):
    client_id: str
    client_secret: str

# Request / Response schemas

## API Common

class Response(BaseModel):
    message: str

class ErrorResponse(BaseModel):
    message: str
    detail: str

## Data API

class FederateRequest(BaseModel):
    access_token: str
    provider_id: str

class FederateResponse(BaseModel):
    access_token: str

class ConfirmAuthorizationRequest(BaseModel):
    access_token: str
    provider_id: str
    resource_url: str

class ConfirmAuthorizationResponse(BaseModel):
    contract: Contract

## Authorization API

class GetAuthorizationListResponse(BaseModel):
    permission: Permission
    contract: Optional[Contract]

class GetAuthorizationResponse(BaseModel):
    permission: Permission
    contract: Optional[Contract]

class RegisterAuthorizationRequest(BaseModel):
    permission: Permission
    contract: Optional[Contract]

class DeleteAuthorizationRequest(BaseModel):
    permission: PermissionToDelete
    contract: Optional[ContractToDelete]

## Provider GUI API

class GetAuthenticationRequestUrlRequest(BaseModel):
    url: str

class GetAuthenticationRequestUrlResponse(BaseModel):
    url: str

class GetTokenUsingAuthorizationCodeRequest(BaseModel):
    code: str
    url: str
    state: str

class GetTokenUsingAuthorizationCodeResponse(BaseModel):
    cadde_user_id: str

class GetSettingsResponse(BaseModel):
    realm_settings: RealmSettings
    client_settings: ClientSettings
    idp_settings: IdpSettings

class UpdateRealmSettingsRequest(BaseModel):
    access_token_lifespan: int

class UpdateIdpSettingsRequest(BaseModel):
    userinfo_url: str
