from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    generate_otp,
    hash_otp,
    hash_password,
    verify_password,
    decode_token,
    generate_invite_token,
)
from app.models.invitation import Invitation
from app.models.otp import OTPToken
from app.models.student import Student
from app.models.lecturer import Lecturer
from app.models.user import User, UserRole
from app.models.pre_registered_student import PreRegisteredStudent
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    ResetPasswordRequest,
    StudentRegisterRequest,
    LecturerRegisterRequest,
)
from app.services.email import send_otp_email, send_invite_email


def register_student(data: StudentRegisterRequest, db: Session) -> User:
    # Verify matric number exists in pre-registered list
    pre_reg = db.query(PreRegisteredStudent).filter_by(matric_number=data.matric_number).first()
    if not pre_reg:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Matric number not found in the school's pre-registered student list",
        )

    if db.query(User).filter_by(email=data.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    if db.query(Student).filter_by(matric_number=data.matric_number).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Matric number already has an account")

    user = User(email=data.email, hashed_password=hash_password(data.password), role=UserRole.student)
    db.add(user)
    db.flush()

    student = Student(
        user_id=user.id,
        first_name=pre_reg.first_name,
        last_name=pre_reg.last_name,
        matric_number=data.matric_number,
        department_id=pre_reg.department_id,
    )
    db.add(student)
    db.commit()
    db.refresh(user)
    return user


def register_lecturer_via_invite(data: LecturerRegisterRequest, db: Session) -> User:
    invite = db.query(Invitation).filter_by(token=data.invite_token, email=data.email).first()
    if not invite or invite.is_used or invite.is_expired:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired invite token")

    if db.query(User).filter_by(email=data.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(email=data.email, hashed_password=hash_password(data.password), role=UserRole.lecturer)
    db.add(user)
    db.flush()

    lecturer = Lecturer(
        user_id=user.id,
        first_name=data.first_name,
        last_name=data.last_name,
        staff_id=data.staff_id,
    )
    db.add(lecturer)

    invite.is_used = True
    db.commit()
    db.refresh(user)
    return user


def login(data: LoginRequest, db: Session) -> dict:
    user = db.query(User).filter_by(email=data.email).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")

    return {
        "access_token": create_access_token(user.id, user.role),
        "refresh_token": create_refresh_token(user.id),
        "token_type": "bearer",
    }


def refresh_access_token(refresh_token: str, db: Session) -> dict:
    from jose import JWTError
    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return {
        "access_token": create_access_token(user.id, user.role),
        "refresh_token": create_refresh_token(user.id),
        "token_type": "bearer",
    }


async def forgot_password(data: ForgotPasswordRequest, db: Session) -> None:
    user = db.query(User).filter_by(email=data.email).first()
    # Always return success to prevent email enumeration
    if not user:
        return

    # Invalidate existing unused OTPs
    db.query(OTPToken).filter_by(user_id=user.id, is_used=False).delete()

    otp = generate_otp()
    token = OTPToken(
        user_id=user.id,
        hashed_otp=hash_otp(otp),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
    )
    db.add(token)
    db.commit()

    try:
        await send_otp_email(user.email, otp)
    except Exception:
        pass  # OTP is saved; email failure is non-fatal


def reset_password(data: ResetPasswordRequest, db: Session) -> None:
    user = db.query(User).filter_by(email=data.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request")

    token = (
        db.query(OTPToken)
        .filter_by(user_id=user.id, is_used=False)
        .order_by(OTPToken.created_at.desc())
        .first()
    )

    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active OTP found")

    if token.is_expired:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP has expired")

    if token.attempts >= settings.OTP_MAX_ATTEMPTS:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many failed attempts")

    if token.hashed_otp != hash_otp(data.otp):
        token.attempts += 1
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP")

    user.hashed_password = hash_password(data.new_password)
    token.is_used = True
    db.commit()


async def create_invitation(email: str, admin_user: User, db: Session) -> Invitation:
    # Check if email is already a registered user
    if db.query(User).filter_by(email=email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This email is already registered")

    # Prevent duplicate active invites
    existing = (
        db.query(Invitation)
        .filter_by(email=email, is_used=False)
        .first()
    )
    if existing and not existing.is_expired:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Active invitation already exists for this email")

    token = generate_invite_token()
    invite = Invitation(
        email=email,
        token=token,
        created_by=admin_user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=48),
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)

    invite_link = f"http://localhost:8000/api/v1/auth/register/lecturer?token={token}&email={email}"
    try:
        await send_invite_email(email, invite_link)
    except Exception:
        pass  # Invite is saved; email failure is non-fatal

    return invite
