from pydantic import BaseModel, ConfigDict, Field
from datetime import date
from typing import List, Optional

# Схемы для читателей
class ReaderCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str = 'reader'

class ReaderLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class ReaderUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None

class ReaderResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str

    model_config = ConfigDict(from_attributes=True)

# Схемы для книг
class BookCreate(BaseModel):
    title: str
    description: Optional[str] = None
    publication_date: date
    available_copies: int = Field(default=1, ge=0)
    author_ids: List[int] = Field(default=[], description="Список ID авторов")
    genre_ids: List[int] = Field(default=[], description="Список ID жанров")

class BookUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    publication_date: Optional[date] = None
    available_copies: Optional[int] = Field(None, ge=0)
    author_ids: Optional[List[int]] = None
    genre_ids: Optional[List[int]] = None

class BookResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    publication_date: date
    available_copies: int
    authors: List["AuthorResponse"] = []
    genres: List["GenreResponse"] = []

    model_config = ConfigDict(from_attributes=True)

# Схемы для авторов
class AuthorCreate(BaseModel):
    name: str
    biography: Optional[str] = None
    date_of_birth: date

class AuthorUpdate(BaseModel):
    name: Optional[str] = None
    biography: Optional[str] = None
    date_of_birth: Optional[date] = None

class AuthorResponse(BaseModel):
    id: int
    name: str
    biography: Optional[str] = None
    date_of_birth: date
    books: List["BookResponse"] = []

    model_config = ConfigDict(from_attributes=True)

# Схемы для жанров
class GenreCreate(BaseModel):
    name: str

class GenreUpdate(BaseModel):
    name: Optional[str] = None

class GenreResponse(BaseModel):
    id: int
    name: str
    books: List["BookResponse"] = []

    model_config = ConfigDict(from_attributes=True)

# Схемы для выдачи книг
class LoanCreate(BaseModel):
    book_id: int
    issue_date: date = Field(default_factory=date.today)
    return_date: Optional[date] = None

class LoanReturn(BaseModel):
    return_date: date = Field(default_factory=date.today)

class LoanResponse(BaseModel):
    id: int
    book_id: int
    reader_id: int
    issue_date: date
    return_date: Optional[date] = None
    book: "BookResponse"
    reader: "ReaderResponse"

    model_config = ConfigDict(from_attributes=True)

# Разрешение циклических ссылок для Pydantic
BookResponse.model_rebuild()
AuthorResponse.model_rebuild()
GenreResponse.model_rebuild()
LoanResponse.model_rebuild()