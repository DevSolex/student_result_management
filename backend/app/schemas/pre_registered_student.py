from pydantic import BaseModel


class PreRegisteredStudentCreate(BaseModel):
    matric_number: str
    first_name: str
    last_name: str
    department_id: int | None = None


class PreRegisteredStudentOut(BaseModel):
    id: int
    matric_number: str
    first_name: str
    last_name: str
    department_id: int | None = None

    model_config = {"from_attributes": True}
