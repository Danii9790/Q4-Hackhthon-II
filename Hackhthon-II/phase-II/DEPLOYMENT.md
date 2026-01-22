# Deployment Guide for Fullstack Todo App

This guide shows you how to deploy your fullstack application to production.

---

## 📦 Architecture Overview

- **Frontend**: Next.js 16 → Deployed on **Vercel**
- **Backend**: FastAPI → Deployed on **Render** (or Railway/Fly.io)
- **Database**: Neon PostgreSQL (already serverless)

---

## 🚀 Part 1: Deploy Frontend to Vercel

### Step 1: Install Vercel CLI
```bash
npm install -g vercel
```

### Step 2: Login to Vercel
```bash
cd frontend
vercel login
```
- This will open a browser window
- Login with your GitHub account (or create one)
- Authorize Vercel

### Step 3: Deploy Frontend
```bash
cd /home/xdev/Hackhthon-II/phase-II/frontend
vercel
```

**Follow the prompts:**
- **Set up and deploy?** → `Y`
- **Which scope?** → Select your account
- **Link to existing project?** → `N`
- **What's your project's name?** → `todo-app` (or any name)
- **In which directory is your code located?** → `./`
- **Want to override settings?** → `N`

Vercel will:
1. Detect Next.js automatically
2. Build your project
3. Deploy to: `https://todo-app-xyz.vercel.app`

