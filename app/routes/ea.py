import secrets
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ExpertAdvisor, Admin
from app.schemas import EACreateRequest, EAResponse
from app.auth import get_current_admin
from app.models import EASymbol

router = APIRouter(tags=["Expert Advisors"])


def generate_ea_code():
    return "EA-" + secrets.token_hex(4).upper()


@router.post("/admin/eas", response_model=EAResponse)
def create_ea(
    payload: EACreateRequest,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    ea = ExpertAdvisor(
        admin_id=current_admin.id,
        name=payload.name,
        description=payload.description,
        ea_code=generate_ea_code(),
        mode=payload.mode,
        is_active=True
    )

    db.add(ea)
    db.commit()
    db.refresh(ea)

    return ea


@router.get("/admin/eas", response_model=list[EAResponse])
def list_eas(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    eas = db.query(ExpertAdvisor).filter(
        ExpertAdvisor.admin_id == current_admin.id
    ).all()

    return eas


@router.post("/admin/eas/{ea_id}/symbols")
def save_ea_symbols(
    ea_id: int,
    symbols: list[str],
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    ea = db.query(ExpertAdvisor).filter(
        ExpertAdvisor.id == ea_id,
        ExpertAdvisor.admin_id == current_admin.id
    ).first()

    if not ea:
        return {"message": "EA not found"}

    # 🧹 delete old symbols first
    db.query(EASymbol).filter(EASymbol.ea_id == ea_id).delete()

    # ➕ add new ones
    for sym in symbols:
        db.add(EASymbol(ea_id=ea_id, symbol=sym))

    db.commit()

    return {
        "message": "Symbols saved successfully",
        "symbols": symbols
    }