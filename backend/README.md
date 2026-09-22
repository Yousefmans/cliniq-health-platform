# ClinIQ API

FastAPI backend for the ClinIQ graduation project. The current implementation is an API foundation for local development, with role-based access and relational data.

## Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env       # Windows: copy .env.example .env
```

Set a unique `JWT_SECRET` of at least 32 characters and load the `.env` values into your shell. For example, on Unix: `set -a; source .env; set +a`. Then:

```bash
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for interactive API documentation. SQLite is the default local database. Set `DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/cliniq` to use PostgreSQL.

To create the first platform admin, set `BOOTSTRAP_ADMIN_EMAIL` and `BOOTSTRAP_ADMIN_PASSWORD` in the environment and run `python -m app.bootstrap_admin` once. Public registration only permits patient and doctor roles. Doctors are hidden from public search until an admin verifies them.

## Implemented

- Password hashing with Argon2, short lived JWT access tokens, role checks, and active account checks.
- Doctor profiles, verified doctor search, available appointment slots, booking, cancellation, rescheduling, and completed visit reviews.
- Doctor verification by admins, a read only subscription status, and audit records for sensitive changes.
- Conditional slot updates to prevent two patients from booking the same slot concurrently.

## Remaining integrations

- The website's sample data and buttons are still a UI prototype. Connect the website to these endpoints and add login screens before presenting it as a live service.
- The two assistant endpoints intentionally return HTTP 501. Add separately validated patient routing and medical knowledge services before enabling them.
- Payment processing, document upload and review, notifications, refresh tokens, password reset, migration tooling, and background jobs are not implemented yet.
- For a deployed service, add migrations, HTTPS, rate limiting, monitoring, secure secret storage, and privacy controls for medical information.
