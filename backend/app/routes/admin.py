from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import require_admin
from app.models.department import Department
from app.models.pre_registered_student import PreRegisteredStudent
from app.models.result import Result, ResultStatus
from app.models.student import Student
from app.schemas.pre_registered_student import PreRegisteredStudentCreate, PreRegisteredStudentOut
from app.schemas.result import ResultApprovalRequest, ResultOut
from app.services.result import approve_or_reject_result

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/dashboard", dependencies=[Depends(require_admin)])
def admin_dashboard(db: Session = Depends(get_db)):
    total_students = db.query(Student).count()
    pending_results = db.query(Result).filter_by(status=ResultStatus.pending).count()
    departments = db.query(Department).all()
    return {
        "total_students": total_students,
        "pending_results": pending_results,
        "departments": [{"id": d.id, "name": d.name, "code": d.code} for d in departments],
    }


@router.get("/results/pending", dependencies=[Depends(require_admin)])
def pending_results(db: Session = Depends(get_db)):
    return db.query(Result).filter_by(status=ResultStatus.pending).all()


@router.patch("/results/{result_id}/review", response_model=ResultOut, dependencies=[Depends(require_admin)])
def review_result(result_id: int, data: ResultApprovalRequest, db: Session = Depends(get_db)):
    return approve_or_reject_result(result_id, data, db)


# ── Pre-registered students ──────────────────────────────────────────────────

@router.get("/pre-registered", response_model=list[PreRegisteredStudentOut], dependencies=[Depends(require_admin)])
def list_pre_registered(db: Session = Depends(get_db)):
    return db.query(PreRegisteredStudent).all()


@router.post("/pre-registered", response_model=PreRegisteredStudentOut, status_code=201, dependencies=[Depends(require_admin)])
def add_pre_registered(data: PreRegisteredStudentCreate, db: Session = Depends(get_db)):
    if db.query(PreRegisteredStudent).filter_by(matric_number=data.matric_number).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Matric number already pre-registered")
    entry = PreRegisteredStudent(**data.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/pre-registered/{entry_id}", status_code=204, dependencies=[Depends(require_admin)])
def remove_pre_registered(entry_id: int, db: Session = Depends(get_db)):
    entry = db.get(PreRegisteredStudent, entry_id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    db.delete(entry)
    db.commit()
