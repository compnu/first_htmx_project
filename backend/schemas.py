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
        
class CallBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    fund_name: str
    
    
class CallCreate(CallBase):
    pass


class Call(CallBase):
    id: int
    owner_id: int
    
    call_number: Optional[str]