### Step 4: Add Environment Variables
Go to your Vercel dashboard or run:
```bash
vercel env add NEXT_PUBLIC_API_URL production
```
**Value** (we'll get this from Part 2):
```
https://your-backend-url.onrender.com
```

### Step 5: Redeploy with Environment Variables
```bash
vercel --prod
```

**Your frontend URL:** `https://todo-app-xyz.vercel.app`

---

## 🔧 Part 2: Deploy Backend to Render

Render provides free hosting for Python web apps with PostgreSQL.

### Step 1: Create render.yaml

Create `/home/xdev/Hackhthon-II/phase-II/backend/render.yaml`:

```yaml
services:
  - type: web
    name: todo-api
    env: python
    region: oregon
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn src.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.12
      - key: DATABASE_URL
        sync: false
      - key: BETTER_AUTH_SECRET
        generate: true
```

### Step 2: Push Backend Code to GitHub (if not already done)
```bash
cd /home/xdev/Hackhthon-II/phase-II
git add backend/
git commit -m "Add backend deployment config"
git push origin 001-fullstack-web-app
```

### Step 3: Deploy on Render

1. Go to **https://render.com**
2. Sign up/login (use GitHub for easy setup)
3. Click **"New +"** → **"Web Service"**
4. Connect your GitHub repository
5. Select: `Danii9790/Q4-Hackhthon-II`
6. Branch: `001-fullstack-web-app`
7. Root directory: `backend`
8. Configure:
   - **Name**: `todo-api`
   - **Region**: `Oregon (US West)`
   - **Plan**: **Free**
   - **Build Command**: `pip install -r requirements.txt && python scripts/init_db.py`
   - **Start Command**: `uvicorn src.main:app --host 0.0.0.0 --port $PORT`

### Step 4: Add Environment Variables on Render

In your Render dashboard, add these environment variables:

```bash
DATABASE_URL=postgresql://neondb_owner:npg_YyJMvo0jbU6W@ep-fragrant-grass-aeghurw1-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require
BETTER_AUTH_SECRET=9mvjhoOonzTQ0Oe6On7MKKJ0x4wRksd8
```

### Step 5: Deploy

Click **"Create Web Service"** and Render will:
1. Build your FastAPI app
2. Run database initialization
3. Start the server
4. Provide a URL like: `https://todo-api.onrender.com`

### Step 6: Test Backend API
```bash
# Test health endpoint
curl https://todo-api.onrender.com/health

# Test signup
curl -X POST https://todo-api.onrender.com/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123","name":"Test"}'
```

---

## 🔗 Part 3: Connect Frontend to Backend

### Step 1: Get Your Backend URL
After Render deployment, you'll get a URL like:
```
https://todo-api.onrender.com
```

### Step 2: Update Frontend Environment

**Via Vercel CLI:**
```bash
cd frontend
vercel env rm NEXT_PUBLIC_API_URL production
vercel env add NEXT_PUBLIC_API_URL production
# Paste your Render backend URL
```

**Via Vercel Dashboard:**
1. Go to https://vercel.com/dashboard
2. Select your project
3. Go to **Settings** → **Environment Variables**
4. Update `NEXT_PUBLIC_API_URL` to your Render URL

### Step 3: Redeploy Frontend
```bash
vercel --prod
```

---

## ✅ Part 4: Test Full Application

1. Visit your frontend URL (e.g., `https://todo-app.vercel.app`)
2. Try to sign up with a new account
3. Create a task
4. Verify everything works

---

## 📊 Deployment Architecture (Production)

```
┌─────────────────────────┐
│   Vercel (Frontend)     │
│  https://todo.app.com   │
│   - Next.js 16          │
│   - Static Files        │
│   - Serverless Functions│
└───────────┬─────────────┘
            │
            │ API Requests
            ▼
┌─────────────────────────┐
│   Render (Backend)      │
│  https://todo-api.app   │
│   - FastAPI             │
│   - Python 3.12         │
│   - JWT Auth            │
└───────────┬─────────────┘
            │
            │ SQL Queries
            ▼
┌─────────────────────────┐
│   Neon (Database)       │
│  - PostgreSQL           │
│   - Serverless          │
│   - Auto-scaling        │
└─────────────────────────┘
```

---

## 🎯 Quick Deploy Commands Reference

### Frontend (Vercel)
```bash
# One-time setup
npm install -g vercel
vercel login

# Deploy
cd frontend
vercel              # Preview deployment
vercel --prod       # Production deployment
```

### Backend (Render)
- Deploy via GitHub integration on render.com
- Automatic deployments on push to main branch

---

## 🛠️ Alternative Backend Deployments

### Option 1: Railway.app
1. Go to https://railway.app
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repo
4. Railway will auto-detect Python
5. Add environment variables
6. Deploy!

### Option 2: Fly.io
```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Login
flyctl auth login

# Deploy
cd backend
flyctl launch
flyctl deploy
```

### Option 3: Heroku
```bash
# Install Heroku CLI
npm install -g heroku

# Login
heroku login

# Create app
heroku create todo-api

# Deploy
git push heroku 001-fullstack-web-app:main
```

---

## 📝 Environment Variables Checklist

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=https://your-backend-url.onrender.com
```

### Backend (.env)
```bash
DATABASE_URL=postgresql://...
BETTER_AUTH_SECRET=your-secret-key
```

---

## 🔍 Troubleshooting

### Frontend Issues

**Problem**: API calls failing
```bash
# Check browser console for CORS errors
# Verify NEXT_PUBLIC_API_URL is correct
```

**Problem**: Build fails on Vercel
```bash
# Check build logs in Vercel dashboard
# Ensure all dependencies are in package.json
```

### Backend Issues

**Problem**: Database connection fails
```bash
# Verify DATABASE_URL is correct
# Check Neon dashboard for connection issues
```

**Problem**: Health check failing
```bash
curl https://your-backend.onrender.com/health
# Should return: {"status":"healthy"}
```

---

## 📚 Useful Links

- **Vercel Docs**: https://vercel.com/docs
- **Render Docs**: https://render.com/docs
- **Neon Docs**: https://neon.tech/docs
- **Next.js Deployment**: https://nextjs.org/docs/deployment

---

## 🎉 Next Steps

After deployment:

1. ✅ Set up custom domain (optional)
2. ✅ Enable SSL certificates (automatic on Vercel/Render)
3. ✅ Set up monitoring (Vercel Analytics, Render Metrics)
4. ✅ Configure error tracking (Sentry)
5. ✅ Add CI/CD pipeline

---

**Need help?** Check the logs in your Vercel and Render dashboards!
