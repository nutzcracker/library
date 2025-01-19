import sys
import os
import logging
from logging.handlers import RotatingFileHandler  # Для ротации логов

# Добавляем корневую папку проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, Depends, HTTPException, status, Query
from datetime import datetime, timedelta, UTC
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.models import Reader, Book, Author, Genre, Loan
from app.database import SessionLocal
from app.schemas import (
    ReaderCreate, ReaderLogin, Token, BookCreate, BookUpdate, AuthorCreate, AuthorUpdate,
    ReaderUpdate, LoanCreate, LoanReturn, BookResponse, AuthorResponse, ReaderResponse, LoanResponse
)
from fastapi.security import OAuth2PasswordBearer
from typing import List

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Вывод в консоль
        logging.FileHandler('app.log')  # Запись в файл app.log
    ]
)

# Альтернативно, можно настроить ротацию логов (например, файл не больше 10 МБ, максимум 5 файлов)
handler = RotatingFileHandler(
    'app.log', maxBytes=10 * 1024 * 1024, backupCount=5  # 10 МБ на файл, 5 файлов в ротации
)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logger = logging.getLogger(__name__)
logger.addHandler(handler)

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

SECRET_KEY = "bZVnt1Rcjo7ILonGa6dHHh3LxRrJXezM"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/register")
def register(reader: ReaderCreate, db: Session = Depends(get_db)):
    hashed_password = pwd_context.hash(reader.password)
    db_reader = Reader(
        name=reader.name,
        email=reader.email,
        hashed_password=hashed_password,
        role=reader.role,
    )
    db.add(db_reader)
    db.commit()
    db.refresh(db_reader)
    logger.info(f"Зарегистрирован новый пользователь: {reader.email}")
    return {"message": "Пользователь успешно зарегистрирован"}

@app.post("/login", response_model=Token)
def login(reader: ReaderLogin, db: Session = Depends(get_db)):
    db_reader = db.query(Reader).filter(Reader.email == reader.email).first()
    if not db_reader or not pwd_context.verify(reader.password, db_reader.hashed_password):
        logger.warning(f"Неудачная попытка входа для пользователя: {reader.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_reader.email, "role": db_reader.role},
        expires_delta=access_token_expires,
    )
    logger.info(f"Успешный вход пользователя: {reader.email}")
    return {"access_token": access_token, "token_type": "bearer"}

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось подтвердить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    db_reader = db.query(Reader).filter(Reader.email == email).first()
    if db_reader is None:
        raise credentials_exception
    return db_reader

def get_current_admin(current_user: Reader = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для выполнения операции",
        )
    return current_user

# Эндпоинт только для администраторов
@app.get("/admin-only")
def admin_only(current_user: Reader = Depends(get_current_admin)):
    return {"message": "Этот эндпоинт доступен только администраторам"}

# Эндпоинт для всех авторизованных пользователей
@app.get("/user-info", response_model=ReaderResponse)
def user_info(current_user: Reader = Depends(get_current_user)):
    return current_user

# CRUD для книг
@app.post("/books/", response_model=BookResponse)
def create_book(book: BookCreate, db: Session = Depends(get_db), current_user: Reader = Depends(get_current_admin)):
    db_book = Book(**book.dict())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    logger.info(f"Создана новая книга: {book.title}")
    return db_book

@app.get("/books/{book_id}", response_model=BookResponse)
def read_book(book_id: int, db: Session = Depends(get_db)):
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if db_book is None:
        logger.error(f"Книга с ID {book_id} не найдена")
        raise HTTPException(status_code=404, detail="Книга не найдена")
    return db_book

@app.put("/books/{book_id}", response_model=BookResponse)
def update_book(book_id: int, book: BookUpdate, db: Session = Depends(get_db), current_user: Reader = Depends(get_current_admin)):
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if db_book is None:
        logger.error(f"Книга с ID {book_id} не найдена")
        raise HTTPException(status_code=404, detail="Книга не найдена")
    for key, value in book.dict().items():
        setattr(db_book, key, value)
    db.commit()
    db.refresh(db_book)
    logger.info(f"Обновлена книга с ID {book_id}")
    return db_book

@app.delete("/books/{book_id}")
def delete_book(book_id: int, db: Session = Depends(get_db), current_user: Reader = Depends(get_current_admin)):
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if db_book is None:
        logger.error(f"Книга с ID {book_id} не найдена")
        raise HTTPException(status_code=404, detail="Книга не найдена")
    db.delete(db_book)
    db.commit()
    logger.info(f"Удалена книга с ID {book_id}")
    return {"message": "Книга успешно удалена"}

# Пагинация для списка книг
@app.get("/books/", response_model=List[BookResponse])
def list_books(
    skip: int = 0,
    limit: int = Query(default=10, le=100),
    db: Session = Depends(get_db)
):
    books = db.query(Book).offset(skip).limit(limit).all()
    logger.info(f"Запрошен список книг. Пропущено: {skip}, Лимит: {limit}")
    return books

# CRUD для авторов
@app.post("/authors/", response_model=AuthorResponse)
def create_author(author: AuthorCreate, db: Session = Depends(get_db), current_user: Reader = Depends(get_current_admin)):
    db_author = Author(**author.dict())
    db.add(db_author)
    db.commit()
    db.refresh(db_author)
    logger.info(f"Создан новый автор: {author.name}")
    return db_author

