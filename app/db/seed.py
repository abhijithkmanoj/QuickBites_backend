from app.db.base import Base
from app.db.models.user import User
from app.db.session import engine, SessionLocal
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_database():
    Base.metadata.create_all(bind=engine)


def seed_initial_data():
    with SessionLocal() as session:
        user = session.query(User).filter_by(email="admin@quickbites.local").first()
        if user is None:
            admin = User(
                name="Admin User",
                email="admin@quickbites.local",
                phone="0000000000",
                password_hash=pwd_context.hash("ChangeMe123!"),
                role="admin",
                is_active=True,
            )
            session.add(admin)
            session.commit()
            print("Created default admin user: admin@quickbites.local")
        else:
            print("Default admin user already exists.")


if __name__ == "__main__":
    create_database()
    seed_initial_data()
