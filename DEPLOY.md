# PostPilot AI -- Deployment Guide

## Architecture
- **Backend**: FastAPI on Railway (single service)
- **Frontend**: React/Vite on Vercel
- **Database**: PostgreSQL on Railway (add-on)

---

## Backend Deploy (Railway)

### 1. Create Railway project
1. Go to https://railway.app -> New Project
2. Connect your GitHub repo -> select `backend/` as root directory
3. Railway auto-detects Dockerfile

### 2. Add PostgreSQL
1. In Railway project -> **+ New** -> **Database** -> **PostgreSQL**
2. Railway auto-sets `DATABASE_URL` environment variable

### 3. Set environment variables
Go to your service -> **Settings -> Variables**, add:

```
SECRET_KEY          = (generate: python -c "import secrets; print(secrets.token_hex(32))")
OPENAI_API_KEY      = sk-proj-...
FACEBOOK_APP_ID     = your-app-id
FACEBOOK_APP_SECRET = your-app-secret
ALLOWED_ORIGINS     = ["https://your-app.vercel.app"]
```

### 4. Deploy
Railway deploys automatically on git push.
On startup, `alembic upgrade head` runs automatically before uvicorn.

### 5. Seed admin user
After first deploy, open Railway shell:

```bash
python seed.py
```

Default credentials: `admin` / `postpilot2024` -- **change password after first login**.

---

## Frontend Deploy (Vercel)

### 1. Import project
1. Go to https://vercel.com -> Import Git Repository
2. Select your repo -> set **Root Directory** to `frontend/`
3. Framework: Vite (auto-detected)

### 2. Set environment variable
In Vercel project -> **Settings -> Environment Variables**:

```
VITE_API_URL = https://your-backend.railway.app
```

### 3. Deploy
Vercel deploys automatically on git push to main.

---

## Post-deploy Checklist

- [ ] GET https://your-backend.railway.app/health returns `{"status":"ok"}`
- [ ] Frontend loads at https://your-app.vercel.app
- [ ] Login with admin/postpilot2024
- [ ] Navigate to FB Setup -> connect Facebook page
- [ ] Create a test campaign -> confirm -> verify scheduled in Dashboard
- [ ] Wait for scheduler tick (up to 60s) -> verify post appears on Facebook

---

## Updating Admin Password

Railway shell:

```python
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.models import User

db = SessionLocal()
user = db.query(User).filter(User.username == "admin").first()
user.hashed_password = hash_password("your-new-secure-password")
db.commit()
print("Password updated")
```

---

## Monitoring

- Railway dashboard: CPU/memory/logs in real-time
- Scheduler logs: search "APScheduler" or "Posted job_post" in Railway logs
- Failed posts: visible in Dashboard -> job detail panel (red FAILED badge)

---

## Cost Estimate (MVP)

| Service | Cost |
|---------|------|
| Railway Hobby plan | $5/month |
| Railway PostgreSQL | ~$0/month (free tier) |
| Vercel | Free (Hobby plan) |
| OpenAI (GPT-4o text) | ~$0.01/post |
| OpenAI (DALL-E 3 image) | ~$0.04/image |
| **Total infra** | **~$5/month** |

Content costs depend on usage. A 30-post campaign with images is approximately $1.50 in OpenAI costs.
