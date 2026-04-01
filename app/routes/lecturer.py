from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import require_admin, require_lecturer
from app.models.lecturer import Lecturer
from app.models.result import Result, ResultStatus
from app.models.student import Student
from app.models.user import User
from app.schemas.result import ResultCreate, ResultOut
from app.services.result import submit_result, bulk_upload_results

router = APIRouter(prefix="/lecturers", tags=["Lecturers"])


@router.get("/me/dashboard")
def lecturer_dashboard(current_user: User = Depends(require_lecturer), db: Session = Depends(get_db)):
    lecturer = current_user.lecturer
    recent = (
        db.query(Result)
        .filter_by(lecturer_id=lecturer.id)
        .order_by(Result.submitted_at.desc())
        .limit(10)
        .all()
    )
    return {"lecturer": lecturer, "recent_submissions": recent}


@router.get("/me/students")
def my_students(current_user: User = Depends(require_lecturer), db: Session = Depends(get_db)):
    """Returns students enrolled in courses assigned to this lecturer."""
    lecturer = current_user.lecturer
    course_ids = [c.id for c in lecturer.courses]
    student_ids = (
        db.query(Result.student_id)
        .filter(Result.course_id.in_(course_ids))
        .distinct()
        .all()
    )
    ids = [s[0] for s in student_ids]
    return db.query(Student).filter(Student.id.in_(ids)).all()


@router.post("/me/results", response_model=ResultOut, status_code=201)
def submit_single_result(
    data: ResultCreate,
    current_user: User = Depends(require_lecturer),
    db: Session = Depends(get_db),
):
    return submit_result(data, current_user.id, db)


@router.post("/me/results/bulk", status_code=201)
async def bulk_result_upload(
    file: UploadFile = File(...),
    current_user: User = Depends(require_lecturer),
    db: Session = Depends(get_db),
):
    if file.content_type not in ("text/csv", "application/vnd.ms-excel"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only CSV files are accepted")
    contents = await file.read()
    return bulk_upload_results(contents, current_user.id, db)


# ── Admin: lecturer management ──────────────────────────────────────────────

@router.get("/", dependencies=[Depends(require_admin)])
def list_lecturers(db: Session = Depends(get_db)):
    return db.query(Lecturer).all()


@router.patch("/{lecturer_id}/activate", dependencies=[Depends(require_admin)])
def toggle_lecturer_status(lecturer_id: int, activate: bool, db: Session = Depends(get_db)):
    lecturer = db.get(Lecturer, lecturer_id)
    if not lecturer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lecturer not found")
    lecturer.user.is_active = activate
    db.commit()
    return {"message": f"Lecturer {'activated' if activate else 'deactivated'}"}
