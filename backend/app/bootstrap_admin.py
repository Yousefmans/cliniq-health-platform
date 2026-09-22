import os

from sqlalchemy import select

from .database import Base, SessionLocal, engine
from .models import User
from .security import hash_password, secret


def main():
    secret()
    email = os.environ["BOOTSTRAP_ADMIN_EMAIL"].strip().lower()
    password = os.environ["BOOTSTRAP_ADMIN_PASSWORD"]
    if len(password) < 12:
        raise ValueError("Admin password must contain at least 12 characters")
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if db.scalar(select(User.id).where(User.email == email)):
            raise ValueError("Email already exists")
        db.add(User(name="Platform Admin", email=email, role="admin", password_hash=hash_password(password)))
        db.commit()
    print("Admin account created")


if __name__ == "__main__":
    main()
