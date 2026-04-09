import io

import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.lecturer import Lecturer
from app.models.result import Result, ResultStatus
from app.models.student import Student
from app.schemas.result import ResultCreate, ResultApprovalRequest
from app.services.gpa import recalculate_gpa, score_to_grade


def _get_lecturer(user_id: int, db: Session) -> Lecturer:
    lecturer = db.query(Lecturer).filter_by(user_id=user_id).first()
    if not lecturer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lecturer profile not found")
    return lecturer


def _assert_course_assigned(lecturer: Lecturer, course_id: int, db: Session) -> Course:
    course = db.get(Course, course_id)
    if not course or course.lecturer_id != lecturer.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Course not assigned to you")
    return course


def submit_result(data: ResultCreate, lecturer_user_id: int, db: Session) -> Result:
    lecturer = _get_lecturer(lecturer_user_id, db)
    _assert_course_assigned(lecturer, data.course_id, db)

    existing = (
        db.query(Result)
        .filter_by(student_id=data.student_id, course_id=data.course_id, academic_year=data.academic_year)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Result already submitted for this course")

    grade, grade_point = score_to_grade(data.score)
    result = Result(
        student_id=data.student_id,
        course_id=data.course_id,
        lecturer_id=lecturer.id,
        score=data.score,
        grade=grade,
        grade_point=grade_point,
        academic_year=data.academic_year,
        semester=data.semester,
        status=ResultStatus.pending,
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


def bulk_upload_results(csv_bytes: bytes, lecturer_user_id: int, db: Session) -> dict:
    lecturer = _get_lecturer(lecturer_user_id, db)

    try:
        df = pd.read_csv(io.BytesIO(csv_bytes))
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid CSV file")

    required_cols = {"matric_number", "course_code", "score", "academic_year", "semester"}
    if not required_cols.issubset(df.columns):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSV must contain columns: {required_cols}",
        )

    success, errors = 0, []

    for idx, row in df.iterrows():
        try:
            student = db.query(Student).filter_by(matric_number=str(row["matric_number"])).first()
            course = db.query(Course).filter_by(code=str(row["course_code"])).first()

            if not student:
                errors.append({"row": idx + 2, "error": f"Student {row['matric_number']} not found"})
                continue
            if not course or course.lecturer_id != lecturer.id:
                errors.append({"row": idx + 2, "error": f"Course {row['course_code']} not assigned to you"})
                continue

            score = float(row["score"])
            if not (0 <= score <= 100):
                errors.append({"row": idx + 2, "error": "Score out of range"})
                continue

            existing = db.query(Result).filter_by(
                student_id=student.id, course_id=course.id, academic_year=str(row["academic_year"])
            ).first()
            if existing:
                errors.append({"row": idx + 2, "error": "Duplicate result"})
                continue

            grade, grade_point = score_to_grade(score)
            db.add(Result(
                student_id=student.id,
                course_id=course.id,
                lecturer_id=lecturer.id,
                score=score,
                grade=grade,
                grade_point=grade_point,
                academic_year=str(row["academic_year"]),
                semester=int(row["semester"]),
                status=ResultStatus.pending,
            ))
            success += 1
        except Exception as e:
            errors.append({"row": idx + 2, "error": str(e)})

    db.commit()
    return {"uploaded": success, "errors": errors}


def approve_or_reject_result(result_id: int, data: ResultApprovalRequest, db: Session) -> Result:
    result = db.get(Result, result_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Result not found")
    if result.status != ResultStatus.pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending results can be reviewed")

    if data.status == ResultStatus.rejected and not data.rejection_reason:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rejection reason required")

    result.status = data.status
    result.rejection_reason = data.rejection_reason
    db.commit()

    if data.status == ResultStatus.approved:
        recalculate_gpa(result.student_id, result.academic_year, result.semester, db)

    db.refresh(result)
    return result
