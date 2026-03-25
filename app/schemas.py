from pydantic import BaseModel, EmailStr
from typing import Optional


class AdminSignup(BaseModel):
    full_name: str
    email: EmailStr
    password: str


class AdminLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    admin: dict


class AdminMeResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    admin_code: str
    is_approved: bool
    display_name: Optional[str] = None
    phone: Optional[str] = None
    logo_url: Optional[str] = None


class MessageResponse(BaseModel):
    message: str


class ApproveAdminResponse(BaseModel):
    message: str
    admin_id: int
    is_approved: bool


class ProfileUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    phone: Optional[str] = None


class ProfileResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    admin_code: str
    is_approved: bool
    display_name: Optional[str] = None
    phone: Optional[str] = None
    logo_url: Optional[str] = None


class EACreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    mode: str = "signal"


class EAResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    ea_code: str
    mode: str
    is_active: bool


class LicenseCreateRequest(BaseModel):
    ea_id: int
    client_name: str
    client_email: EmailStr
    duration_days: int


class LicenseResponse(BaseModel):
    id: int
    client_name: str
    client_email: EmailStr
    license_key: str
    status: str
    duration_days: int
    ea_id: int


class LicenseValidateRequest(BaseModel):
    license_key: str


class LicenseValidateResponse(BaseModel):
    valid: bool
    message: str
    license_key: Optional[str] = None
    status: Optional[str] = None
    ea_id: Optional[int] = None


class ClientActivateRequest(BaseModel):
    license_key: str


class ClientActivateResponse(BaseModel):
    success: bool
    message: str
    license_key: Optional[str] = None
    ea_name: Optional[str] = None
    ea_code: Optional[str] = None
    client_name: Optional[str] = None
    client_email: Optional[str] = None


class ClientDashboardResponse(BaseModel):
    license_key: str
    client_name: str
    client_email: str
    status: str
    ea_name: str
    ea_code: str
    mode: str
    broker_name: Optional[str] = None
    mt_login: Optional[str] = None
    mt_server: Optional[str] = None
    is_connected: bool = False
    allowed_symbols: list[str] = []
    
class ClientMT5ConnectRequest(BaseModel):
    license_key: str
    mt_login: str
    mt_password: str
    mt_server: str
    broker_name: Optional[str] = None

class ClientMT5ConnectResponse(BaseModel):
    success: bool
    message: str
    license_key: str
    mt_login: Optional[str] = None
    mt_server: Optional[str] = None
    broker_name: Optional[str] = None
    is_connected: bool

class SignalCreateRequest(BaseModel):
    ea_id: int
    symbol: str
    action: str
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

class SignalResponse(BaseModel):
    id: int
    ea_id: int
    symbol: str
    action: str
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    status: str
    created_at: str


class ClientSignalResponse(BaseModel):
    id: int
    symbol: str
    action: str
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    status: str
    created_at: str

class ClientSymbolSettingSave(BaseModel):
    license_key: str
    symbol: str
    direction: str
    lot_size: str
    platform: str
    max_trades: str


class ClientSymbolSettingOut(BaseModel):
    symbol: str
    direction: str
    lot_size: str
    platform: str
    max_trades: str
    is_enabled: bool

class Config:
    from_attributes = True