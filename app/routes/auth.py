from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.database import get_db
from app.dependencies.auth import get_current_user, require_admin
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    LecturerRegisterRequest,
    RefreshRequest,
    ResetPasswordRequest,
    StudentRegisterRequest,
    TokenResponse,
)
from app.schemas.invitation import InvitationCreate, InvitationOut
from app.schemas.user import UserOut
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/register/student", response_model=UserOut, status_code=201)
def register_student(data: StudentRegisterRequest, db: Session = Depends(get_db)):
    return auth_service.register_student(data, db)


@router.post("/register/lecturer", response_model=UserOut, status_code=201)
def register_lecturer(data: LecturerRegisterRequest, db: Session = Depends(get_db)):
    return auth_service.register_lecturer_via_invite(data, db)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, data: LoginRequest, db: Session = Depends(get_db)):
    return auth_service.login(data, db)


@router.post("/refresh", response_model=TokenResponse)
def refresh(data: RefreshRequest, db: Session = Depends(get_db)):
    return auth_service.refresh_access_token(data.refresh_token, db)


@router.post("/forgot-password", status_code=202)
@limiter.limit("5/minute")
async def forgot_password(request: Request, data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    await auth_service.forgot_password(data, db)
    return {"message": "If that email exists, an OTP has been sent"}


@router.post("/reset-password", status_code=200)
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    auth_service.reset_password(data, db)
    return {"message": "Password reset successful"}


@router.post("/invite", response_model=InvitationOut, status_code=201)
async def invite_lecturer(
    data: InvitationCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return await auth_service.create_invitation(data.email, admin, db)
