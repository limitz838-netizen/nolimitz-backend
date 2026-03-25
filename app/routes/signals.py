from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Signal, License
from app.schemas import SignalCreateRequest, SignalResponse, ClientSignalResponse

router = APIRouter()


@router.post("/admin/signals", response_model=SignalResponse)
def push_signal(data: SignalCreateRequest, db: Session = Depends(get_db)):
    new_signal = Signal(
        admin_id=1,
        ea_id=data.ea_id,
        symbol=data.symbol,
        action=data.action,
        entry_price=data.entry_price,
        stop_loss=data.stop_loss,
        take_profit=data.take_profit,
    )

    db.add(new_signal)
    db.commit()
    db.refresh(new_signal)

    return {
        "id": new_signal.id,
        "ea_id": new_signal.ea_id,
        "symbol": new_signal.symbol,
        "action": new_signal.action,
        "entry_price": new_signal.entry_price,
        "stop_loss": new_signal.stop_loss,
        "take_profit": new_signal.take_profit,
        "status": new_signal.status,
        "created_at": new_signal.created_at.isoformat() if new_signal.created_at else None,
    }


@router.get("/client/signals/{license_key}", response_model=list[ClientSignalResponse])
def get_signals(license_key: str, db: Session = Depends(get_db)):
    license_obj = db.query(License).filter(
        License.license_key == license_key
    ).first()

    if not license_obj:
        raise HTTPException(status_code=404, detail="Invalid license")

    signals = db.query(Signal).filter(
        Signal.ea_id == license_obj.ea_id
    ).order_by(Signal.id.asc()).all()

    result = []
    for s in signals:
        result.append({
            "id": s.id,
            "symbol": s.symbol,
            "action": s.action,
            "entry_price": s.entry_price,
            "stop_loss": s.stop_loss,
            "take_profit": s.take_profit,
            "status": s.status,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        })

    return result