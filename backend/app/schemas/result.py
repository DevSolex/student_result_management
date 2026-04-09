from pydantic import BaseModel, field_validator
from app.models.result import ResultStatus


class ResultCreate(BaseModel):
    student_id: int
    course_id: int
    score: float
    academic_year: str
    semester: int

    @field_validator("score")
    @classmethod
    def valid_score(cls, v: float) -> float:
        if not (0 <= v <= 100):
            raise ValueError("Score must be between 0 and 100")
        return v

    @field_validator("semester")
    @classmethod
    def valid_semester(cls, v: int) -> int:
        if v not in (1, 2):
            raise ValueError("Semester must be 1 or 2")
        return v


class ResultOut(BaseModel):
    id: int
    student_id: int
    course_id: int
    score: float
    grade: str
    grade_point: float
    academic_year: str
    semester: int
    status: ResultStatus

    model_config = {"from_attributes": True}


class ResultApprovalRequest(BaseModel):
    status: ResultStatus
    rejection_reason: str | None = None
