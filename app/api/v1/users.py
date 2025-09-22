from fastapi import APIRouter, HTTPException, status, Request, UploadFile
from fastapi.params import Depends, File
from sqlalchemy.orm import Session

from ...schemas.users import UserResponseSchema
from ...services.auth import auth_service
from ...repositories.auth import auth_repository
from ...conf.limiter import limiter
from ...conf.config import app_settings, get_db
from ...services.upload_file import UploadFileService

"""Users API router providing endpoints for profile info and avatar updates."""
router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponseSchema)
@limiter.limit("10/second")
async def me(request: Request, user: UserResponseSchema = Depends(auth_service.get_current_user)):
    """Return the current authenticated user's public info."""
    return user

@router.patch("/avatar", response_model=UserResponseSchema)
async def update_user_avatar(
        file: UploadFile = File(),
        user: UserResponseSchema = Depends(auth_service.get_current_user),
        db: Session = Depends(get_db)
):
    """Update user's avatar; only admins are allowed to change avatar."""
    if getattr(user, "role", "user") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can update their avatar")

    avatar_url = UploadFileService(
        app_settings.CLOUDINARY_NAME,
        app_settings.CLOUDINARY_API_KEY,
        app_settings.CLOUDINARY_API_SECRET
    ).upload_file(file, user.username)

    user = await auth_repository.update_avatar_url(user.email, avatar_url, db)

    return user