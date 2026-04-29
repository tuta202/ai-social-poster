# PostPilot AI — Backend

FastAPI backend for PostPilot AI.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env  # then fill in your values
uvicorn app.main:app --reload
```

Health check: `GET http://localhost:8000/health`

## Development Notes

### Alembic (Windows)
Run alembic with the project's Python interpreter to avoid PATH issues:
```
python -m alembic upgrade head
python -m alembic revision --autogenerate -m "description"
```

### Default credentials (dev only)
- Username: `admin`
- Password: `postpilot2024`
- Run `python seed.py` to create the default user

### Environment
Copy `.env.example` to `.env` and fill in values before running.
