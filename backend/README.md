# PostPilot AI — Backend

FastAPI backend for PostPilot AI.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env  # then fill in your values
uvicorn app.main:app --reload
```

Health check: `GET http://localhost:8000/health`
