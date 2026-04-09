from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Lecturer(Base):
    __tablename__ = "lecturers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"), nullable=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    staff_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="lecturer")
    department: Mapped["Department"] = relationship("Department", back_populates="lecturers")
    courses: Mapped[list["Course"]] = relationship("Course", back_populates="lecturer")
