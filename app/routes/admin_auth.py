import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Admin, AdminProfile
from app.schemas import (
    AdminSignup,
    AdminLogin,
    TokenResponse,
    AdminMeResponse,
    MessageResponse,
    ApproveAdminResponse,
)
from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_admin,
)

router = APIRouter(tags=["Admin Auth"])


def generate_admin_code() -> str:
    return "ADM-" + secrets.token_hex(4).upper()


@router.post("/admin/signup", response_model=MessageResponse)
def admin_signup(payload: AdminSignup, db: Session = Depends(get_db)):
    existing_admin = db.query(Admin).filter(Admin.email == payload.email).first()
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    admin_code = generate_admin_code()

    while db.query(Admin).filter(Admin.admin_code == admin_code).first():
        admin_code = generate_admin_code()

    new_admin = Admin(
        full_name=payload.full_name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        admin_code=admin_code,
        is_approved=False,
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    profile = AdminProfile(
        admin_id=new_admin.id,
        display_name=payload.full_name,
        phone=None,
        logo_url=None,
    )
    db.add(profile)
    db.commit()

    return {
        "message": "Signup successful. Your admin account is pending approval."
    }


@router.post("/admin/login", response_model=TokenResponse)
def admin_login(payload: AdminLogin, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.email == payload.email).first()

    if not admin or not verify_password(payload.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not admin.is_approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your admin account is pending approval"
        )

    token = create_access_token({"sub": str(admin.id)})

    return {
        "access_token": token,
        "token_type": "bearer",
        "admin": {
            "id": admin.id,
            "full_name": admin.full_name,
            "email": admin.email,
            "admin_code": admin.admin_code,
            "is_approved": admin.is_approved,
        },
    }


@router.get("/admin/me", response_model=AdminMeResponse)
def admin_me(current_admin: Admin = Depends(get_current_admin)):
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


@router.get("/admin/pending")
def get_pending_admins(db: Session = Depends(get_db)):
    pending_admins = db.query(Admin).filter(Admin.is_approved == False).all()

    return [
        {
            "id": admin.id,
            "full_name": admin.full_name,
            "email": admin.email,
            "admin_code": admin.admin_code,
            "is_approved": admin.is_approved,
            "created_at": admin.created_at,
        }
        for admin in pending_admins
    ]


@router.post("/admin/approve/{admin_id}", response_model=ApproveAdminResponse)
def approve_admin(admin_id: int, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.id == admin_id).first()

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )

    admin.is_approved = True
    db.commit()
    db.refresh(admin)

    return {
        "message": "Admin approved successfully",
        "admin_id": admin.id,
        "is_approved": admin.is_approved,
    }