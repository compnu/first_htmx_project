from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime


class UserBase(BaseModel):
    email: str
    username: str
    name: str
    lastname: str


class UserCreate(UserBase):
    model_config = ConfigDict(from_attributes=True)
    hashed_password: str

    
class User(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: int   
        
class MovieBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    film_name: str
    director: Optional[str]
    
    
class MovieCreate(MovieBase):
    pass


class Movie(MovieBase):
    id: int
    owner_id: int
    
    # comment: Optional[str]