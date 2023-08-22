from sqlalchemy import Boolean, Column, ForeignKey, String, DateTime, Integer
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import List, Optional
from datetime import datetime
from passlib.context import CryptContext

from backend.database import Base

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    email: Mapped[str] = mapped_column(String, unique=True)
    name = Column(String)
    lastname = Column(String)
    hashed_password = Column(String)

    films = relationship("Movie", back_populates="owner")

    def verify_password(self, password: str):
        return pwd_context.verify(password, self.hashed_password)
    

class Movie(Base):
    __tablename__ = "movies"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id'))
    
    
    film_name: Mapped[str]
    director: Mapped[Optional[str]]
    # comment: Mapped[Optional[str]]
    
    owner = relationship("User", back_populates="films")

