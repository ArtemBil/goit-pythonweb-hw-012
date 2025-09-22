from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.sql import select, or_, func
from datetime import date, timedelta

from starlette import status

from ..db.models import Contact
from ..schemas.contacts import ContactCreate, ContactUpdate

"""
Contacts repository provides CRUD operations and business queries
for `Contact` entities using a synchronous SQLAlchemy ORM `Session`.
"""

class ContactsRepository:
    """Repository for `Contact` entity operations."""

    def create_contact(self, db: Session, contact: ContactCreate) -> Contact:
        """Create a new contact.

        Raises an HTTP 400 if email already exists.
        """
        new_contact = Contact(**contact.model_dump())
        db.add(new_contact)
        try:
            db.commit()
            db.refresh(new_contact)
            return new_contact
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contact with this email already exists"
            )

    def get_contact(self, db: Session, contact_id: int):
        """Return contact by id or None."""
        return db.get(Contact, contact_id)

    def list_contacts(
        self,
        db: Session,
        search: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        email: str | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> list[Contact]:
        """List contacts with optional text filters and pagination."""
        query = select(Contact)
        if search:
            like = f"%{search}%"
            query = query.where(
                or_(
                    Contact.first_name.ilike(like),
                    Contact.last_name.ilike(like),
                    Contact.email.ilike(like),
                )
            )
        if first_name:
            query = query.where(Contact.first_name.ilike(f"%{first_name}%"))
        if last_name:
            query = query.where(Contact.last_name.ilike(f"%{last_name}%"))
        if email:
            query = query.where(Contact.email.ilike(f"%{email}%"))
        query = query.offset(skip).limit(limit)
        return db.execute(query).scalars().all()

    def update_contact(self, db: Session, contact_id: int, data: ContactUpdate) -> Contact | None:
        """Update a contact by id returning the updated entity or None if not found."""
        obj = db.get(Contact, contact_id)
        if not obj:
            return None
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(obj, k, v)
        db.commit()
        db.refresh(obj)
        return obj

    def delete_contact(self, db: Session, contact_id: int) -> bool:
        """Delete a contact by id, returning True if deleted, False if not found."""
        obj = db.get(Contact, contact_id)
        if not obj:
            return False
        db.delete(obj)
        db.commit()
        return True

    def birthdays_next_7_days(self, db: Session) -> list[Contact]:
        """Return contacts with birthdays within the next 7 days.

        Handles year wrap-around using day-of-year computations.
        """
        today = date.today()
        end = today + timedelta(days=7)

        doy = func.extract("doy", Contact.birthday)
        t_doy = func.extract("doy", func.make_date(2000, today.month, today.day))
        e_doy = func.extract("doy", func.make_date(2000, end.month, end.day))

        if end.year == today.year:
            cond = (doy >= t_doy) & (doy <= e_doy)
        else:
            cond = (doy >= t_doy) | (doy <= e_doy)

        return db.execute(select(Contact).where(Contact.birthday.is_not(None), cond)).scalars().all()


contacts_repository = ContactsRepository()