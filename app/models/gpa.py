from sqlalchemy import Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class GPARecord(Base):
    __tablename__ = "gpa_records"
    __table_args__ = (UniqueConstraint("student_id", "academic_year", "semester", name="uq_gpa"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    academic_year: Mapped[str] = mapped_column(String(10), nullable=False)
    semester: Mapped[int] = mapped_column(Integer, nullable=False)
    gpa: Mapped[float] = mapped_column(Float, nullable=False)
    cgpa: Mapped[float] = mapped_column(Float, nullable=False)
    total_credit_units: Mapped[int] = mapped_column(Integer, nullable=False)

    student: Mapped["Student"] = relationship("Student", back_populates="gpa_records")
