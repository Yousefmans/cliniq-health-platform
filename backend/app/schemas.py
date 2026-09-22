from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Register(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    role: str = Field(pattern="^(patient|doctor)$")


class Login(BaseModel):
    email: EmailStr
    password: str


class DoctorUpdate(BaseModel):
    specialty: str = Field(min_length=2, max_length=100)
    university: str = Field(default="", max_length=150)
    qualifications: str = Field(default="", max_length=2000)
    experience_years: int = Field(default=0, ge=0, le=80)
    price: int = Field(default=0, ge=0)
    location: str = Field(default="", max_length=200)


class SlotCreate(BaseModel):
    starts_at: datetime


class Book(BaseModel):
    slot_id: int


class Reschedule(BaseModel):
    slot_id: int


class ReviewCreate(BaseModel):
    appointment_id: int
    rating: int = Field(ge=1, le=5)
    comment: str = Field(default="", max_length=2000)


class VerificationDecision(BaseModel):
    status: str = Field(pattern="^(verified|rejected)$")


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: EmailStr
    role: str
