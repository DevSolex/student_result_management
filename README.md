# Student Result Management System

A role-based academic portal API built with **FastAPI**, **MySQL**, and **Docker**. It handles student registration, result submission by lecturers, admin approval workflows, GPA calculation, and more.

---

## Tech Stack

| Layer      | Technology                        |
|------------|-----------------------------------|
| Backend    | Python 3.11, FastAPI              |
| Database   | MySQL 8.0 (via SQLAlchemy/Alembic)|
| Auth       | JWT (access + refresh tokens)     |
| Password   | bcrypt (SHA-256 pre-hash)         |
| Email      | FastAPI-Mail (SMTP)               |
| File Upload| Cloudinary                        |
| Container  | Docker + Docker Compose           |
| DB GUI     | phpMyAdmin                        |

---

## Roles

| Role     | Description                                              |
|----------|----------------------------------------------------------|
| `admin`  | Manages pre-registered students, invites lecturers, approves/rejects results |
| `lecturer` | Submits and bulk-uploads student results               |
| `student`  | Views own results, GPA, transcript                     |

---

## Getting Started

### Prerequisites
- Docker & Docker Compose installed

### 1. Clone the repo
```bash
git clone git@github.com:DevSolex/student_result_management.git
cd student_result_management
```

### 2. Set up environment variables
```bash
cp .env.example .env
# Fill in your values in .env
```

### 3. Start all services
```bash
docker compose up --build -d
```

### 4. Run database migrations
```bash
docker compose exec api alembic upgrade head
```

### 5. Create a super admin
```bash
docker compose exec api python3 -c "
from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.core.security import hash_password
db = SessionLocal()
db.add(User(email='admin@yourdomain.com', hashed_password=hash_password('YourPassword1'), role=UserRole.admin))
db.commit()
print('Admin created')
db.close()
"
```

---

## Services & Ports

| Service    | URL                          |
|------------|------------------------------|
| API        | http://localhost:8001         |
| API Docs   | http://localhost:8001/api/docs|
| phpMyAdmin | http://localhost:8080         |

---

## API Overview

### Auth — `/api/v1/auth`
| Method | Endpoint                    | Access  | Description                        |
|--------|-----------------------------|---------|------------------------------------|
| POST   | `/register/student`         | Public  | Register using pre-registered matric|
| POST   | `/register/lecturer`        | Public  | Register via admin invite token    |
| POST   | `/login`                    | Public  | Login, returns JWT tokens          |
| POST   | `/refresh`                  | Public  | Refresh access token               |
| POST   | `/forgot-password`          | Public  | Request OTP for password reset     |
| POST   | `/reset-password`           | Public  | Reset password with OTP            |
| POST   | `/invite`                   | Admin   | Invite a lecturer by email         |

### Students — `/api/v1/students`
| Method | Endpoint              | Access  | Description                  |
|--------|-----------------------|---------|------------------------------|
| GET    | `/me`                 | Student | Get own profile              |
| PATCH  | `/me`                 | Student | Update own profile           |
| POST   | `/me/avatar`          | Student | Upload profile picture       |
| POST   | `/me/change-password` | Student | Change password              |
| GET    | `/me/results`         | Student | View approved results        |
| GET    | `/me/gpa`             | Student | View GPA/CGPA                |
| GET    | `/me/transcript`      | Student | Full academic transcript     |
| GET    | `/`                   | Admin   | List all students            |
| DELETE | `/{student_id}`       | Admin   | Delete a student             |

### Lecturers — `/api/v1/lecturers`
| Method | Endpoint              | Access  | Description                    |
|--------|-----------------------|---------|--------------------------------|
| GET    | `/me/dashboard`       | Lecturer| Dashboard + recent submissions |
| GET    | `/me/students`        | Lecturer| Students in assigned courses   |
| POST   | `/me/results`         | Lecturer| Submit a single result         |
| POST   | `/me/results/bulk`    | Lecturer| Bulk upload results via CSV    |
| GET    | `/`                   | Admin   | List all lecturers             |
| PATCH  | `/{id}/activate`      | Admin   | Activate/deactivate lecturer   |

### Admin — `/api/v1/admin`
| Method | Endpoint                        | Access | Description                      |
|--------|---------------------------------|--------|----------------------------------|
| GET    | `/dashboard`                    | Admin  | Stats overview                   |
| GET    | `/results/pending`              | Admin  | List pending results             |
| PATCH  | `/results/{id}/review`          | Admin  | Approve or reject a result       |
| GET    | `/pre-registered`               | Admin  | List pre-registered students     |
| POST   | `/pre-registered`               | Admin  | Add student to pre-registered list|
| DELETE | `/pre-registered/{id}`          | Admin  | Remove from pre-registered list  |

---

## Student Registration Flow

```
Admin adds matric → pre_registered_students table
Student visits /register/student → enters email + password + matric
System validates matric against pre_registered_students
  ✓ Found → account created (name & dept pulled from pre-registered record)
  ✗ Not found → 403 Forbidden
```

## Lecturer Onboarding Flow

```
Admin sends invite → POST /auth/invite (email)
Lecturer receives invite token (via email or manually)
Lecturer registers → POST /auth/register/lecturer (with token)
```

## Result Workflow

```
Lecturer submits result → status: pending
Admin reviews → approved / rejected (rejection requires reason)
On approval → GPA/CGPA auto-recalculated for that student
```

## Bulk Result Upload (CSV Format)

```csv
matric_number,course_code,score,academic_year,semester
MAT001,CSC301,75.5,2024/2025,1
MAT002,CSC301,60.0,2024/2025,1
```

---

## Environment Variables

```env
SECRET_KEY=
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

DATABASE_URL=mysql://user:password@db:3306/dbname
MYSQL_ROOT_PASSWORD=
MYSQL_DATABASE=
MYSQL_USER=
MYSQL_PASSWORD=

CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=

MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_FROM=
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com
MAIL_STARTTLS=True
MAIL_SSL_TLS=False

OTP_EXPIRE_MINUTES=10
OTP_MAX_ATTEMPTS=5
```

---

## Project Structure

```
app/
├── core/           # config, database, security
├── models/         # SQLAlchemy models
├── schemas/        # Pydantic schemas
├── routes/         # FastAPI routers
├── services/       # Business logic
└── dependencies/   # Auth guards
alembic/            # DB migrations
```
