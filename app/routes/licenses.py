import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_admin
from app.database import get_db
from app.models import License, ExpertAdvisor, Admin
from app.schemas import (
    LicenseCreateRequest,
    LicenseValidateRequest,
    LicenseValidateResponse,
    LicenseResponse,
)

router = APIRouter(prefix="/admin", tags=["Licenses"])


@router.post("/licenses", response_model=LicenseResponse)
def create_license(
    data: LicenseCreateRequest,
    db: Session = Depends(get_db),
):
    ea = db.query(ExpertAdvisor).filter(
        ExpertAdvisor.id == data.ea_id,
    ).first()

    if not ea:
        raise HTTPException(status_code=404, detail="EA not found")

    license_key = f"NL-{uuid.uuid4().hex[:10].upper()}"
    expires_at = datetime.utcnow() + timedelta(days=data.duration_days)

    new_license = License(
        admin_id=ea.admin_id,
        ea_id=data.ea_id,
        client_name=data.client_name,
        client_email=data.client_email,
        license_key=license_key,
        duration_days=data.duration_days,
        expires_at=expires_at,
        status="active",
    )

    db.add(new_license)
    db.commit()
    db.refresh(new_license)

    return {
        "id": new_license.id,
        "client_name": new_license.client_name,
        "client_email": new_license.client_email,
        "license_key": new_license.license_key,
        "status": new_license.status,
        "duration_days": new_license.duration_days,
        "ea_id": new_license.ea_id,
    }


@router.get("/licenses", response_model=list[LicenseResponse])
def list_licenses(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    licenses = db.query(License).filter(
        License.admin_id == current_admin.id
    ).all()

    return [
        {
            "id": lic.id,
            "client_name": lic.client_name,
            "client_email": lic.client_email,
            "license_key": lic.license_key,
            "status": lic.status,
            "duration_days": lic.duration_days,
            "ea_id": lic.ea_id,
        }
        for lic in licenses
    ]


@router.post("/licenses/validate", response_model=LicenseValidateResponse)
def validate_license(
    data: LicenseValidateRequest,
    db: Session = Depends(get_db),
):
    license_obj = db.query(License).filter(
        License.license_key == data.license_key
    ).first()

    if not license_obj:
        return {
            "valid": False,
            "message": "Invalid license key",
            "license_key": None,
            "status": None,
            "ea_id": None,
        }

    if license_obj.status != "active":
        return {
            "valid": False,
            "message": "License is not active",
            "license_key": license_obj.license_key,
            "status": license_obj.status,
            "ea_id": license_obj.ea_id,
        }

    if license_obj.expires_at and license_obj.expires_at < datetime.utcnow():
        return {
            "valid": False,
            "message": "License expired",
            "license_key": license_obj.license_key,
            "status": license_obj.status,
            "ea_id": license_obj.ea_id,
        }

    return {
        "valid": True,
        "message": "License valid",
        "license_key": license_obj.license_key,
        "status": license_obj.status,
        "ea_id": license_obj.ea_id,
    }