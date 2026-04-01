from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.gpa import GPARecord
from app.models.result import Result, ResultStatus


def score_to_grade(score: float) -> tuple[str, float]:
    """Returns (letter_grade, grade_point) for a given score."""
    if score >= 70:
        return "A", 5.0
    elif score >= 60:
        return "B", 4.0
    elif score >= 50:
        return "C", 3.0
    elif score >= 45:
        return "D", 2.0
    elif score >= 40:
        return "E", 1.0
    else:
        return "F", 0.0


def recalculate_gpa(student_id: int, academic_year: str, semester: int, db: Session) -> GPARecord:
    """Recalculate and upsert GPA for a student's semester."""
    approved_results = (
        db.query(Result)
        .filter(
            Result.student_id == student_id,
            Result.academic_year == academic_year,
            Result.semester == semester,
            Result.status == ResultStatus.approved,
        )
        .all()
    )

    total_points = 0.0
    total_units = 0

    for result in approved_results:
        course = db.get(Course, result.course_id)
        if course:
            total_points += result.grade_point * course.credit_units
            total_units += course.credit_units

    semester_gpa = round(total_points / total_units, 2) if total_units else 0.0

    # CGPA: all approved results across all semesters
    all_results = (
        db.query(Result)
        .filter(Result.student_id == student_id, Result.status == ResultStatus.approved)
        .all()
    )
    all_points, all_units = 0.0, 0
    for r in all_results:
        course = db.get(Course, r.course_id)
        if course:
            all_points += r.grade_point * course.credit_units
            all_units += course.credit_units

    cgpa = round(all_points / all_units, 2) if all_units else 0.0

    record = (
        db.query(GPARecord)
        .filter_by(student_id=student_id, academic_year=academic_year, semester=semester)
        .first()
    )
    if record:
        record.gpa = semester_gpa
        record.cgpa = cgpa
        record.total_credit_units = total_units
    else:
        record = GPARecord(
            student_id=student_id,
            academic_year=academic_year,
            semester=semester,
            gpa=semester_gpa,
            cgpa=cgpa,
            total_credit_units=total_units,
        )
        db.add(record)

    db.commit()
    db.refresh(record)
    return record
