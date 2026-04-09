from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"), nullable=True)
    lecturer_id: Mapped[int | None] = mapped_column(ForeignKey("lecturers.id"), nullable=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    credit_units: Mapped[int] = mapped_column(Integer, nullable=False)
    semester: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 or 2
    level: Mapped[int] = mapped_column(Integer, nullable=False)     # 100–500

    department: Mapped["Department"] = relationship("Department", back_populates="courses")
    lecturer: Mapped["Lecturer"] = relationship("Lecturer", back_populates="courses")
    results: Mapped[list["Result"]] = relationship("Result", back_populates="course")
