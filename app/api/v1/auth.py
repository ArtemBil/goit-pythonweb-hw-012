from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.params import Depends
from sqlalchemy.orm import Session

from ...conf.config import get_db
from ...schemas.users import UserRegisterSchema, UserResponseSchema, TokenModel, TokenRefreshRequest, PasswordResetRequest, PasswordResetConfirm
from ...repositories.auth import auth_repository
from ...services.auth import auth_service
from ...services.email import send_email, send_password_reset_email
from ...services.cache import cache_service

"""Authentication API router.

Endpoints: signup, login, refresh-token, confirm email, password reset.
"""

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/signup",
    response_model=UserResponseSchema
)
async def signup(
        body: UserRegisterSchema,
        background_tasks: BackgroundTasks,
        request: Request,
        db: Session = Depends(get_db)
):
    """Register a new user and send a confirmation email."""
    user = await auth_repository.get_user_by_email(body.email, db)
    if user is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with this email already exists")

    body.password = auth_service.hash_password(body.password)

    user = await auth_repository.create_user(body, db)
    background_tasks.add_task(
        send_email,
        user.email,
        user.username,
        request.base_url
    )
    return user


@router.post("/login", response_model=TokenModel)
async def signup(
        body: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db)
):
    """Log in with email and password and receive access/refresh tokens."""
    user = await auth_repository.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")

    if not user.confirmed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User email not confirmed")

    access_token = await auth_service.create_access_token(payload={"sub": user.email})
    refresh_token = await auth_service.create_refresh_token(payload={"sub": user.email})
    user.refresh_token = refresh_token
    db.commit()

    # Cache current user by access token
    await cache_service.set_user_for_token(access_token, user)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post('/refresh-token', response_model=TokenModel)
async def get_new_refresh_token(request: TokenRefreshRequest, db: Session = Depends(get_db)):
    """Create a new access token from a valid refresh token."""
    user = auth_service.verify_refresh_token(request.refresh_token, db)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    new_access_token = await auth_service.create_access_token(payload={"sub": user.email})

    # Refresh cache for new access token
    await cache_service.set_user_for_token(new_access_token, user)

    return {
        "access_token": new_access_token,
        "refresh_token": request.refresh_token,
        "token_type": "bearer",
    }


@router.get("/confirmed_email/{token}")
async def confirmed_email(token: str, db: Session = Depends(get_db)):
    """Confirm user email using a token from the verification email."""
    email = await auth_service.get_user_by_email_token(token)
    user = await auth_repository.get_user_by_email(email, db)

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.confirmed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already confirmed")

    await auth_repository.confirm_email(user.email, db)
    return {"message": "Email confirmed"}


@router.post("/password-reset/request")
async def request_password_reset(body: PasswordResetRequest, background_tasks: BackgroundTasks, request: Request, db: Session = Depends(get_db)):
    """Request a password reset and send a reset token via email.

    For security, respond with 200 even if user not found.
    """
    user = await auth_repository.get_user_by_email(body.email, db)
    if user is None:
        # Do not reveal whether the email exists
        return {"message": "If the account exists, an email has been sent"}

    reset_token = await auth_service.create_reset_token({"sub": user.email})
    await cache_service.set_password_reset_token(reset_token, user.email)
    background_tasks.add_task(send_password_reset_email, user.email, user.username, request.base_url, reset_token)
    return {"message": "If the account exists, an email has been sent"}


@router.post("/password-reset/confirm")
async def confirm_password_reset(body: PasswordResetConfirm, db: Session = Depends(get_db)):
    """Reset password using a valid reset token. Token is single-use."""
    # Validate token structure and subject
    try:
        _ = await auth_service.get_user_by_email_token(body.token)
    except HTTPException:
        raise

    # Ensure token is present in Redis (not used/revoked/expired)
    email = await cache_service.pop_email_by_reset_token(body.token)
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

    user = await auth_repository.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.password = auth_service.hash_password(body.new_password)
    db.commit()
    return {"message": "Password updated"}
