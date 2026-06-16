from pydantic import BaseModel, AnyUrl, EmailStr
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from database import Base
from datetime import datetime

class ShortenRequest(BaseModel):
    url:AnyUrl

class SignUpRequest(BaseModel):
    email: EmailStr
    password: str

class LogInRequest(BaseModel):
    email: EmailStr
    password: str

class URL(Base):
    __tablename__ = "urls"

    short_code = Column(String, primary_key=True)
    url = Column(String)
    clicks = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    owner_id = Column(Integer, ForeignKey("users.id"),  nullable=True)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.now)