@app.get("/authors/{author_id}", response_model=AuthorResponse)
def read_author(author_id: int, db: Session = Depends(get_db)):
    db_author = db.query(Author).filter(Author.id == author_id).first()
    if db_author is None:
        logger.error(f"Автор с ID {author_id} не найден")
        raise HTTPException(status_code=404, detail="Автор не найден")
    return db_author

@app.put("/authors/{author_id}", response_model=AuthorResponse)
def update_author(author_id: int, author: AuthorUpdate, db: Session = Depends(get_db), current_user: Reader = Depends(get_current_admin)):
    db_author = db.query(Author).filter(Author.id == author_id).first()
    if db_author is None:
        logger.error(f"Автор с ID {author_id} не найден")
        raise HTTPException(status_code=404, detail="Автор не найден")
    for key, value in author.dict().items():
        setattr(db_author, key, value)
    db.commit()
    db.refresh(db_author)
    logger.info(f"Обновлен автор с ID {author_id}")
    return db_author

@app.delete("/authors/{author_id}")
def delete_author(author_id: int, db: Session = Depends(get_db), current_user: Reader = Depends(get_current_admin)):
    db_author = db.query(Author).filter(Author.id == author_id).first()
    if db_author is None:
        logger.error(f"Автор с ID {author_id} не найден")
        raise HTTPException(status_code=404, detail="Автор не найден")
    db.delete(db_author)
    db.commit()
    logger.info(f"Удален автор с ID {author_id}")
    return {"message": "Автор успешно удален"}

# Пагинация для списка авторов
@app.get("/authors/", response_model=List[AuthorResponse])
def list_authors(
    skip: int = 0,
    limit: int = Query(default=10, le=100),
    db: Session = Depends(get_db)
):
    authors = db.query(Author).offset(skip).limit(limit).all()
    logger.info(f"Запрошен список авторов. Пропущено: {skip}, Лимит: {limit}")
    return authors

# Управление читателями
@app.get("/readers/", response_model=List[ReaderResponse])
def list_readers(db: Session = Depends(get_db), current_user: Reader = Depends(get_current_admin)):
    return db.query(Reader).all()

@app.put("/readers/{reader_id}", response_model=ReaderResponse)
def update_reader(reader_id: int, reader: ReaderUpdate, db: Session = Depends(get_db), current_user: Reader = Depends(get_current_user)):
    if current_user.id != reader_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Недостаточно прав для выполнения операции")
    db_reader = db.query(Reader).filter(Reader.id == reader_id).first()
    if db_reader is None:
        logger.error(f"Читатель с ID {reader_id} не найден")
        raise HTTPException(status_code=404, detail="Читатель не найден")
    for key, value in reader.dict().items():
        setattr(db_reader, key, value)
    db.commit()
    db.refresh(db_reader)
    logger.info(f"Обновлен читатель с ID {reader_id}")
    return db_reader

# Выдача книг
@app.post("/loans/", response_model=LoanResponse)
def create_loan(loan: LoanCreate, db: Session = Depends(get_db), current_user: Reader = Depends(get_current_user)):
    db_book = db.query(Book).filter(Book.id == loan.book_id).first()
    if db_book is None:
        logger.error(f"Книга с ID {loan.book_id} не найдена")
        raise HTTPException(status_code=404, detail="Книга не найдена")
    if db_book.available_copies <= 0:
        logger.warning(f"Нет доступных экземпляров книги с ID {loan.book_id}")
        raise HTTPException(status_code=400, detail="Нет доступных экземпляров книги")

    active_loans = db.query(Loan).filter(Loan.reader_id == current_user.id, Loan.return_date == None).count()
    if active_loans >= 5:
        logger.warning(f"Читатель {current_user.name} превысил лимит книг")
        raise HTTPException(status_code=400, detail="Превышено количество одновременно взятых книг")

    db_loan = Loan(
        book_id=loan.book_id,
        reader_id=current_user.id,
        issue_date=datetime.utcnow(),
        return_date=None
    )
    db_book.available_copies -= 1
    db.add(db_loan)
    db.commit()
    db.refresh(db_loan)
    logger.info(f"Книга {db_book.title} выдана читателю {current_user.name}")
    return db_loan

@app.put("/loans/{loan_id}/return")
def return_loan(loan_id: int, db: Session = Depends(get_db), current_user: Reader = Depends(get_current_user)):
    db_loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if db_loan is None:
        logger.error(f"Выдача книги с ID {loan_id} не найдена")
        raise HTTPException(status_code=404, detail="Выдача книги не найдена")
    if db_loan.reader_id != current_user.id and current_user.role != "admin":
        logger.warning(f"Попытка возврата книги читателем {current_user.name} без прав")
        raise HTTPException(status_code=403, detail="Недостаточно прав для выполнения операции")

    db_book = db.query(Book).filter(Book.id == db_loan.book_id).first()
    db_book.available_copies += 1
    db_loan.return_date = datetime.utcnow()
    db.commit()
    logger.info(f"Книга {db_book.title} возвращена читателем {current_user.name}")
    return {"message": "Книга успешно возвращена"}