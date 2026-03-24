from sqlalchemy import text

from app.db.session import SessionLocal, engine
from app.models import Base, User, Project, File


def test_db_connection():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1
    print("DB connection: OK")


def test_create_tables():
    Base.metadata.create_all(bind=engine)
    print("Tables created: OK")


def test_crud():
    db = SessionLocal()

    try:
        user = User(username="testuser", email="test@example.com", password="hashed_pw")
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Created user: id={user.id}, username={user.username}")

        project = Project(name="Test Project", user_id=user.id)
        db.add(project)
        db.commit()
        db.refresh(project)
        print(f"Created project: id={project.id}, name={project.name}")

        file = File(
            filename="test.txt",
            s3_key="test/test.txt",
            uploaded_by_id=user.id,
            project_id=project.id,
        )
        db.add(file)
        db.commit()
        db.refresh(file)
        print(f"Created file: id={file.id}, filename={file.filename}")

    finally:
        db.delete(file)
        db.delete(project)
        db.delete(user)
        db.commit()
        db.close()
        print("Cleanup done")


if __name__ == "__main__":
    test_db_connection()
    test_create_tables()
    test_crud()