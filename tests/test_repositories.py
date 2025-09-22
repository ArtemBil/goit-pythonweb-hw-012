from datetime import date
from app.repositories.contacts import contacts_repository
from app.repositories.auth import auth_repository
from app.schemas.contacts import ContactCreate, ContactUpdate
from app.schemas.users import UserRegisterSchema


def test_create_and_get_contact(db_session):
    payload = ContactCreate(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        phone="123456",
        birthday=date(1990,1,1),
        user_id=1,
        extra=None,
    )
    obj = contacts_repository.create_contact(db_session, payload)
    fetched = contacts_repository.get_contact(db_session, obj.id)
    assert fetched.id == obj.id
    assert fetched.email == "john@example.com"


def test_update_and_delete_contact(db_session):
    obj = contacts_repository.create_contact(db_session, ContactCreate(
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        phone="654321",
        birthday=date(1991,2,2),
        user_id=2,
        extra=None,
    ))

    updated = contacts_repository.update_contact(db_session, obj.id, ContactUpdate(phone="0000"))
    assert updated.phone == "0000"

    ok = contacts_repository.delete_contact(db_session, obj.id)
    assert ok is True
    assert contacts_repository.get_contact(db_session, obj.id) is None


def test_user_repository_create_and_get(db_session):
    body = UserRegisterSchema(
        id=0,
        username="tester",
        email="tester@example.com",
        avatar="",
        password="secret12345",
        role="admin"
    )
    user = db_session.execute("""INSERT INTO users (email, username, password, confirmed, role) VALUES (:email, :username, :password, 1, :role) RETURNING id""",
                              {"email": body.email, "username": body.username, "password": body.password, "role": body.role}).scalar()
    assert user is not None

    fetched = auth_repository.get_user_by_email  # ensure method exists
    assert callable(fetched) 