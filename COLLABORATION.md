# Collaboration Guide

Welcome to the **Student Result Management System** project. This guide is for every team member — frontend, backend, or any new contributor — to get up and running quickly.

---

## Team Roles

| Stack    | Responsibility                                                  |
|----------|-----------------------------------------------------------------|
| Backend  | FastAPI API, database models, business logic, migrations        |
| Frontend | UI for students, lecturers, and admins consuming the REST API   |

---

## For Frontend Developers

### Base URL
```
http://localhost:8001/api/v1
```
> In production, replace with the deployed API URL.

### Interactive API Docs
The API has auto-generated Swagger docs — use this to explore and test every endpoint before building UI:
```
http://localhost:8001/api/docs
```

### Authentication
The API uses **JWT Bearer tokens**.

1. Call `POST /auth/login` with `{ email, password }`
2. You get back `access_token` and `refresh_token`
3. Attach the access token to every protected request:
   ```
   Authorization: Bearer <access_token>
   ```
4. When the access token expires (30 min), call `POST /auth/refresh` with `{ refresh_token }` to get a new one

### User Roles & What They Can Access

| Role       | Can Access                                                  |
|------------|-------------------------------------------------------------|
| `student`  | Own profile, results, GPA, transcript, change password      |
| `lecturer` | Dashboard, submit results, bulk upload, view own students   |
| `admin`    | Everything — manage students, lecturers, results, pre-reg   |

### Key Flows to Build UI For

#### Student Registration
```
POST /auth/register/student
Body: { email, password, matric_number }
```
- Student must have a matric number pre-registered by admin
- Name and department are auto-filled from the pre-registered record
- Show a clear error if matric is not found (403)

#### Student Login & Dashboard
```
POST /auth/login → get tokens
GET  /students/me → profile
GET  /students/me/results?academic_year=2024/2025&semester=1 → results
GET  /students/me/gpa → { cgpa, semesters: [...] }
GET  /students/me/transcript → full academic record
```

#### Lecturer Login & Dashboard
```
POST /auth/login → get tokens
GET  /lecturers/me/dashboard → { lecturer, recent_submissions }
GET  /lecturers/me/students → students in assigned courses
POST /lecturers/me/results → submit single result
POST /lecturers/me/results/bulk → upload CSV file
```

#### Admin Panel
```
GET   /admin/dashboard → { total_students, pending_results, departments }
GET   /admin/results/pending → list of results awaiting review
PATCH /admin/results/{id}/review → { status: "approved" | "rejected", rejection_reason? }

GET    /admin/pre-registered → list of pre-registered students
POST   /admin/pre-registered → add student { matric_number, first_name, last_name, department_id }
DELETE /admin/pre-registered/{id} → remove student

GET   /students/ → all registered students
DELETE /students/{id} → delete student

GET   /lecturers/ → all lecturers
PATCH /lecturers/{id}/activate?activate=true|false → toggle lecturer status

POST  /auth/invite → invite lecturer by email { email }
```

### Response Shapes (Key Ones)

**Login response:**
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer"
}
```

**Student profile:**
```json
{
  "id": 1,
  "matric_number": "MAT001",
  "first_name": "John",
  "last_name": "Doe",
  "level": 100,
  "department_id": 1
}
```

**Result:**
```json
{
  "id": 1,
  "student_id": 1,
  "course_id": 1,
  "score": 75.5,
  "grade": "A",
  "grade_point": 5.0,
  "academic_year": "2024/2025",
  "semester": 1,
  "status": "pending" | "approved" | "rejected"
}
```

**GPA:**
```json
{
  "cgpa": 4.5,
  "semesters": [
    { "academic_year": "2024/2025", "semester": 1, "gpa": 4.5, "cgpa": 4.5, "total_credit_units": 18 }
  ]
}
```

### Error Handling
All errors follow this shape:
```json
{ "detail": "Human readable error message" }
```

Common HTTP codes:
| Code | Meaning                              |
|------|--------------------------------------|
| 400  | Bad request / validation error       |
| 401  | Not authenticated / token expired    |
| 403  | Forbidden (wrong role or matric not found) |
| 404  | Resource not found                   |
| 409  | Conflict (duplicate email/matric)    |
| 422  | Unprocessable entity (schema error)  |
| 429  | Rate limit exceeded                  |

### File Uploads
- **Avatar:** `POST /students/me/avatar` — multipart form, field name `file`, max 5MB, JPEG/PNG/WebP
- **Bulk results:** `POST /lecturers/me/results/bulk` — multipart form, field name `file`, CSV format

### CSV Format for Bulk Result Upload
```csv
matric_number,course_code,score,academic_year,semester
MAT001,CSC301,75.5,2024/2025,1
MAT002,CSC301,60.0,2024/2025,1
```

---

## For Backend Developers

### Setup
```bash
git clone git@github.com:DevSolex/student_result_management.git
cd student_result_management
cp .env.example .env   # fill in your values
docker compose up --build -d
docker compose exec api alembic upgrade head
```

### Project Structure
```
app/
├── core/
│   ├── config.py       # pydantic-settings (reads .env)
│   ├── database.py     # SQLAlchemy engine + session
│   └── security.py     # bcrypt hashing, JWT creation/decode
├── models/             # SQLAlchemy ORM models
├── schemas/            # Pydantic request/response schemas
├── routes/             # FastAPI routers (auth, student, lecturer, admin)
├── services/           # Business logic (auth, result, gpa, email, cloudinary)
└── dependencies/       # Auth guards (require_admin, require_student, etc.)
alembic/                # DB migrations
```

### Creating a Migration
After changing any model:
```bash
docker compose exec api alembic revision --autogenerate -m "describe your change"
docker compose exec api alembic upgrade head
```

### Adding a New Endpoint
1. Add route in `app/routes/<router>.py`
2. Add business logic in `app/services/`
3. Add schema in `app/schemas/`
4. If new model needed, add in `app/models/` and register in `app/models/__init__.py`
5. Generate and run migration

### Branch Strategy
```
main        → stable, production-ready
dev         → integration branch, all features merge here first
feature/*   → individual feature branches (e.g. feature/course-management)
fix/*       → bug fix branches
```

### Pull Request Rules
- Always branch off `dev`
- PR title must be descriptive
- At least one review before merging to `dev`
- Only `dev` merges into `main` after testing

---

## Environment Variables Reference

| Variable                  | Description                          |
|---------------------------|--------------------------------------|
| `SECRET_KEY`              | JWT signing secret (keep private)    |
| `DATABASE_URL`            | MySQL connection string              |
| `CLOUDINARY_*`            | Cloudinary credentials for avatars   |
| `MAIL_*`                  | SMTP config for OTP/invite emails    |
| `OTP_EXPIRE_MINUTES`      | OTP validity window (default: 10)    |
| `OTP_MAX_ATTEMPTS`        | Max wrong OTP tries (default: 5)     |

---

## Contact

For questions, reach out via the project's GitHub Issues or the team chat.
