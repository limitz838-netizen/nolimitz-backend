from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ExecutionJob
from app.schemas import ExecutionJobResponse, ExecutionJobUpdateRequest

router = APIRouter(tags=["Execution Jobs"])


@router.get("/worker/jobs/pending", response_model=list[ExecutionJobResponse])
def get_pending_jobs(db: Session = Depends(get_db)):
    jobs = (
        db.query(ExecutionJob)
        .filter(ExecutionJob.status == "pending")
        .order_by(ExecutionJob.created_at.asc())
        .all()
    )
    return jobs


@router.post("/worker/jobs/{job_id}/claim", response_model=ExecutionJobResponse)
def claim_job(job_id: int, worker_name: str, db: Session = Depends(get_db)):
    job = db.query(ExecutionJob).filter(ExecutionJob.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != "pending":
        raise HTTPException(status_code=400, detail="Job is not pending")

    job.status = "processing"
    job.worker_name = worker_name
    db.commit()
    db.refresh(job)
    return job


@router.post("/worker/jobs/{job_id}/complete", response_model=ExecutionJobResponse)
def complete_job(job_id: int, data: ExecutionJobUpdateRequest, db: Session = Depends(get_db)):
    job = db.query(ExecutionJob).filter(ExecutionJob.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.status = data.status
    job.worker_name = data.worker_name
    job.error_message = data.error_message
    job.processed_at = datetime.utcnow()

    db.commit()
    db.refresh(job)
    return job


@router.get("/admin/execution-jobs", response_model=list[ExecutionJobResponse])
def list_execution_jobs(db: Session = Depends(get_db)):
    jobs = db.query(ExecutionJob).order_by(ExecutionJob.created_at.desc()).all()
    return jobs