# 🚀 SentXStock Deployment Guide

Complete step-by-step guide to deploy SentXStock website to production.

---

## 📋 Deployment Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    PRODUCTION ARCHITECTURE                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Frontend (React)          Backend (Flask)                 │
│  ├─ Vercel               ├─ Render.com                     │
│  ├─ Netlify              ├─ Railway                        │
│  └─ GitHub Pages         └─ AWS EC2                        │
│                                                             │
│         ↓ HTTPS ↓                                          │
│                                                             │
│  Database (if needed)      Environment Variables           │
│  ├─ MongoDB              ├─ API Keys (.env)               │
│  ├─ PostgreSQL           ├─ Database URLs                 │
│  └─ Firebase             └─ Secrets                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 RECOMMENDED DEPLOYMENT STACK

| Component | Service | Cost | Ease |
|---|---|---|---|
| **Frontend** | **Vercel** | Free | ⭐⭐⭐⭐⭐ |
| **Backend** | **Render** | Free tier available | ⭐⭐⭐⭐ |
| **Domain** | **Namecheap/GoDaddy** | $10-15/year | ⭐⭐⭐ |

---

# PART 1️⃣ : DEPLOY FRONTEND (React) TO VERCEL

## Step 1: Create Vercel Account

1. Go to [vercel.com](https://vercel.com)
2. Click **"Sign Up"** → Use GitHub account
3. Authorize Vercel to access your GitHub repos
4. ✅ Account created

---

## Step 2: Deploy Frontend

1. **In Vercel Dashboard**, click **"New Project"**
2. **Import your GitHub repo:**
   - Select: `RajendharAre/SentXStock`
   - Click **"Import"**
3. **Configure Project:**
   - Framework Preset: **Next.js** (or Vite - let Vercel auto-detect)
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`

4. **Environment Variables** (if needed):
   - Go to **Settings** → **Environment Variables**
   - Add any `.env` variables needed for frontend
   - Example: `VITE_API_URL=https://your-backend.com`

5. **Click "Deploy"**
   - ⏳ Vercel builds and deploys (~2-3 minutes)
   - ✅ Get your live URL: `https://sentxstock-frontend.vercel.app`

---

## Step 3: Verify Frontend Deployment

```bash
# Test your deployed frontend
https://sentxstock-frontend.vercel.app
```

✅ You should see the SentXStock homepage with working pages!

---

# PART 2️⃣ : DEPLOY BACKEND (Flask) TO RENDER

## Step 1: Prepare Backend for Production

### 1.1 Create `requirements.txt` (if not already done)

```bash
cd C:\Users\Bhanu\SentXStock
pip freeze > requirements.txt
```

This file should already exist with all Python dependencies.

### 1.2 Create `render.yaml` (Configuration file)

Create file: `render.yaml` in root directory:

```yaml
services:
  - type: web
    name: sentxstock-api
    env: python311
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn server:app
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: GEMINI_API_KEYS
        fromBuild: true
      - key: FINNHUB_API_KEY
        fromBuild: true
      - key: NEWSAPI_KEY
        fromBuild: true
```

### 1.3 Update `server.py` for Production

Edit `server.py` and change:

```python
# ❌ BEFORE
if __name__ == '__main__':
    app.run(debug=True, port=5000)

# ✅ AFTER
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
```

Add at top of `server.py`:
```python
import os
```

### 1.4 Create `Procfile` (for Render/Heroku)

Create file: `Procfile` in root directory:

```
web: gunicorn server:app
```

### 1.5 Install Gunicorn

```bash
pip install gunicorn
pip freeze > requirements.txt
```

---

## Step 2: Create Render Account

1. Go to [render.com](https://render.com)
2. Click **"Sign Up"** → Use GitHub
3. Connect your GitHub account
4. ✅ Account created

---

## Step 3: Deploy Backend to Render

1. **In Render Dashboard**, click **"New"** → **"Web Service"**
2. **Connect GitHub:**
   - Select your `SentXStock` repository
   - Click **"Connect"**
3. **Configure Service:**
   - Name: `sentxstock-api`
   - Environment: **Python 3**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn server:app`
   - Plan: **Free** (sufficient for testing)

4. **Add Environment Variables:**
   - Click **"Environment"** → **"Add Environment Variable"**
   - Add each variable:
     ```
     GEMINI_API_KEYS = your_gemini_keys_here
     FINNHUB_API_KEY = your_finnhub_key_here
     NEWSAPI_KEY = your_newsapi_key_here
     ```

5. **Click "Create Web Service"**
   - ⏳ Render builds and deploys (~5-10 minutes)
   - ✅ Get your live URL: `https://sentxstock-api.onrender.com`

---

## Step 4: Verify Backend Deployment

```bash
# Test your deployed backend
https://sentxstock-api.onrender.com/health

# Or test an API endpoint
https://sentxstock-api.onrender.com/api/sentiment
```

✅ You should get a JSON response!

---

# PART 3️⃣ : CONNECT FRONTEND ↔ BACKEND

## Step 1: Update Frontend API URL

Edit: `frontend/src/services/api.js`

```javascript

// ✅ AFTER
const API_URL = process.env.VITE_API_URL || 'https://sentxstock-api.onrender.com';
```

## Step 2: Add Environment Variable in Vercel

1. Go to **Vercel Dashboard** → Your project → **Settings**
2. Go to **Environment Variables**
3. Add:
   - Key: `VITE_API_URL`
   - Value: `https://sentxstock-api.onrender.com`
4. **Redeploy** frontend

```bash
git add .
git commit -m "update: configure API URL for production"
git push origin main
```

---

# PART 4️⃣ : CONFIGURE CUSTOM DOMAIN (Optional)

## Step 1: Buy Domain

1. Go to [Namecheap.com](https://namecheap.com) or [GoDaddy.com](https://godaddy.com)
2. Search for your domain (e.g., `sentxstock.com`)
3. Buy for 1 year (~$10-15)
4. ✅ Domain purchased

---

## Step 2: Add Domain to Vercel

1. **Vercel Dashboard** → Your project → **Settings** → **Domains**
2. Click **"Add Domain"**
3. Enter: `sentxstock.com`
4. Vercel will show **DNS records** to add to your domain registrar

---

## Step 3: Update DNS Settings

1. Go to your **Namecheap/GoDaddy account**
2. Find **DNS Settings** for your domain
3. Add the **CNAME records** provided by Vercel
4. Wait 24-48 hours for DNS propagation
5. ✅ Your domain should now point to Vercel!

---

# PART 5️⃣ : FINAL CHECKS & LAUNCH

## Checklist Before Going Live

```
Frontend (Vercel):
  ✅ Homepage displays correctly
  ✅ Navigation works
  ✅ GIFs load properly
  ✅ All pages accessible
  ✅ Mobile responsive

Backend (Render):
  ✅ API endpoints responding
  ✅ Environment variables set
  ✅ Database connections working
  ✅ Error handling in place

Connection:
  ✅ Frontend calls backend API
  ✅ Sentiment analysis works
  ✅ Portfolio data loads
  ✅ Chat functionality works

Domain:
  ✅ Custom domain resolves
  ✅ SSL/HTTPS working
  ✅ Redirects configured
```

---

## Terminal Commands Summary

```bash
# 1. Commit all changes
git add .
git commit -m "chore: prepare for production deployment"
git push origin main

# 2. Verify Vercel auto-deployed
# Check: https://sentxstock-frontend.vercel.app

# 3. Verify Render deployment
# Check: https://sentxstock-api.onrender.com/health

# 4. Test API connection
curl https://sentxstock-api.onrender.com/api/sentiment
```

---

## 🎉 DEPLOYMENT COMPLETE!

Your SentXStock website is now **LIVE** on the internet!

| What | Where |
|---|---|
| **Website** | `https://sentxstock.com` (custom domain) or `https://sentxstock-frontend.vercel.app` |
| **API Backend** | `https://sentxstock-api.onrender.com` |
| **GitHub** | `https://github.com/RajendharAre/SentXStock` |

---

## 📊 Monitoring & Maintenance

### View Logs

**Vercel Frontend:**
- Dashboard → Your project → **Deployments** → View logs

**Render Backend:**
- Dashboard → Your service → **Logs** tab

### Auto-Deploy on Push

Both Vercel and Render automatically redeploy when you push to `main` branch!

```bash
# Just push code and they auto-update
git add .
git commit -m "fix: bug in sentiment analysis"
git push origin main
```

---

## 🆘 Troubleshooting

| Issue | Solution |
|---|---|
| **Frontend won't load** | Check Vercel logs, ensure `npm run build` succeeds locally |
| **Backend 502 error** | Check Render logs, verify `requirements.txt` and Python version |
| **API calls failing** | Check CORS settings in `server.py`, verify environment variables |
| **GIFs not loading** | Verify `/assests/gifs/` path is correct, check public folder permissions |
| **Domain not resolving** | Wait 24-48 hours for DNS propagation, check DNS records |

---

## 💡 Next Steps

1. ✅ Monitor application for 24-48 hours
2. ✅ Gather user feedback
3. ✅ Fix any bugs discovered
4. ✅ Plan future features
5. ✅ Celebrate! 🎊

---

**Deployment Guide by:** GitHub Copilot  
**Last Updated:** 2026-06-10  
**Status:** Ready for Production ✅
