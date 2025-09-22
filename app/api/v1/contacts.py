from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from ...conf.config import engine, get_db
from ...db.base import Base
from ...schemas.contacts import ContactCreate, ContactUpdate, ContactRead
from ...repositories.contacts import (
    contacts_repository
)
from ...services.auth import auth_service

"""Contacts API router.

Provides CRUD endpoints for managing contacts and a helper endpoint for
upcoming birthdays. All endpoints require authentication.
"""

router = APIRouter(tags=["contacts"], prefix="/contacts", dependencies=[Depends(auth_service.get_current_user)])

Base.metadata.create_all(engine)

@router.post("/", response_model=ContactRead, status_code=status.HTTP_201_CREATED)
def create_contact_ep(payload: ContactCreate, db: Session = Depends(get_db)):
    """Create a new contact.

    Args:
        payload: Contact payload.
        db: Database session.
    Returns:
        The created contact.
    """
    return contacts_repository.create_contact(db, payload)

@router.get("/", response_model=list[ContactRead])
def list_contacts_ep(
    db: Session = Depends(get_db),
    search: str | None = Query(default=None, description="free text: first_name/last_name/email"),
    first_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
    skip: int = 0,
    limit: int = Query(100, le=500)
):
    """List contacts with optional filters and pagination."""
    return contacts_repository.list_contacts(db, search, first_name, last_name, email, skip, limit)

@router.get("/{contact_id}", response_model=ContactRead)
def get_contact_ep(contact_id: int, db: Session = Depends(get_db)):
    """Get a single contact by id."""
    obj = contacts_repository.get_contact(db, contact_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Contact not found")
    return obj

@router.put("/{contact_id}", response_model=ContactRead)
def update_contact_ep(contact_id: int, payload: ContactUpdate, db: Session = Depends(get_db)):
    """Update an existing contact by id."""
    obj = contacts_repository.update_contact(db, contact_id, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Contact not found")
    return obj

@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact_ep(contact_id: int, db: Session = Depends(get_db)):
    """Delete a contact by id."""
    ok = contacts_repository.delete_contact(db, contact_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Contact not found")
    return

@router.get("/upcoming/birthdays", response_model=list[ContactRead])
def birthdays_next_7_days_ep(db: Session = Depends(get_db)):
    """List contacts with birthdays in the next 7 days."""
    return contacts_repository.birthdays_next_7_days(db)
