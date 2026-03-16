# Deployment Runbook - ChatApp

## Table of Contents

1. [Scope](#1-scope)
2. [Prerequisites](#2-prerequisites)
3. [Environment Variables](#3-environment-variables)
4. [Local Verification Before Deploy](#4-local-verification-before-deploy)
5. [Production Deployment](#5-production-deployment)
   - 5.1 MongoDB Atlas
   - 5.2 Backend on Render
   - 5.3 Frontend on GitHub Pages
6. [Post-Deployment Validation](#6-post-deployment-validation)
7. [Operations: Update, Rollback, and Rotation](#7-operations-update-rollback-and-rotation)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Scope

This document is an end-to-end deployment runbook for this repository:

- Frontend: Angular app in frontend/
- Backend: FastAPI app in backend/
- Database: MongoDB Atlas
- Target hosting: Render (backend) + GitHub Pages (frontend)

Use this order every time:

1. Provision Atlas
2. Deploy backend to Render
3. Configure frontend to call backend
4. Deploy frontend to GitHub Pages
5. Run smoke tests

---

## 2. Prerequisites

### 2.1 Accounts and access

1. GitHub account with permission to push this repository.
2. Render account with ability to create a Web Service.
3. MongoDB Atlas account with ability to create an M0 cluster.

### 2.2 Local tooling

| Tool | Minimum version | Check command |
|------|-----------------|---------------|
| Python | 3.11 | python --version |
| Node.js | 18 LTS | node --version |
| npm | 9 | npm --version |
| Angular CLI | 19 | ng version |
| Git | any modern | git --version |

If Angular CLI is missing:

```powershell
npm install -g @angular/cli
```

### 2.3 Repository readiness

1. Confirm both folders exist: backend/ and frontend/.
2. Confirm backend dependencies file exists: backend/requirements.txt.
3. Confirm frontend build works locally at least once before cloud deploy.

---

## 3. Environment Variables

### 3.1 Backend local file

Create backend/.env locally and do not commit it.

```env
MONGODB_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/thechat?retryWrites=true&w=majority
JWT_SECRET=<random-64-hex-or-long-random-string>
CORS_ORIGINS=https://<your-github-username>.github.io
```

Generate JWT_SECRET with Python:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3.2 Render environment variables

Set the same values in Render service settings:

1. MONGODB_URI
2. JWT_SECRET
3. CORS_ORIGINS

Notes:

- CORS_ORIGINS supports comma-separated origins.
- If your Pages site path includes a project segment, origin is still only protocol + host.

Example valid origin:

```text
https://myuser.github.io
```

---

## 4. Local Verification Before Deploy

### 4.1 Start backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Verify:

1. Open http://localhost:8000/health and expect {"status":"ok"}.
2. Open http://localhost:8000/docs and verify routes are listed.

### 4.2 Start frontend

In another terminal:

```powershell
cd frontend
npm install
npm start
```

Verify:

1. App loads at http://localhost:4200.
2. Login/Register actions hit /api routes successfully.
3. Messages appear in real time between two browser sessions.

### 4.3 Production build sanity check

```powershell
cd frontend
ng build --configuration production
```

Fix all build errors before cloud deployment.

---

## 5. Production Deployment

## 5.1 MongoDB Atlas

1. Create a new M0 cluster in your preferred region.
2. Create DB user:
   1. Atlas -> Security -> Database Access.
   2. Add new database user.
   3. Grant readWrite on database thechat.
3. Configure network access:
   1. Atlas -> Security -> Network Access.
   2. Add IP address 0.0.0.0/0 for Render compatibility.
4. Obtain connection string:
   1. Atlas -> Cluster -> Connect.
   2. Drivers.
   3. Copy URI and replace username/password placeholders.
5. Save this URI for Render MONGODB_URI.

## 5.2 Backend on Render

### Step A: Create service

1. Push code to GitHub main branch.
2. Render dashboard -> New -> Web Service.
3. Connect repository and select this project.

### Step B: Configure build/runtime

Use these exact values:

| Setting | Value |
|---------|-------|
| Name | chatapp-backend |
| Root Directory | backend |
| Runtime | Python 3 |
| Build Command | pip install -r requirements.txt |
| Start Command | uvicorn main:app --host 0.0.0.0 --port $PORT |

### Step C: Configure secrets

In Environment Variables add:

1. MONGODB_URI=<atlas-uri>
2. JWT_SECRET=<generated-secret>
3. CORS_ORIGINS=https://<github-username>.github.io

### Step D: Deploy and verify

1. Click Create Web Service.
2. Wait for build logs to finish.
3. Open https://<render-service>.onrender.com/health.
4. Confirm JSON response is {"status":"ok"}.

Free tier behavior:

- Service sleeps after inactivity.
- First request after idle may take around 30 seconds.

## 5.3 Frontend on GitHub Pages

This project currently uses relative /api calls in frontend services.
For production, choose one approach:

1. Preferred: add an environment base URL and prepend it in API services.
2. Alternative: host frontend and backend behind one shared origin/reverse proxy.

### Step A: Build with correct base-href

From frontend/:

```powershell
ng build --configuration production --base-href "https://<github-username>.github.io/<repo-name>/"
```

Output directory:

frontend/dist/frontend/browser/

### Step B: Deploy manually to Pages

```powershell
npm install -g angular-cli-ghpages
npx angular-cli-ghpages --dir=dist/frontend/browser
```

### Step C: Enable Pages in repository settings

1. GitHub -> Repository -> Settings -> Pages.
2. Source: Deploy from a branch.
3. Branch: gh-pages, folder: /(root).

### Step D: Add SPA fallback file

```powershell
Copy-Item dist/frontend/browser/index.html dist/frontend/browser/404.html
```

Redeploy after adding fallback so deep links load correctly.

### Step E: Optional GitHub Actions automation

Create .github/workflows/deploy-frontend.yml:

```yaml
name: Deploy Frontend

on:
  push:
    branches: [main]
    paths: [frontend/**]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 18

      - name: Build frontend
        working-directory: frontend
        run: |
          npm ci
          npx ng build --configuration production --base-href "https://${{ github.repository_owner }}.github.io/${{ github.event.repository.name }}/"
          cp dist/frontend/browser/index.html dist/frontend/browser/404.html

      - name: Deploy to gh-pages
        uses: peaceiris/actions-gh-pages@v4
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: frontend/dist/frontend/browser
```

---

## 6. Post-Deployment Validation

Run these checks in order.

### 6.1 API health

```powershell
curl https://<render-service>.onrender.com/health
```

Expected:

{"status":"ok"}

### 6.2 Auth flow

```powershell
curl -X POST https://<render-service>.onrender.com/auth/register -H "Content-Type: application/json" -d '{"username":"deployuser1","email":"deployuser1@example.com","password":"supersecret123"}'

curl -X POST https://<render-service>.onrender.com/auth/login -H "Content-Type: application/json" -d '{"email":"deployuser1@example.com","password":"supersecret123"}'
```

Expected login response contains access_token.

### 6.3 Browser smoke test

1. Open Pages URL.
2. Register/Login as user A.
3. Open incognito, register/login as user B.
4. Start conversation A->B.
5. Send messages from both windows.
6. Confirm live delivery and conversation list update.

---

## 7. Operations: Update, Rollback, and Rotation

### 7.1 Standard update procedure

1. Merge tested changes to main.
2. Confirm Render auto-deploy succeeds.
3. Confirm frontend deploy succeeds.
4. Run section 6 smoke tests.

### 7.2 Backend rollback

1. In Render service, open Deploys tab.
2. Select previous healthy deploy.
3. Click Rollback/Promote previous deploy.
4. Re-run health and auth checks.

### 7.3 Frontend rollback

1. Re-run deployment from a previous stable git commit.
2. Or redeploy previously known-good gh-pages output.
3. Confirm deep-link routing still works.

### 7.4 JWT secret rotation

1. Generate new secret.
2. Update JWT_SECRET in Render.
3. Redeploy backend.
4. Expect all users to log in again.

---

## 8. Troubleshooting

### CORS error in browser console

Cause: CORS_ORIGINS missing frontend origin.

Fix:

1. Add exact origin in Render env var.
2. Redeploy backend.
3. Hard-refresh browser.

### 401 on authenticated API calls

Cause candidates:

1. Expired JWT.
2. Wrong JWT_SECRET after redeploy.
3. Token not being attached by frontend interceptor.

Fix:

1. Log out and log in again.
2. Verify Authorization header in browser network panel.

### WebSocket disconnects immediately

Cause candidates:

1. Invalid token in query string.
2. User is not a participant of conversation.
3. Backend cold start delay on free tier.

Fix:

1. Reopen conversation after login.
2. Validate user is in conversation participants.
3. Retry after backend wakes up.

### 404 on page refresh for chat route

Cause: Missing 404.html SPA fallback on GitHub Pages.

Fix:

1. Copy index.html to 404.html in built output.
2. Redeploy gh-pages.
