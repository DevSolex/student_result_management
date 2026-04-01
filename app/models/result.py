import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ResultStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class Result(Base):
    __tablename__ = "results"
    __table_args__ = (UniqueConstraint("student_id", "course_id", "academic_year", name="uq_result"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    lecturer_id: Mapped[int] = mapped_column(ForeignKey("lecturers.id"), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    grade: Mapped[str] = mapped_column(String(2), nullable=False)
    grade_point: Mapped[float] = mapped_column(Float, nullable=False)
    academic_year: Mapped[str] = mapped_column(String(10), nullable=False)  # e.g. "2024/2025"
    semester: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[ResultStatus] = mapped_column(Enum(ResultStatus), default=ResultStatus.pending)
    rejection_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    student: Mapped["Student"] = relationship("Student", back_populates="results")
    course: Mapped["Course"] = relationship("Course", back_populates="results")
