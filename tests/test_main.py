import sys
import os
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal, Base, engine
from app.models import Reader
from sqlalchemy.orm import Session
import uuid

# Добавляем корневую папку проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Фикстура для клиента
@pytest.fixture(scope="module")
def client():
    with TestClient(app) as client:
        yield client

# Фикстура для базы данных
@pytest.fixture(scope="function")
def db_session():
    # Создаем все таблицы в базе данных
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db  # Возвращаем сессию для использования в тестах
    # Очищаем базу данных после завершения теста
    db.query(Reader).delete()
    db.commit()
    db.close()

# Тест регистрации пользователя
def test_register(client, db_session: Session):
    # Генерируем уникальный email для каждого теста
    unique_email = f"test_{uuid.uuid4()}@example.com"
    response = client.post(
        "/register",
        json={
            "name": "Test User",
            "email": unique_email,
            "password": "testpassword",
            "role": "reader"
        }
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Пользователь успешно зарегистрирован"}

    # Проверяем, что пользователь действительно создан в базе данных
    db_user = db_session.query(Reader).filter(Reader.email == unique_email).first()
    assert db_user is not None
    assert db_user.name == "Test User"
    assert db_user.role == "reader"

# Тест входа пользователя
def test_login(client, db_session: Session):
    # Генерируем уникальный email для каждого теста
    unique_email = f"test_{uuid.uuid4()}@example.com"
    # Сначала регистрируем пользователя
    client.post(
        "/register",
        json={
            "name": "Test User",
            "email": unique_email,
            "password": "testpassword",
            "role": "reader"
        }
    )
    # Пытаемся войти
    response = client.post(
        "/login",
        json={
            "email": unique_email,
            "password": "testpassword"
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()