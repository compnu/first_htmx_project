from sqlalchemy import Boolean, Column, ForeignKey, String, DateTime, Integer
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import List, Optional
from datetime import datetime
from passlib.hash import bcrypt

from backend.database import Base


class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True)
    username = Column(String)
    name = Column(String)
    lastname = Column(String)
    hashed_password = Column(String)

    calls = relationship("Call", back_populates="owner")

    def verify_password(self, password: str):
        return bcrypt.verify(password, self.hashed_password)
    

class Call(Base):
    __tablename__ = "calls"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id'))
    
    
    fund_name: Mapped[str]
    call_number: Mapped[Optional[str]]
    
    owner = relationship("User", back_populates="calls")

