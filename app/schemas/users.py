from pydantic import BaseModel, EmailStr, ConfigDict

class UserRegisterSchema(BaseModel):
    id: int
    username: str
    email: str
    avatar: str
    password: str
    role: str | None = None

    model_config = ConfigDict(from_attributes=True)

class UserResponseSchema(BaseModel):
    username: str
    email: EmailStr
    role: str | None = None

class TokenModel(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class PasswordResetRequest(BaseModel):
    """Schema to request a password reset by email."""
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    """Schema to confirm password reset with token and new password."""
    token: str
    new_password: str