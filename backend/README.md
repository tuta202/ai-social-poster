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

## Production (Railway)

See [DEPLOY.md](../DEPLOY.md) for full deployment guide.

Quick start:
1. Set environment variables in Railway dashboard
2. `alembic upgrade head` runs automatically on deploy
3. Run `python seed.py` once to create admin user

### Alembic (reminder)
- Windows dev: `python -m alembic upgrade head`
- Railway/Linux: `alembic upgrade head`

### Generate SECRET_KEY
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
