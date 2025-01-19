from sqlalchemy import Column, Integer, String, Date, ForeignKey, Table
from sqlalchemy.orm import relationship
from .database import Base


book_author = Table(
    'book_author',
    Base.metadata,
    Column('book_id', Integer, ForeignKey('books.id')),
    Column('author_id', Integer, ForeignKey('authors.id'))
)

book_genre = Table(
    'book_genre',
    Base.metadata,
    Column('book_id', Integer, ForeignKey('books.id')),
    Column('genre_id', Integer, ForeignKey('genres.id'))
)

class Genre(Base):
    __tablename__ = 'genres'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    books = relationship('Book', secondary=book_genre, back_populates='genres')

class Book(Base):
    __tablename__ = 'books'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    publication_date = Column(Date)
    available_copies = Column(Integer, default=0)

    authors = relationship('Author', secondary=book_author, back_populates='books')
    genres = relationship('Genre', secondary=book_genre, back_populates='books')
    loans = relationship('Loan', back_populates='book')

class Author(Base):
    __tablename__ = 'authors'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    biography = Column(String)
    date_of_birth = Column(Date)
    books = relationship('Book', secondary=book_author, back_populates='authors')

class Reader(Base):
    __tablename__ = 'readers'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True)
    role = Column(String, default='reader')
    loans = relationship('Loan', back_populates='reader')

class Loan(Base):
    __tablename__ = 'loans'
    id = Column(Integer, primary_key=True)
    book_id = Column(Integer, ForeignKey('books.id'))
    reader_id = Column(Integer, ForeignKey('readers.id'))
    issue_date = Column(Date)
    return_date = Column(Date)

    book = relationship('Book', back_populates='loans')
    reader = relationship('Reader', back_populates='loans')