from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)

    students: Mapped[list["Student"]] = relationship("Student", back_populates="department")
    lecturers: Mapped[list["Lecturer"]] = relationship("Lecturer", back_populates="department")
    courses: Mapped[list["Course"]] = relationship("Course", back_populates="department")
