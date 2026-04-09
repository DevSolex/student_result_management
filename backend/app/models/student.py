from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"), nullable=True)
    matric_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=100)  # 100, 200, 300, 400, 500

    user: Mapped["User"] = relationship("User", back_populates="student")
    department: Mapped["Department"] = relationship("Department", back_populates="students")
    results: Mapped[list["Result"]] = relationship("Result", back_populates="student")
    gpa_records: Mapped[list["GPARecord"]] = relationship("GPARecord", back_populates="student")
