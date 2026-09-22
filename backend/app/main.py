import os
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Appointment, AuditLog, Doctor, Review, Slot, Subscription, User
from .schemas import Book, DoctorUpdate, Login, Register, Reschedule, ReviewCreate, SlotCreate, UserPublic, VerificationDecision
from .security import current_user, hash_password, issue_token, require_role, verify_password

app = FastAPI(title="ClinIQ API", version="0.1.0")
origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["GET", "POST", "PATCH"], allow_headers=["Authorization", "Content-Type"])


@app.on_event("startup")
def initialize():
    from .security import secret
    secret()
    # Simple initial schema for the prototype. Use migrations before production changes.
    Base.metadata.create_all(engine)


def audit(db: Session, user: User, action: str, resource: str):
    db.add(AuditLog(user_id=user.id, action=action, resource=resource))


def own_doctor(db: Session, user: User) -> Doctor:
    doctor = db.scalar(select(Doctor).where(Doctor.user_id == user.id))
    if not doctor:
        raise HTTPException(404, "Doctor profile not found")
    return doctor


def doctor_public(db: Session, d: Doctor):
    avg, count = db.execute(select(func.avg(Review.rating), func.count(Review.id)).where(Review.doctor_id == d.id)).one()
    return {"id": d.id, "name": d.user.name, "specialty": d.specialty, "university": d.university,
            "qualifications": d.qualifications, "experience_years": d.experience_years, "price": d.price,
            "location": d.location, "verification_status": d.verification_status,
            "rating_avg": round(float(avg), 1) if avg else None, "reviews_count": count}


def ensure_future(when: datetime) -> datetime:
    if when.tzinfo is None or when.utcoffset() is None:
        raise HTTPException(422, "Timestamp must include a timezone")
    value = when.astimezone(timezone.utc).replace(tzinfo=None)
    if value <= datetime.now(timezone.utc).replace(tzinfo=None):
        raise HTTPException(422, "Slot must be in the future")
    return value


@app.get("/api/v1/health")
def health():
    return {"status": "ok"}


@app.post("/api/v1/auth/register", status_code=201)
def register(data: Register, db: Session = Depends(get_db)):
    email = data.email.lower()
    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(409, "Email is already registered")
    user = User(name=data.name, email=email, password_hash=hash_password(data.password), role=data.role)
    db.add(user)
    try:
        db.flush()
        if data.role == "doctor":
            db.add(Doctor(user_id=user.id, specialty="Unspecified"))
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Email is already registered")
    return {"access_token": issue_token(user), "token_type": "bearer", "user": UserPublic.model_validate(user)}


