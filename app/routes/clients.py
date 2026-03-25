from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import License, ClientAccount, ClientSymbolSetting
from app.schemas import (
    ClientActivateRequest,
    ClientActivateResponse,
    ClientDashboardResponse,
    ClientMT5ConnectRequest,
    ClientMT5ConnectResponse,
    ClientSymbolSettingSave,
    ClientSymbolSettingOut,
)

router = APIRouter(tags=["Clients"])


@router.post("/client/activate", response_model=ClientActivateResponse)
def activate_client_license(
    payload: ClientActivateRequest,
    db: Session = Depends(get_db),
):
    license_obj = db.query(License).filter(
        License.license_key == payload.license_key
    ).first()

    if not license_obj:
        return {
            "success": False,
            "message": "Invalid license key",
            "license_key": None,
            "ea_name": None,
            "ea_code": None,
            "client_name": None,
            "client_email": None,
        }

    if license_obj.status != "active":
        return {
            "success": False,
            "message": "License is not active",
            "license_key": license_obj.license_key,
            "ea_name": None,
            "ea_code": None,
            "client_name": None,
            "client_email": None,
        }

    ea = license_obj.ea

    client_account = db.query(ClientAccount).filter(
        ClientAccount.license_id == license_obj.id
    ).first()

    if not client_account:
        client_account = ClientAccount(
            license_id=license_obj.id,
            mt_login=None,
            mt_password=None,
            mt_server=None,
            broker_name=None,
            is_connected=False,
        )
        db.add(client_account)
        db.commit()

    return {
        "success": True,
        "message": "License activated successfully",
        "license_key": license_obj.license_key,
        "ea_name": ea.name if ea else None,
        "ea_code": ea.ea_code if ea else None,
        "client_name": license_obj.client_name,
        "client_email": license_obj.client_email,
    }


@router.get("/client/dashboard/{license_key}", response_model=ClientDashboardResponse)
def get_client_dashboard(
    license_key: str,
    db: Session = Depends(get_db),
    x_device_id: Optional[str] = Header(default=None),
):
    license_obj = db.query(License).filter(
        License.license_key == license_key
    ).first()

    if not license_obj:
        raise HTTPException(status_code=404, detail="License not found")

    if not x_device_id:
        raise HTTPException(status_code=400, detail="Missing device ID")

    if not license_obj.device_id:
        license_obj.device_id = x_device_id
        db.commit()
        db.refresh(license_obj)
    elif license_obj.device_id != x_device_id:
        raise HTTPException(
            status_code=403,
            detail="License already in use on another device",
        )

    ea = license_obj.ea
    client_account = license_obj.client_account

    return {
        "license_key": license_obj.license_key,
        "client_name": license_obj.client_name,
        "client_email": license_obj.client_email,
        "status": license_obj.status,
        "ea_name": ea.name if ea else "",
        "ea_code": ea.ea_code if ea else "",
        "mode": ea.mode if ea else "signal",
        "broker_name": client_account.broker_name if client_account else None,
        "mt_login": client_account.mt_login if client_account else None,
        "mt_server": client_account.mt_server if client_account else None,
        "is_connected": client_account.is_connected if client_account else False,
        "allowed_symbols": [symbol.symbol for symbol in ea.symbols] if ea and ea.symbols else [],
    }


@router.post("/client/connect-mt5", response_model=ClientMT5ConnectResponse)
def connect_client_mt5(
    payload: ClientMT5ConnectRequest,
    db: Session = Depends(get_db),
):
    license_obj = db.query(License).filter(
        License.license_key == payload.license_key
    ).first()

    if not license_obj:
        raise HTTPException(status_code=404, detail="License not found")

    client_account = db.query(ClientAccount).filter(
        ClientAccount.license_id == license_obj.id
    ).first()

    if not client_account:
        client_account = ClientAccount(
            license_id=license_obj.id,
            mt_login=payload.mt_login,
            mt_password=payload.mt_password,
            mt_server=payload.mt_server,
            broker_name=payload.broker_name,
            is_connected=True,
        )
        db.add(client_account)
    else:
        client_account.mt_login = payload.mt_login
        client_account.mt_password = payload.mt_password
        client_account.mt_server = payload.mt_server
        client_account.broker_name = payload.broker_name
        client_account.is_connected = True

    db.commit()
    db.refresh(client_account)

    return {
        "success": True,
        "message": "MT5 credentials saved successfully",
        "license_key": license_obj.license_key,
        "mt_login": client_account.mt_login,
        "mt_server": client_account.mt_server,
        "broker_name": client_account.broker_name,
        "is_connected": client_account.is_connected,
    }


@router.get("/client/symbols/{license_key}", response_model=list[ClientSymbolSettingOut])
def get_client_symbol_settings(
    license_key: str,
    db: Session = Depends(get_db),
):
    license_obj = db.query(License).filter(
        License.license_key == license_key
    ).first()

    if not license_obj:
        raise HTTPException(status_code=404, detail="License not found")

    settings = (
        db.query(ClientSymbolSetting)
        .filter(ClientSymbolSetting.license_id == license_obj.id)
        .all()
    )
    return settings


@router.post("/client/symbols/save")
def save_client_symbol_setting(
    payload: ClientSymbolSettingSave,
    db: Session = Depends(get_db),
):
    license_obj = db.query(License).filter(
        License.license_key == payload.license_key
    ).first()

    if not license_obj:
        raise HTTPException(status_code=404, detail="License not found")

    existing = (
        db.query(ClientSymbolSetting)
        .filter(
            ClientSymbolSetting.license_id == license_obj.id,
            ClientSymbolSetting.symbol == payload.symbol,
        )
        .first()
    )

    if existing:
        existing.direction = payload.direction
        existing.lot_size = payload.lot_size
        existing.platform = payload.platform
        existing.max_trades = payload.max_trades
        existing.is_enabled = True
    else:
        existing = ClientSymbolSetting(
            license_id=license_obj.id,
            symbol=payload.symbol,
            direction=payload.direction,
            lot_size=payload.lot_size,
            platform=payload.platform,
            max_trades=payload.max_trades,
            is_enabled=True,
        )
        db.add(existing)

    db.commit()
    db.refresh(existing)

    return {
        "message": "Symbol configuration saved successfully",
        "symbol": existing.symbol,
    }


@router.post("/admin/reset-device/{license_key}")
def reset_license_device(
    license_key: str,
    db: Session = Depends(get_db),
):
    license_obj = db.query(License).filter(
        License.license_key == license_key
    ).first()

    if not license_obj:
        raise HTTPException(status_code=404, detail="License not found")

    license_obj.device_id = None
    db.commit()

    return {"message": "Device reset successful"}