from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from app.database import get_db
from app.models import Signal, License, ClientAccount, ExecutionJob
from app.schemas import SignalCreateRequest, ClientSignalResponse

router = APIRouter()


@router.post("/admin/signals")
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

    licenses = db.query(License).filter(
        License.ea_id == new_signal.ea_id,
        License.status == "active"
    ).all()

    job_results = []

    for license_obj in licenses:
        client_account = db.query(ClientAccount).filter(
            ClientAccount.license_id == license_obj.id
        ).first()

        if not client_account:
            result = {
                "license_key": license_obj.license_key,
                "success": False,
                "error": "No MT5 account",
            }
            job_results.append(result)
            print(f"{license_obj.license_key} -> {result}")
            continue

        if not client_account.is_connected:
            result = {
                "license_key": license_obj.license_key,
                "success": False,
                "error": "MT5 not connected",
            }
            job_results.append(result)
            print(f"{license_obj.license_key} -> {result}")
            continue

        if not client_account.execute_trades:
            result = {
                "license_key": license_obj.license_key,
                "success": False,
                "error": "Auto execution OFF",
            }
            job_results.append(result)
            print(f"{license_obj.license_key} -> {result}")
            continue

        lot = client_account.lot_size if client_account.lot_size else 0.01

        recent_duplicate = db.query(Signal).filter(
            Signal.ea_id == new_signal.ea_id,
            Signal.symbol == new_signal.symbol,
            Signal.action == new_signal.action,
            Signal.stop_loss == new_signal.stop_loss,
            Signal.take_profit == new_signal.take_profit,
            Signal.id != new_signal.id,
            Signal.created_at >= datetime.now(timezone.utc) - timedelta(seconds=20)
        ).first()

        if recent_duplicate:
            result = {
                "license_key": license_obj.license_key,
                "success": False,
                "error": "Duplicate signal blocked",
            }
            job_results.append(result)
            print(f"{license_obj.license_key} -> {result}")
            continue

        new_job = ExecutionJob(
            license_id=license_obj.id,
            signal_id=new_signal.id,
            symbol=new_signal.symbol,
            action=new_signal.action,
            volume=lot,
            stop_loss=new_signal.stop_loss,
            take_profit=new_signal.take_profit,

            # 🔥 ADD THIS
            mt_login=client_account.mt_login,
            mt_password=client_account.mt_password,
            mt_server=client_account.mt_server,

            status="pending",
        )
        db.add(new_job)
        db.commit()
        db.refresh(new_job)

        result = {
            "license_key": license_obj.license_key,
            "success": True,
            "job_id": new_job.id,
            "job_status": new_job.status,
        }
        job_results.append(result)
        print(f"{license_obj.license_key} -> {result}")

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
        "job_results": job_results,
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