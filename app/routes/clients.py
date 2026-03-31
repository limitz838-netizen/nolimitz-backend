import requests
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from app.models import TradeExecution
from app.schemas import TradeExecutionResponse
from app.schemas import ClientExecutionToggleRequest
from app.database import get_db
from app.models import License, ClientAccount, ClientSymbolSetting
from app.schemas import (
    ClientActivateRequest,
    ClientActivateResponse,
    ClientDashboardResponse,
    ClientMT5ConnectRequest,
    ClientMT5ConnectResponse,
    ClientMT5SaveRequest,
    ClientMT5Response,
    ClientMT5StatusResponse,
    ClientSymbolSettingSave,
    ClientSymbolSettingOut,
    TradeExecutionResponse,
    ClientExecutionToggleRequest,
)

def verify_mt5_credentials(mt_login: str, mt_password: str, mt_server: str):
    try:
        res = requests.post(
            "http://127.0.0.1:8011/verify-mt5",
            json={
                "login": str(mt_login),
                "password": mt_password,
                "server": mt_server,
            },
            timeout=20,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"MT5 verifier unavailable: {str(e)}"
        )

    if not res.ok:
        raise HTTPException(
            status_code=500,
            detail=f"MT5 verifier error: {res.text}"
        )

    data = res.json()

    if not data.get("success"):
        raise HTTPException(
            status_code=400,
            detail=data.get("message", "MT5 login failed")
        )

    return data

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
    print("DEVICE ID HEADER:", x_device_id)
    print("LICENSE KEY RECEIVED:", license_key)

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

    try:
        verify_res = requests.post(
            "http://127.0.0.1:8011/verify-mt5",
            json={
                "mt_login": payload.mt_login,
                "mt_password": payload.mt_password,
                "mt_server": payload.mt_server,
            },
            timeout=15,
        )
        verify_data = verify_res.json()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"MT5 verifier unavailable: {str(e)}"
        )

    if not verify_data.get("valid"):
        raise HTTPException(
            status_code=400,
            detail=verify_data.get("message", "MT5 login failed")
        )

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
        "message": "MT5 connected successfully",
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

@router.post("/client/mt5/save", response_model=ClientMT5StatusResponse)
def save_client_mt5_settings(
    data: ClientMT5SaveRequest,
    db: Session = Depends(get_db),
):
    license_obj = db.query(License).filter(
        License.license_key == data.license_key
    ).first()

    if not license_obj:
        raise HTTPException(status_code=404, detail="Invalid license key")

    verify_data = verify_mt5_credentials(
        data.mt_login,
        data.mt_password,
        data.mt_server,
    )

    account = db.query(ClientAccount).filter(
        ClientAccount.license_id == license_obj.id
    ).first()

    if account:
        account.mt_login = data.mt_login
        account.mt_password = data.mt_password
        account.mt_server = data.mt_server
        account.execute_trades = data.execute_trades
        account.lot_size = data.lot_size
        account.is_connected = True
        account.broker_name = verify_data.get("server")
    else:
        account = ClientAccount(
            license_id=license_obj.id,
            mt_login=data.mt_login,
            mt_password=data.mt_password,
            mt_server=data.mt_server,
            execute_trades=data.execute_trades,
            lot_size=data.lot_size,
            is_connected=True,
            broker_name=verify_data.get("server"),
        )
        db.add(account)

    db.commit()
    db.refresh(account)

    return {
        "saved": True,
        "message": "MT5 settings saved successfully"
    }

@router.post("/client/connect-mt5", response_model=ClientMT5StatusResponse)
def connect_client_mt5(
    data: ClientMT5SaveRequest,
    db: Session = Depends(get_db),
):
    return save_client_mt5_settings(data, db)

@router.get("/client/mt5/{license_key}", response_model=ClientMT5Response)
def get_client_mt5_settings(
    license_key: str,
    db: Session = Depends(get_db),
):
    license_obj = db.query(License).filter(
        License.license_key == license_key
    ).first()

    if not license_obj:
        raise HTTPException(status_code=404, detail="Invalid license key")

    account = db.query(ClientAccount).filter(
        ClientAccount.license_id == license_obj.id
    ).first()

    if not account:
        raise HTTPException(status_code=404, detail="MT5 settings not found")

    return {
        "license_key": license_obj.license_key,
        "mt_login": account.mt_login,
        "mt_server": account.mt_server,
        "execute_trades": account.execute_trades,
        "lot_size": account.lot_size,
    }

@router.get("/client/history/{license_key}", response_model=list[TradeExecutionResponse])
def get_client_trade_history(
    license_key: str,
    db: Session = Depends(get_db),
):
    license_obj = db.query(License).filter(
        License.license_key == license_key
    ).first()

    if not license_obj:
        raise HTTPException(status_code=404, detail="Invalid license key")

    rows = (
        db.query(TradeExecution)
        .filter(TradeExecution.license_id == license_obj.id)
        .order_by(TradeExecution.id.desc())
        .all()
    )

    result = []
    for row in rows:
        result.append({
            "id": row.id,
            "license_id": row.license_id,
            "signal_id": row.signal_id,
            "symbol": row.symbol,
            "action": row.action,
            "success": row.success,
            "message": row.message,
            "order_id": row.order_id,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        })

    return result


@router.post("/client/execution/toggle")
def toggle_client_execution(
    data: ClientExecutionToggleRequest,
    db: Session = Depends(get_db),
):
    license_obj = db.query(License).filter(
        License.license_key == data.license_key
    ).first()

    if not license_obj:
        raise HTTPException(status_code=404, detail="Invalid license key")

    client_account = db.query(ClientAccount).filter(
        ClientAccount.license_id == license_obj.id
    ).first()

    if not client_account:
        raise HTTPException(status_code=404, detail="Client MT5 account not found")

    client_account.execute_trades = data.execute_trades
    db.commit()

    return {
        "success": True,
        "license_key": data.license_key,
        "execute_trades": client_account.execute_trades,
        "message": "Smart execution updated successfully",
    }
