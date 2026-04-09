from pydantic import BaseModel, EmailStr


class StudentOut(BaseModel):
    id: int
    matric_number: str
    first_name: str
    last_name: str
    level: int
    department_id: int | None = None

    model_config = {"from_attributes": True}


class StudentUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    level: int | None = None
    department_id: int | None = None


class AdminStudentCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    matric_number: str
    level: int = 100
    department_id: int | None = None
