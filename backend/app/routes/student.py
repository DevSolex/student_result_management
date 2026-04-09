from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user, require_admin, require_student
from app.models.gpa import GPARecord
from app.models.result import Result, ResultStatus
from app.models.student import Student
from app.models.user import User
from app.schemas.student import StudentOut, StudentUpdate, AdminStudentCreate
from app.schemas.user import ChangePasswordRequest
from app.core.security import hash_password, verify_password
from app.services.cloudinary import upload_avatar

router = APIRouter(prefix="/students", tags=["Students"])


def _get_student_or_404(student_id: int, db: Session) -> Student:
    s = db.get(Student, student_id)
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return s


# ── Student: own dashboard ──────────────────────────────────────────────────

@router.get("/me", response_model=StudentOut)
def my_profile(current_user: User = Depends(require_student), db: Session = Depends(get_db)):
    return current_user.student


@router.patch("/me", response_model=StudentOut)
def update_my_profile(
    data: StudentUpdate,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    student = current_user.student
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(student, field, value)
    db.commit()
    db.refresh(student)
    return student


@router.post("/me/avatar")
async def upload_my_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    url = await upload_avatar(file, current_user.id)
    current_user.avatar_url = url
    db.commit()
    return {"avatar_url": url}


@router.post("/me/change-password")
def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    current_user.hashed_password = hash_password(data.new_password)
    db.commit()
    return {"message": "Password updated"}


@router.get("/me/results")
def my_results(
    academic_year: str | None = None,
    semester: int | None = None,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    query = db.query(Result).filter(
        Result.student_id == current_user.student.id,
        Result.status == ResultStatus.approved,
    )
    if academic_year:
        query = query.filter(Result.academic_year == academic_year)
    if semester:
        query = query.filter(Result.semester == semester)
    return query.all()


@router.get("/me/gpa")
def my_gpa(current_user: User = Depends(require_student), db: Session = Depends(get_db)):
    records = db.query(GPARecord).filter_by(student_id=current_user.student.id).all()
    latest_cgpa = records[-1].cgpa if records else 0.0
    return {"cgpa": latest_cgpa, "semesters": records}


@router.get("/me/transcript")
def my_transcript(current_user: User = Depends(require_student), db: Session = Depends(get_db)):
    student = current_user.student
    results = db.query(Result).filter(
        Result.student_id == student.id,
        Result.status == ResultStatus.approved,
    ).all()
    gpa_records = db.query(GPARecord).filter_by(student_id=student.id).all()
    return {
        "student": {"name": f"{student.first_name} {student.last_name}", "matric": student.matric_number},
        "results": results,
        "gpa_records": gpa_records,
    }


# ── Admin: student management ───────────────────────────────────────────────

@router.get("/", dependencies=[Depends(require_admin)])
def list_students(db: Session = Depends(get_db)):
    return db.query(Student).all()


@router.delete("/{student_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_student(student_id: int, db: Session = Depends(get_db)):
    from app.models.result import Result
    from app.models.gpa import GPARecord
    student = _get_student_or_404(student_id, db)
    user = student.user
    db.query(Result).filter_by(student_id=student.id).delete()
    db.query(GPARecord).filter_by(student_id=student.id).delete()
    db.delete(student)
    db.flush()
    db.delete(user)
    db.commit()
