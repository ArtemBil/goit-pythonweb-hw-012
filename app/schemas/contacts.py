from pydantic import BaseModel, EmailStr, Field
from datetime import date

class ContactBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=80)
    last_name: str = Field(..., min_length=1, max_length=80)
    email: EmailStr
    phone: str = Field(..., min_length=1, max_length=32)
    birthday: date
    extra: str | None = None
    user_id: int

class ContactCreate(ContactBase):
    pass

class ContactUpdate(ContactBase):
    first_name: str | None = Field(default=None, min_length=1, max_length=80)
    last_name: str | None = Field(default=None, min_length=1, max_length=80)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=32)
    birthday: date | None = None
    extra: str | None = None
    user_id: int | None = None

class ContactRead(ContactBase):
    id: int
    class Config:
        from_attributes = True