@app.post("/api/v1/auth/login")
def login(data: Login, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    if not user or not user.is_active or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    return {"access_token": issue_token(user), "token_type": "bearer", "user": UserPublic.model_validate(user)}


@app.get("/api/v1/auth/me", response_model=UserPublic)
def me(user: User = Depends(current_user)):
    return user


@app.get("/api/v1/doctors")
def doctors(specialty: str | None = None, location: str | None = None,
            q: str | None = None, max_price: int | None = Query(default=None, ge=0),
            limit: int = Query(default=20, ge=1, le=100), offset: int = Query(default=0, ge=0),
            db: Session = Depends(get_db)):
    stmt = select(Doctor).join(User).where(Doctor.verification_status == "verified", User.is_active.is_(True))
    if specialty:
        stmt = stmt.where(Doctor.specialty.ilike(f"%{specialty}%"))
    if location:
        stmt = stmt.where(Doctor.location.ilike(f"%{location}%"))
    if q:
        stmt = stmt.where((Doctor.specialty.ilike(f"%{q}%")) | (User.name.ilike(f"%{q}%")))
    if max_price is not None:
        stmt = stmt.where(Doctor.price <= max_price)
    return [doctor_public(db, d) for d in db.scalars(stmt.order_by(Doctor.id).offset(offset).limit(limit)).all()]


@app.get("/api/v1/doctors/{doctor_id}")
def doctor_detail(doctor_id: int, db: Session = Depends(get_db)):
    d = db.get(Doctor, doctor_id)
    if not d or d.verification_status != "verified" or not d.user.is_active:
        raise HTTPException(404, "Doctor not found")
    return doctor_public(db, d)


@app.get("/api/v1/doctors/{doctor_id}/slots")
def doctor_slots(doctor_id: int, db: Session = Depends(get_db)):
    d = db.get(Doctor, doctor_id)
    if not d or d.verification_status != "verified":
        raise HTTPException(404, "Doctor not found")
    slots = db.scalars(select(Slot).where(Slot.doctor_id == doctor_id, Slot.is_available.is_(True),
                    Slot.starts_at > datetime.now(timezone.utc).replace(tzinfo=None)).order_by(Slot.starts_at)).all()
    return [{"id": s.id, "starts_at": s.starts_at.replace(tzinfo=timezone.utc).isoformat()} for s in slots]


@app.get("/api/v1/doctor/profile")
def my_doctor_profile(db: Session = Depends(get_db), user: User = Depends(require_role("doctor"))):
    return doctor_public(db, own_doctor(db, user))


@app.patch("/api/v1/doctor/profile")
def update_doctor_profile(data: DoctorUpdate, db: Session = Depends(get_db), user: User = Depends(require_role("doctor"))):
    d = own_doctor(db, user)
    for field, value in data.model_dump().items():
        setattr(d, field, value)
    audit(db, user, "update_profile", f"doctor:{d.id}")
    db.commit()
    return doctor_public(db, d)


@app.post("/api/v1/doctor/slots", status_code=201)
def add_slot(data: SlotCreate, db: Session = Depends(get_db), user: User = Depends(require_role("doctor"))):
    d = own_doctor(db, user)
    when = ensure_future(data.starts_at)
    slot = Slot(doctor_id=d.id, starts_at=when)
    db.add(slot)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Slot already exists")
    return {"id": slot.id, "starts_at": when.replace(tzinfo=timezone.utc).isoformat()}


@app.get("/api/v1/doctor/appointments")
def doctor_appointments(db: Session = Depends(get_db), user: User = Depends(require_role("doctor"))):
    d = own_doctor(db, user)
    return [{"id": a.id, "patient_id": a.patient_id, "slot_id": a.slot_id, "status": a.status}
            for a in db.scalars(select(Appointment).where(Appointment.doctor_id == d.id).order_by(Appointment.id.desc())).all()]


@app.post("/api/v1/appointments", status_code=201)
def book(data: Book, db: Session = Depends(get_db), user: User = Depends(require_role("patient"))):
    slot = db.get(Slot, data.slot_id)
    if not slot or slot.starts_at <= datetime.now(timezone.utc).replace(tzinfo=None):
        raise HTTPException(404, "Available slot not found")
    doctor = db.get(Doctor, slot.doctor_id)
    if not doctor or doctor.verification_status != "verified" or not doctor.user.is_active:
        raise HTTPException(404, "Available slot not found")
    if db.execute(update(Slot).where(Slot.id == slot.id, Slot.is_available.is_(True)).values(is_available=False)).rowcount != 1:
        db.rollback()
        raise HTTPException(409, "Slot has already been booked")
    a = Appointment(patient_id=user.id, doctor_id=doctor.id, slot_id=slot.id)
    db.add(a)
    db.flush()
    audit(db, user, "book", f"appointment:{a.id}")
    db.commit()
    return {"id": a.id, "status": a.status, "doctor_id": a.doctor_id, "slot_id": a.slot_id}


@app.get("/api/v1/appointments")
def my_appointments(db: Session = Depends(get_db), user: User = Depends(require_role("patient"))):
    return [{"id": a.id, "doctor_id": a.doctor_id, "slot_id": a.slot_id, "status": a.status}
            for a in db.scalars(select(Appointment).where(Appointment.patient_id == user.id).order_by(Appointment.id.desc())).all()]


def owned_appointment(db: Session, user: User, appointment_id: int) -> Appointment:
    a = db.get(Appointment, appointment_id)
    if not a or a.patient_id != user.id:
        raise HTTPException(404, "Appointment not found")
    return a


@app.post("/api/v1/appointments/{appointment_id}/cancel")
def cancel(appointment_id: int, db: Session = Depends(get_db), user: User = Depends(require_role("patient"))):
    a = owned_appointment(db, user, appointment_id)
    if a.status != "confirmed":
        raise HTTPException(409, "Appointment cannot be cancelled")
    a.status = "cancelled"
    db.execute(update(Slot).where(Slot.id == a.slot_id).values(is_available=True))
    audit(db, user, "cancel", f"appointment:{a.id}")
    db.commit()
    return {"id": a.id, "status": a.status}


@app.post("/api/v1/appointments/{appointment_id}/reschedule")
def reschedule(appointment_id: int, data: Reschedule, db: Session = Depends(get_db), user: User = Depends(require_role("patient"))):
    a = owned_appointment(db, user, appointment_id)
    slot = db.get(Slot, data.slot_id)
    if a.status != "confirmed" or not slot or slot.doctor_id != a.doctor_id or slot.id == a.slot_id or slot.starts_at <= datetime.now(timezone.utc).replace(tzinfo=None):
        raise HTTPException(409, "Cannot reschedule to that slot")
    if db.execute(update(Slot).where(Slot.id == slot.id, Slot.is_available.is_(True)).values(is_available=False)).rowcount != 1:
        db.rollback()
        raise HTTPException(409, "Slot has already been booked")
    db.execute(update(Slot).where(Slot.id == a.slot_id).values(is_available=True))
    a.slot_id = slot.id
    audit(db, user, "reschedule", f"appointment:{a.id}")
    db.commit()
    return {"id": a.id, "status": a.status, "slot_id": a.slot_id}


@app.post("/api/v1/doctor/appointments/{appointment_id}/complete")
def complete(appointment_id: int, db: Session = Depends(get_db), user: User = Depends(require_role("doctor"))):
    d = own_doctor(db, user)
    a = db.get(Appointment, appointment_id)
    if not a or a.doctor_id != d.id:
        raise HTTPException(404, "Appointment not found")
    if a.status != "confirmed":
        raise HTTPException(409, "Appointment cannot be completed")
    if db.get(Slot, a.slot_id).starts_at > datetime.now(timezone.utc).replace(tzinfo=None):
        raise HTTPException(409, "Appointment is in the future")
    a.status = "completed"
    audit(db, user, "complete", f"appointment:{a.id}")
    db.commit()
    return {"id": a.id, "status": a.status}


@app.post("/api/v1/reviews", status_code=201)
def create_review(data: ReviewCreate, db: Session = Depends(get_db), user: User = Depends(require_role("patient"))):
    a = owned_appointment(db, user, data.appointment_id)
    if a.status != "completed":
        raise HTTPException(409, "Review requires a completed appointment")
    review = Review(appointment_id=a.id, doctor_id=a.doctor_id, patient_id=user.id,
                    rating=data.rating, comment=data.comment)
    db.add(review)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Appointment has already been reviewed")
    return {"id": review.id, "doctor_id": review.doctor_id, "rating": review.rating}


@app.get("/api/v1/doctors/{doctor_id}/reviews")
def doctor_reviews(doctor_id: int, db: Session = Depends(get_db)):
    d = db.get(Doctor, doctor_id)
    if not d or d.verification_status != "verified":
        raise HTTPException(404, "Doctor not found")
    return [{"rating": r.rating, "comment": r.comment}
            for r in db.scalars(select(Review).where(Review.doctor_id == doctor_id).order_by(Review.id.desc()).limit(100)).all()]


@app.get("/api/v1/admin/doctors/pending")
def pending_doctors(db: Session = Depends(get_db), user: User = Depends(require_role("admin"))):
    return [doctor_public(db, d) for d in db.scalars(select(Doctor).where(Doctor.verification_status == "pending")).all()]


@app.post("/api/v1/admin/doctors/{doctor_id}/verification")
def verify_doctor(doctor_id: int, data: VerificationDecision, db: Session = Depends(get_db), user: User = Depends(require_role("admin"))):
    d = db.get(Doctor, doctor_id)
    if not d:
        raise HTTPException(404, "Doctor not found")
    d.verification_status = data.status
    audit(db, user, "verify_doctor", f"doctor:{d.id}:{data.status}")
    db.commit()
    return {"doctor_id": d.id, "verification_status": d.verification_status}


@app.get("/api/v1/doctor/subscription")
def subscription(db: Session = Depends(get_db), user: User = Depends(require_role("doctor"))):
    d = own_doctor(db, user)
    s = db.scalar(select(Subscription).where(Subscription.doctor_id == d.id))
    return {"plan": s.plan if s else "basic", "status": s.status if s else "inactive"}


@app.post("/api/v1/assistant/patient/chat", status_code=501)
def patient_ai(user: User = Depends(require_role("patient"))):
    raise HTTPException(501, "Patient assistant requires a validated specialty routing service")


@app.post("/api/v1/assistant/doctor/case", status_code=501)
def doctor_ai(user: User = Depends(require_role("doctor"))):
    raise HTTPException(501, "Doctor assistant requires a validated medical knowledge base")
