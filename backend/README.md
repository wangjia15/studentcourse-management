# Chinese University Grade Management System Backend

FastAPI-based backend API for managing university grades, courses, and users.

## Features

- FastAPI with automatic OpenAPI documentation
- SQLAlchemy ORM with SQLite database
- JWT authentication and authorization
- Pydantic data validation
- Alembic database migrations
- CORS support for frontend integration
- Comprehensive logging and audit trails

## Setup

### Prerequisites

- Python 3.11+
- UV package manager

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd studentcourse/backend
```

2. Install dependencies:
```bash
make install
# or
uv sync
```

3. Copy environment file:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Initialize database:
```bash
make db-init
# or
uv run alembic upgrade head
```

## Development

### Running the Server

```bash
make run
# or
uv run uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

API Documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Code Quality

Run linting:
```bash
make lint
```

Format code:
```bash
make format
```

Run tests:
```bash
make test
```

### Database Migrations

Create a new migration:
```bash
make migration
```

Apply migrations:
```bash
make migrate
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Get current user

### Users
- `GET /api/v1/users` - List users
- `POST /api/v1/users` - Create user
- `GET /api/v1/users/{id}` - Get user
- `PUT /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Delete user

### Courses
- `GET /api/v1/courses` - List courses
- `POST /api/v1/courses` - Create course
- `GET /api/v1/courses/{id}` - Get course
- `PUT /api/v1/courses/{id}` - Update course
- `DELETE /api/v1/courses/{id}` - Delete course

### Grades
- `GET /api/v1/grades` - List grades
- `POST /api/v1/grades` - Create grade
- `GET /api/v1/grades/{id}` - Get grade
- `PUT /api/v1/grades/{id}` - Update grade
- `DELETE /api/v1/grades/{id}` - Delete grade

## Configuration

Environment variables are configured in `.env`:

- `SECRET_KEY` - JWT secret key
- `DATABASE_URL` - Database connection string
- `ALLOWED_HOSTS` - CORS allowed origins
- `ADMIN_EMAIL` - Default admin email
- `ADMIN_PASSWORD` - Default admin password

## Project Structure

```
backend/
├── app/
│   ├── api/           # API routes
│   ├── core/          # Configuration and security
│   ├── db/            # Database setup
│   ├── models/        # SQLAlchemy models
│   ├── schemas/       # Pydantic schemas
│   └── services/      # Business logic
├── alembic/           # Database migrations
├── tests/             # Test files
├── main.py           # FastAPI application
├── pyproject.toml    # Project configuration
└── .env              # Environment variables
```

## License

MIT License
