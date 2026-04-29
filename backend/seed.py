"""
Run: python seed.py
Tạo user mặc định cho demo
"""
from app.core.database import SessionLocal, engine
from app.core.database import Base
from app.models.models import User
from passlib.context import CryptContext

Base.metadata.create_all(bind=engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def seed():
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "admin").first()
        if existing:
            print("User 'admin' already exists")
            return
        user = User(
            username="admin",
            hashed_password=pwd_context.hash("postpilot2024"),
        )
        db.add(user)
        db.commit()
        print("Created user: admin / postpilot2024")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
