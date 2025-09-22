from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.db.models import User
from app.schemas.users import UserRegisterSchema

class UserRepository:
    """Repository for `User` entity operations using SQLAlchemy Session."""
    async def get_user_by_email(self, email: str, db: Session):
        """Return a user by email or None."""
        return db.query(User).filter_by(email=email).first()

    async def get_user_refresh_token(self, email: str, refresh_token: str, db: Session):
        """Return a user by email with matching refresh token or None."""
        return db.query(User).filter_by(email=email, refresh_token=refresh_token).first()

    async def create_user(self, body: UserRegisterSchema, db: Session):
        """Create a new user, ensuring unique email. Raises HTTP 400 on conflict."""
        new_user = User(**body.model_dump())
        db.add(new_user)
        try:
            db.commit()
            db.refresh(new_user)
            return new_user
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )

    async def confirm_email(self, email: str, db: Session):
        """Mark user's email as confirmed. Raises 404 if user not found."""
        user = await self.get_user_by_email(email, db)

        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        user.confirmed = True
        db.commit()

    async def update_avatar_url(self, email: str, avatar_url: str, db: Session):
        """Update user's avatar URL and return updated user."""
        user = await self.get_user_by_email(email, db)
        user.avatar = avatar_url
        db.commit()
        db.refresh(user)
        return user


auth_repository = UserRepository()