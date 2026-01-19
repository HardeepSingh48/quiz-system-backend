# Online Quiz System - Production Backend

A production-ready online quiz platform backend built with FastAPI, featuring JWT authentication with token rotation, timed quizzes with server-side validation, automated scoring, real-time leaderboards, and async notifications.

## 🎯 Features

- **JWT Authentication** with secure token rotation
- **Role-Based Access Control (RBAC)** - Admin and User roles
- **Timed Quizzes** with server-side validation
- **Automated Scoring** for MCQ and True/False questions
- **Real-time Leaderboards** using Redis
- **Async Notifications** via Celery
- **Anti-Cheating Measures**:
  - Single active attempt per quiz
  - Question/option randomization
  - Server-side timer enforcement
  - Attempt locking after submission
- **Database Migrations** with Alembic
- **Comprehensive Testing** (Unit + Integration)
- **Docker Support** for easy deployment

## 🏗️ Tech Stack

- **FastAPI** - Modern async web framework
- **PostgreSQL** - Primary database
- **SQLModel** - ORM with Pydantic validation
- **Redis** - Caching, timers, leaderboards
- **Celery** - Background task processing
- **Alembic** - Database migrations
- **Pydantic v2** - Data validation
- **pytest** - Testing framework
- **Docker & Docker Compose** - Containerization

## 📁 Project Structure

```
app/
├── main.py                  # FastAPI application entry point
├── core/
│   ├── config.py           # Application configuration
│   ├── security.py         # JWT & password utilities
│   ├── logging.py          # Logging configuration
│   └── exceptions.py       # Custom exceptions
├── api/v1/
│   ├── deps.py             # Dependency injection
│   └── routers/
│       ├── auth.py         # Authentication endpoints
│       ├── quizzes.py      # Quiz CRUD endpoints
│       ├── attempts.py     # Quiz attempt endpoints
│       ├── results.py      # Results endpoints
│       └── leaderboard.py  # Leaderboard endpoints
├── domain/
│   └── enums.py            # Domain enumerations
├── services/
│   ├── auth_service.py     # Authentication logic
│   ├── quiz_service.py     # Quiz management logic
│   ├── attempt_service.py  # Attempt & timer logic
│   └── scoring_service.py  # Scoring logic
├── repositories/
│   ├── user_repo.py        # User data access
│   ├── quiz_repo.py        # Quiz data access
│   ├── attempt_repo.py     # Attempt data access
│   └── result_repo.py      # Result data access
├── schemas/
│   ├── auth.py             # Auth Pydantic schemas
│   ├── quiz.py             # Quiz Pydantic schemas
│   ├── attempt.py          # Attempt Pydantic schemas
│   └── result.py           # Result Pydantic schemas
├── db/
│   ├── base.py             # Database models
│   ├── session.py          # Database session
│   └── migrations/         # Alembic migrations
├── workers/
│   ├── celery_app.py       # Celery configuration
│   ├── notification_worker.py  # Notification tasks
│   ├── leaderboard_worker.py   # Leaderboard tasks
│   └── attempt_worker.py       # Auto-submit tasks
└── tests/
    ├── conftest.py         # Test fixtures
    ├── unit/               # Unit tests
    └── integration/        # Integration tests
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

### Local Setup

1. **Clone repository**:
```bash
cd Assessment
```

2. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Run database migrations**:
```bash
alembic upgrade head
```

6. **Start the application**:
```bash
uvicorn app.main:app --reload
```

7. **Start Celery worker** (in another terminal):
```bash
celery -A app.workers.celery_app worker --loglevel=info
```

8. **Start Celery beat** (in another terminal):
```bash
celery -A app.workers.celery_app beat --loglevel=info
```

### Docker Setup

1. **Create .env file**:
```bash
cp .env.example .env
```

2. **Start all services**:
```bash
docker-compose up -d
```

3. **Run migrations**:
```bash
docker-compose exec api alembic upgrade head
```

4. **View logs**:
```bash
docker-compose logs -f api
```

## 📚 API Documentation

Once the application is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login (returns access + refresh tokens)
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout (revoke tokens)
- `GET /api/v1/auth/me` - Get current user

#### Quizzes (Admin)
- `POST /api/v1/quizzes` - Create quiz
- `PUT /api/v1/quizzes/{id}` - Update quiz
- `POST /api/v1/quizzes/{id}/publish` - Publish quiz
- `DELETE /api/v1/quizzes/{id}` - Delete quiz

#### Quizzes (User)
- `GET /api/v1/quizzes` - List published quizzes
- `GET /api/v1/quizzes/{id}` - Get quiz details

#### Quiz Attempts
- `POST /api/v1/attempts/quizzes/{id}/start` - Start quiz attempt
- `GET /api/v1/attempts/{id}` - Get attempt status
- `POST /api/v1/attempts/{id}/answers` - Submit answer
- `POST /api/v1/attempts/{id}/submit` - Submit quiz

#### Results
- `GET /api/v1/results/attempts/{id}` - Get result by attempt
- `GET /api/v1/results/my-results` - Get user's all results

#### Leaderboard
- `GET /api/v1/leaderboard/quizzes/{id}` - Quiz leaderboard
- `GET /api/v1/leaderboard/global` - Global leaderboard

## 🔐 Security Features

### JWT Token Rotation
- Access tokens expire in 15 minutes
- Refresh tokens expire in 7 days
- Refresh tokens are one-time use (rotated on refresh)
- Tokens are hashed before storing in database
- All tokens invalidated on logout

### Server-Side Timer Validation
```python
# Quiz expires at calculated time
expires_at = started_at + timedelta(minutes=quiz.duration_minutes)

