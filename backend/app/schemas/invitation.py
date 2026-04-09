from pydantic import BaseModel, EmailStr


class InvitationCreate(BaseModel):
    email: EmailStr


class InvitationOut(BaseModel):
    id: int
    email: str
    token: str
    is_used: bool

    model_config = {"from_attributes": True}
