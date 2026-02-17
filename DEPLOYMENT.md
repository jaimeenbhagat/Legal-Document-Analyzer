# 🚀 Deployment Guide

This guide explains how to deploy the Legal AI Document Analysis System to production.

---

## Architecture Overview

```
┌─────────────────────┐         ┌─────────────────────┐
│   VERCEL            │         │   RENDER/RAILWAY    │
│   (Frontend)        │  ───►   │   (Backend)         │
│   Next.js App       │  API    │   FastAPI + Python  │
│   Port: 443 (HTTPS) │  Calls  │   Port: 443 (HTTPS) │
└─────────────────────┘         └─────────────────────┘
```

Since Vercel only supports Node.js serverless functions, the Python backend must be deployed separately.

---

## Step 1: Deploy Backend (Choose One)

### Option A: Deploy to Render (Recommended - Free Tier)

1. **Create account** at [render.com](https://render.com)

2. **Create New Web Service**
   - Connect your GitHub repository
   - Select the repository

3. **Configure the service:**
   ```
   Name: legal-ai-backend
   Region: Oregon (or closest to you)
   Branch: main
   Root Directory: app
   Runtime: Python 3
   Build Command: pip install -r ../requirements.txt
   Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

4. **Add Environment Variables:**
   ```
   GOOGLE_API_KEY=your_gemini_api_key_here
   ```

5. **Deploy** - Note your URL (e.g., `https://legal-ai-backend.onrender.com`)

### Option B: Deploy to Railway

1. **Create account** at [railway.app](https://railway.app)

2. **Create New Project** → Deploy from GitHub

3. **Configure:**
   ```
   Root Directory: /app
   Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

4. **Add Variables:**
   ```
   GOOGLE_API_KEY=your_gemini_api_key_here
   ```

5. **Deploy** - Note your URL

### Option C: Deploy to Google Cloud Run

```bash
# From the project root
cd app

# Build and deploy
gcloud run deploy legal-ai-backend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_API_KEY=your_key_here
```

---

## Step 2: Deploy Frontend to Vercel

### Method 1: Via Vercel Dashboard (Easiest)

1. **Go to** [vercel.com](https://vercel.com) and sign in

2. **Import Project**
   - Click "Add New" → "Project"
   - Connect your GitHub repository

3. **Configure Project:**
   ```
   Framework Preset: Next.js
   Root Directory: frontend    ← IMPORTANT!
   Build Command: npm run build
   Output Directory: .next
   Install Command: npm install
   ```

4. **Add Environment Variable:**
   ```
   Name: NEXT_PUBLIC_BACKEND_URL
   Value: https://your-backend-url.onrender.com  ← Your backend URL from Step 1
   ```

5. **Click Deploy**

### Method 2: Via Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Navigate to frontend directory
cd frontend

# Deploy
vercel

# Follow prompts:
# - Link to existing project? No
# - Project name: legal-ai-frontend
# - Directory: ./
# - Override settings? No

# Set environment variable
vercel env add NEXT_PUBLIC_BACKEND_URL
# Enter your backend URL when prompted

# Deploy to production
vercel --prod
```

---

## Step 3: Configure CORS on Backend

Update `app/main.py` to allow your Vercel frontend domain:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://your-app.vercel.app",  # Add your Vercel URL
        "https://*.vercel.app",          # Allow all Vercel preview URLs
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Environment Variables Summary

### Backend (Render/Railway)
| Variable | Description |
|----------|-------------|
| `GOOGLE_API_KEY` | Your Google Gemini API key |

### Frontend (Vercel)
| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_BACKEND_URL` | Full URL of your deployed backend (e.g., `https://legal-ai-backend.onrender.com`) |

---

## Troubleshooting

### "API not reachable" error
- Check that `NEXT_PUBLIC_BACKEND_URL` is set correctly in Vercel
- Ensure backend is running (visit the backend URL directly)
- Check CORS settings on backend

### Build fails on Vercel
- Make sure `Root Directory` is set to `frontend`
- Check that all dependencies are in `package.json`

### Backend errors on Render
- Check logs in Render dashboard
- Ensure `GOOGLE_API_KEY` is set
- Verify `requirements.txt` has all dependencies

---

## URLs After Deployment

- **Frontend:** `https://your-app.vercel.app`
- **Backend:** `https://your-backend.onrender.com`
- **API Health Check:** `https://your-backend.onrender.com/health`

---

## Cost Estimates

| Service | Free Tier | Paid |
|---------|-----------|------|
| **Vercel** | 100GB bandwidth/mo | $20/mo |
| **Render** | 750 hrs/mo (sleeps after 15min) | $7/mo |
| **Railway** | $5 credit/mo | Pay as you go |
| **Gemini API** | Free tier available | Pay per token |

---

## Production Checklist

- [ ] Backend deployed and accessible
- [ ] `GOOGLE_API_KEY` set on backend
- [ ] Frontend deployed to Vercel
- [ ] `NEXT_PUBLIC_BACKEND_URL` set on Vercel
- [ ] CORS configured for Vercel domain
- [ ] Test PDF upload works
- [ ] Test chat functionality works
