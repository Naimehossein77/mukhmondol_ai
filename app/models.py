# app/models.py

from pydantic import BaseModel, EmailStr

class PhotographerBase(BaseModel):
    name: str
    email: EmailStr
    # Add any other relevant fields

class PhotographerCreate(PhotographerBase):
    password: str  # If you want to include a password
