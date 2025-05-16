from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List, Union
from datetime import datetime
import uuid

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserApproval(BaseModel):
    user_id: Union[uuid.UUID, str]
    approve: bool
    
    @field_validator('user_id')
    def validate_uuid(cls, v):
        if isinstance(v, str):
            try:
                return uuid.UUID(v)
            except ValueError:
                raise ValueError('Invalid UUID format')
        return v

class UserAdmin(BaseModel):
    user_id: Union[uuid.UUID, str]
    make_admin: bool
    
    @field_validator('user_id')
    def validate_uuid(cls, v):
        if isinstance(v, str):
            try:
                return uuid.UUID(v)
            except ValueError:
                raise ValueError('Invalid UUID format')
        return v

class UserActivation(BaseModel):
    user_id: Union[uuid.UUID, str]
    activate: bool
    
    @field_validator('user_id')
    def validate_uuid(cls, v):
        if isinstance(v, str):
            try:
                return uuid.UUID(v)
            except ValueError:
                raise ValueError('Invalid UUID format')
        return v

class User(UserBase):
    id: uuid.UUID
    is_admin: bool
    is_active: bool
    is_approved: bool
    created_at: datetime
    
    class Config:
        orm_mode = True

class UserList(BaseModel):
    users: List[User]

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    is_admin: Optional[bool] = None
