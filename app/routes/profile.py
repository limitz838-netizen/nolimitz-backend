from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Admin, AdminProfile
from app.schemas import ProfileUpdateRequest, ProfileResponse
from app.auth import get_current_admin

router = APIRouter(tags=["Profile"])


@router.get("/admin/profile", response_model=ProfileResponse)
def get_admin_profile(current_admin: Admin = Depends(get_current_admin)):
    profile = current_admin.profile

    return {
        "id": current_admin.id,
        "full_name": current_admin.full_name,
        "email": current_admin.email,
        "admin_code": current_admin.admin_code,
        "is_approved": current_admin.is_approved,
        "display_name": profile.display_name if profile else None,
        "phone": profile.phone if profile else None,
        "logo_url": profile.logo_url if profile else None,
    }


@router.post("/admin/profile", response_model=ProfileResponse)
def update_admin_profile(
    payload: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    profile = db.query(AdminProfile).filter(AdminProfile.admin_id == current_admin.id).first()

    if not profile:
        profile = AdminProfile(
            admin_id=current_admin.id,
            display_name=payload.display_name,
            phone=payload.phone,
            logo_url=None,
        )
        db.add(profile)
    else:
        if payload.display_name is not None:
            profile.display_name = payload.display_name
        if payload.phone is not None:
            profile.phone = payload.phone

    db.commit()
    db.refresh(profile)

    return {
        "id": current_admin.id,
        "full_name": current_admin.full_name,
        "email": current_admin.email,
        "admin_code": current_admin.admin_code,
        "is_approved": current_admin.is_approved,
        "display_name": profile.display_name,
        "phone": profile.phone,
        "logo_url": profile.logo_url,
    }