# Validated on every request
if datetime.utcnow() > attempt.expires_at:
    await auto_submit_attempt(attempt_id)
    raise QuizExpiredException()
```

### Anti-Cheating
- Database constraint ensures single active attempt
- Questions/options randomized per user
- Answers auto-saved (no waiting for final submission)
- Atomic submission with row locking

## ⚙️ Configuration

Key environment variables in `.env`:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/db

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=your-secret-key-min-32-chars
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Email (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## 🧪 Testing

Run all tests:
```bash
pytest app/tests/ -v
```

Run with coverage:
```bash
pytest app/tests/ --cov=app --cov-report=html
```

Run specific test file:
```bash
pytest app/tests/integration/test_auth_flow.py -v
```

## 📊 Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback one migration:
```bash
alembic downgrade -1
```

View migration history:
```bash
alembic history
```

## 🔄 Background Tasks

### Celery Workers
- **Notification Worker**: Sends emails for quiz published, results available
- **Leaderboard Worker**: Updates Redis and syncs to DB every 5 minutes
- **Attempt Worker**: Auto-submits expired quizzes every minute

### Celery Beat Schedule
```python
{
    "sync-leaderboard-every-5-minutes": {
        "task": "sync_leaderboard_to_db",
        "schedule": 300.0,  # 5 minutes
    },
    "auto-submit-expired-attempts-every-minute": {
        "task": "auto_submit_expired_attempts",
        "schedule": 60.0,  # 1 minute
    },
}
```

## 🏭 Production Deployment

### Pre-deployment Checklist
- [ ] Set strong `SECRET_KEY` (min 32 characters)
- [ ] Use production database (PostgreSQL)
- [ ] Set `DB_ECHO=False`
- [ ] Configure SMTP for emails
- [ ] Set `ENVIRONMENT=production`
- [ ] Use proper CORS origins
- [ ] Enable HTTPS
- [ ] Set up Redis persistence
- [ ] Configure Celery monitoring (Flower)

### Docker Production
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## 📝 Architecture Highlights

### Clean Architecture
- **Domain Layer**: Pure business logic
- **Repository Layer**: Data access abstraction
- **Service Layer**: Business orchestration
- **API Layer**: HTTP concerns

### Dependency Injection
All services use FastAPI's DI system for testability:
```python
async def create_quiz(
    quiz_data: QuizCreate,
    current_admin: User = Depends(require_admin),
    quiz_service: QuizService = Depends(get_quiz_service)
):
    ...
```

### Atomic Operations
Critical operations use database transactions:
```python
async with db.begin():
    attempt = await repo.get_for_update(id)  # Lock row
    score = await scoring_service.calculate(id)
    result = await result_repo.create(...)
    attempt.is_submitted = True
    # Either all succeed or all rollback
```

## 🤝 Contributing

This is a technical assessment project. For production use:
1. Add comprehensive logging
2. Implement Redis for leaderboard caching
3. Add rate limiting
4. Implement email sending
5. Add monitoring (Prometheus, Grafana)
6. Set up CI/CD pipeline

## 📄 License

This project is created as a technical assessment.

## 👨‍💻 Author

Built with ❤️ using FastAPI and modern Python async patterns.

---

**Note**: This is a production-grade backend demonstrating best practices in:
- Security (JWT rotation, RBAC)
- Scalability (async operations, Celery, Redis)
- Code Quality (type hints, clean architecture)
- Testing (unit + integration tests)
- Documentation (comprehensive README)
