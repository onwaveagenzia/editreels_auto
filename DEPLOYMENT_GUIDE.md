# 🚀 ONWAVE Video Processing - Complete Deployment Guide

## 📋 Table of Contents
1. [GitHub Repository Setup](#github-repository-setup)
2. [Vercel Dashboard Deployment](#vercel-dashboard-deployment)
3. [API Server Deployment](#api-server-deployment)
4. [Google Drive Setup](#google-drive-setup)
5. [Environment Configuration](#environment-configuration)
6. [Monitoring & Support](#monitoring--support)

---

## GitHub Repository Setup

### 1. Create GitHub Repository

```bash
# Initialize git
git init
git add .
git commit -m "🎬 ONWAVE Video Processing Platform v1.0"

# Add remote
git remote add origin https://github.com/onwave/video-processing.git

# Push to main
git branch -M main
git push -u origin main
```

### 2. GitHub Secrets (for CI/CD)

Settings → Secrets and Variables → Actions

**Required secrets:**

```
VERCEL_TOKEN          = [from Vercel dashboard]
VERCEL_ORG_ID         = [from Vercel dashboard]
VERCEL_PROJECT_ID     = [from Vercel dashboard]
GOOGLE_CREDENTIALS    = [base64 encoded JSON]
API_SECRET_KEY        = [generate random string]
```

### 3. Branch Protection

Settings → Branches → Add rule

- Branch name pattern: `main`
- Require pull request reviews: ✓
- Require status checks to pass: ✓

---

## Vercel Dashboard Deployment

### 1. Connect Vercel to GitHub

```bash
# Visit: https://vercel.com/new
# → Import Git Repository
# → Select onwave/video-processing
# → Authorize GitHub
```

### 2. Configure Vercel Project

**Project Settings:**

```
Framework Preset: Next.js
Build Command: npm run build
Install Command: npm install
Output Directory: .next
Development Command: npm run dev
Node.js Version: 18.x
```

**Root Directory:**
```
./dashboard
```

### 3. Environment Variables

Vercel Dashboard → Settings → Environment Variables

```
NEXT_PUBLIC_API_URL = https://api.onwave.studio
```

### 4. Deploy

```bash
# First deployment
vercel --prod

# Or automatic via git push to main
```

**Result:**
```
✓ Deployed to: https://video-processing.vercel.app
✓ Production URL: https://onwave-video.vercel.app
```

---

## API Server Deployment

### Option A: Heroku

```bash
# 1. Install Heroku CLI
curl https://cli.heroku.com/install.sh | sh

# 2. Create app
heroku login
heroku create onwave-video-api

# 3. Set Python version
echo "python-3.11.0" > runtime.txt

# 4. Create Procfile
echo "web: gunicorn api.server:app" > Procfile

# 5. Add Procfile to git
git add Procfile runtime.txt
git commit -m "Add Procfile for Heroku"

# 6. Deploy
git push heroku main

# 7. Check logs
heroku logs --tail
```

**Heroku Config:**
```bash
heroku config:set FLASK_ENV=production
heroku config:set API_SECRET_KEY=your_secret_key
heroku config:set ELEVENLABS_API_KEY=sk_...
```

### Option B: Railway

```bash
# 1. Install Railway CLI
npm i -g @railway/cli

# 2. Login
railway login

# 3. Create project
railway init

# 4. Deploy
railway up

# 5. Get URL
railway status
```

### Option C: DigitalOcean App Platform

```bash
# 1. Connect GitHub
# https://cloud.digitalocean.com/apps

# 2. Select repository
# → onwave/video-processing

# 3. Configure
# → Python
# → python api/server.py
# → Port 5000

# 4. Deploy
```

**Result:**
```
✓ API running at: https://api.onwave.studio
```

---

## Google Drive Setup

### 1. Google Cloud Console

```
1. Go to: https://console.cloud.google.com/
2. Create new project: "ONWAVE Video Processing"
3. Enable APIs:
   - Google Drive API
   - Google Photos Library API
4. Create OAuth 2.0 credentials:
   - Application type: Desktop app
   - Download JSON credentials
5. Save as: ~/.onwave/google_credentials.json
```

### 2. Initialize Drive Sync

```bash
# First time setup
npm run drive:setup

# Follow prompts:
# → Authenticate with Google
# → Create input/output folders
# → Save folder IDs
```

### 3. Test Connection

```bash
# List folders
python scripts/google_drive_sync.py --list

# Watch for new videos
npm run drive:watch
```

---

## Environment Configuration

### Create `.env` file

```bash
# API Configuration
FLASK_ENV=production
FLASK_DEBUG=False
API_SECRET_KEY=your-super-secret-key-here-32-chars-min

# Google Drive
GOOGLE_DRIVE_ENABLED=true
GOOGLE_DRIVE_INPUT_FOLDER_ID=1a2b3c4d5e6f7g8h9i0j
GOOGLE_DRIVE_OUTPUT_FOLDER_ID=2b3c4d5e6f7g8h9i0j1k

# ElevenLabs
ELEVENLABS_API_KEY=YOUR_ELEVENLABS_API_KEY

# Processing
MAX_VIDEO_SIZE_MB=5000
MAX_QUEUE_LENGTH=100
PROCESSING_TIMEOUT_MINUTES=60
OUTPUT_RETENTION_DAYS=30

# API
API_HOST=0.0.0.0
API_PORT=5000
CORS_ORIGINS=*

# Dashboard
NEXT_PUBLIC_API_URL=https://api.onwave.studio
NEXT_PUBLIC_APP_ENV=production
```

### For Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 5000

# Run API
CMD ["python", "api/server.py"]
```

```bash
# Build & run
docker build -t onwave-video-api .
docker run -p 5000:5000 -e FLASK_ENV=production onwave-video-api
```

---

## Monitoring & Support

### Health Check

```bash
# API health
curl https://api.onwave.studio/api/health

# Dashboard
https://video-processing.vercel.app
```

### Logging

**API Logs:**
```bash
# Heroku
heroku logs --tail

# DigitalOcean
doctl apps logs <app-id>

# Local
tail -f ~/.onwave/logs.txt
```

**Dashboard Logs:**
```bash
# Vercel
vercel logs
```

### Error Monitoring

**Setup Sentry:**
```python
# api/server.py
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FlaskIntegration()]
)
```

---

## Performance Optimization

### Caching

```bash
# CDN for dashboard assets
# → Vercel handles automatically

# API rate limiting
# → Implement in Flask middleware
```

### Database (optional)

For persistent job storage:

```bash
# PostgreSQL on Heroku
heroku addons:create heroku-postgresql:hobby-dev

# Or: Supabase
# → https://supabase.com
```

---

## Troubleshooting

### Dashboard not connecting to API

```bash
# Check CORS
# → API must have CORS_ORIGINS set correctly

# Check environment variable
# → NEXT_PUBLIC_API_URL must be set in Vercel

# Test API
curl -H "Origin: https://video-processing.vercel.app" \
  -H "Access-Control-Request-Method: GET" \
  https://api.onwave.studio/api/health
```

### Processing jobs failing

```bash
# Check FFmpeg installed
ffmpeg -version

# Check disk space
df -h

# Check logs
npm run dev:api  # Watch real-time logs
```

### Google Drive sync not working

```bash
# Re-authenticate
npm run drive:setup

# Check folder IDs
python scripts/google_drive_sync.py --list

# Test upload
python scripts/google_drive_sync.py --test-upload /path/to/video.mp4
```

---

## Cost Estimation

| Service | Usage | Monthly Cost |
|---------|-------|--------------|
| Vercel | Dashboard hosting | Free |
| Heroku | API server (2x Dyno) | $50 |
| Google Drive | Storage | Free (15GB) or $2 (100GB) |
| ElevenLabs | 10k words/month | $9 |
| **Total** | - | **$59-61** |

---

## Rollback

### Quick Rollback

```bash
# Vercel
vercel rollback

# Heroku
heroku releases
heroku rollback v123
```

---

## Next Steps

1. ✅ Deploy dashboard to Vercel
2. ✅ Deploy API to Heroku/Railway
3. ✅ Setup Google Drive integration
4. ✅ Configure monitoring
5. 🎯 Launch beta testing
6. 📊 Monitor metrics
7. 🔄 Iterate based on feedback

---

**Support & Questions?**
- Docs: https://docs.onwave.studio
- Email: deploy@onwave.studio
- GitHub Issues: https://github.com/onwave/video-processing/issues
