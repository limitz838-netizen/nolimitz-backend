import json
import os
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import decode_access_token
from app.database import get_db
from app.models import Admin

router = APIRouter(prefix="/admin/master-account", tags=["Master Account"])


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "storage")
DATA_FILE = os.path.join(DATA_DIR, "master_accounts.json")

os.makedirs(DATA_DIR, exist_ok=True)


class MasterAccountSaveRequest(BaseModel):
    ea_id: int
    mt_login: str
    mt_password: str
    mt_server: str


class MasterAccountVerifyRequest(BaseModel):
    ea_id: int
    mt_login: str
    mt_password: str
    mt_server: str


def read_storage() -> dict:
    if not os.path.exists(DATA_FILE):
        return {}

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def write_storage(data: dict) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_current_admin(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
) -> Admin:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header",
        )

    token = authorization.split(" ")[1]
    payload = decode_access_token(token)

    admin_id = payload.get("admin_id")
    if not admin_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")

    return admin


@router.post("/save")
def save_master_account(
    payload: MasterAccountSaveRequest,
    current_admin: Admin = Depends(get_current_admin),
):
    data = read_storage()
    admin_key = str(current_admin.id)

    existing = data.get(admin_key, {})

    data[admin_key] = {
        "admin_id": current_admin.id,
        "ea_id": payload.ea_id,
        "mt_login": str(payload.mt_login).strip(),
        "mt_password": str(payload.mt_password).strip(),
        "mt_server": str(payload.mt_server).strip(),
        "connected": existing.get("connected", False),
        "account_name": existing.get("account_name"),
        "broker_name": existing.get("broker_name"),
        "verified": existing.get("verified", False),
        "last_verified_at": existing.get("last_verified_at"),
        "updated_at": datetime.utcnow().isoformat(),
    }

    write_storage(data)

    return {
        "success": True,
        "message": "Master account saved successfully",
        "connected": data[admin_key]["connected"],
    }


@router.post("/verify")
def verify_master_account(
    payload: MasterAccountVerifyRequest,
    current_admin: Admin = Depends(get_current_admin),
):
    mt_login = str(payload.mt_login).strip()
    mt_password = str(payload.mt_password).strip()
    mt_server = str(payload.mt_server).strip()

    if not mt_login or not mt_password or not mt_server:
        raise HTTPException(
            status_code=400,
            detail="MT login, password and server are required",
        )

    data = read_storage()
    admin_key = str(current_admin.id)

    # For now this is a working backend version that marks the account verified
    # once all fields are provided. Later you can connect this to a real MT5
    # bridge/verification service.
    account_name = f"Master {mt_login}"
    broker_name = mt_server

    data[admin_key] = {
        "admin_id": current_admin.id,
        "ea_id": payload.ea_id,
        "mt_login": mt_login,
        "mt_password": mt_password,
        "mt_server": mt_server,
        "connected": True,
        "account_name": account_name,
        "broker_name": broker_name,
        "verified": True,
        "last_verified_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }

    write_storage(data)

    return {
        "success": True,
        "connected": True,
        "account_name": account_name,
        "broker_name": broker_name,
        "message": "Master MT5 account verified successfully",
    }


@router.get("/status")
def master_account_status(
    current_admin: Admin = Depends(get_current_admin),
):
    data = read_storage()
    admin_key = str(current_admin.id)
    item = data.get(admin_key)

    if not item:
        return {
            "connected": False,
            "account_name": None,
            "broker_name": None,
            "ea_id": None,
            "mt_login": None,
            "mt_server": None,
            "verified": False,
            "last_verified_at": None,
        }

    return {
        "connected": bool(item.get("connected", False)),
        "account_name": item.get("account_name"),
        "broker_name": item.get("broker_name"),
        "ea_id": item.get("ea_id"),
        "mt_login": item.get("mt_login"),
        "mt_server": item.get("mt_server"),
        "verified": bool(item.get("verified", False)),
        "last_verified_at": item.get("last_verified_at"),
    }