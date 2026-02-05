# Render Deployment Guide - Phase-II Backend

This guide will help you deploy the Phase-II backend to Render and fix authentication issues.

## Prerequisites

1. A Render account at https://render.com
2. A PostgreSQL database on Render (or use an external one)
3. Your GitHub repository connected to Render

## Step 1: Create PostgreSQL Database

1. Go to Render Dashboard → **New** → **PostgreSQL**
2. Choose database name: `q4-hackhthon-db` (or any name you prefer)
3. Select region closest to your users
4. Choose database plan (Free is fine for development)
5. Click **Create Database**

6. **Important**: Copy the **Internal Database URL** from the dashboard
   - Format: `postgresql://user:password@host:port/database`
   - You'll need this for Step 3

## Step 2: Create Web Service

1. Go to Render Dashboard → **New** → **Web Service**
2. Connect your GitHub repository: `Danii9790/Q4-Hackhthon-II`
3. Render will detect the `render.yaml` configuration automatically
4. Verify the following settings:
   - **Name**: `q4-hackhthon-phase2-backend` (auto-detected)
   - **Branch**: `main`
   - **Runtime**: Python 3.12
   - **Build Command**: `cd phase-II/backend && pip install -e .[dev]`
   - **Start Command**: `cd phase-II/backend && gunicorn src.main:app ...`

5. **DO NOT CLICK CREATE YET** - First set environment variables!

## Step 3: Configure Environment Variables (CRITICAL)

Before creating the service, you MUST set these environment variables:

### 3.1 Add DATABASE_URL

1. Scroll down to **Environment** section
2. Click **Add Environment Variable**
3. Key: `DATABASE_URL`
4. Value: Paste the Internal Database URL from Step 1
   - Example: `postgresql://q4_hackhthon_db_user:abc123@dpg-cxxx.oregon-postgres.render.com/q4_hackhthon_db`
5. Click **Save**

### 3.2 Add BETTER_AUTH_SECRET

This is **CRITICAL** - without this, authentication will fail with 500 errors!

1. Click **Add Environment Variable** again
2. Key: `BETTER_AUTH_SECRET`
3. Value: Generate a secure secret using one of these methods:

   **Option A: Use Python** (if you have Python installed):
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

   **Option B: Use OpenSSL**:
   ```bash
   openssl rand -base64 32
   ```

   **Option C: Use an online generator** (not recommended for production):
   - Generate at least 32 random characters

4. Example value: `aB3xK9mP2qL7vN5wR8sT4uY6cZ1dF0eH`
5. Click **Save**

### 3.3 Optional Environment Variables

You can also add (these have defaults):
- `ENVIRONMENT`: `production`
- `LOG_LEVEL`: `INFO`
- `PYTHON_VERSION`: `3.12`

## Step 4: Deploy the Service

1. Click **Create Web Service** (or **Update** if editing existing)
2. Render will automatically:
   - Build your application
   - Run database migrations via `preDeployCommand`
   - Start the server
   - Set up HTTPS with SSL

3. Watch the deployment logs:
   - Click on your service → **Logs** tab
   - Look for: `Application startup completed successfully`
   - If you see errors about missing environment variables, go back to Step 3

## Step 5: Verify Deployment

### 5.1 Check Health Endpoint

```bash
curl https://your-service-name.onrender.com/health
```

Expected response:
```json
{"status": "healthy", "timestamp": "2026-02-06"}
```

### 5.2 Check API Documentation

Visit: `https://your-service-name.onrender.com/docs`

You should see the Swagger UI with all endpoints.

### 5.3 Test Authentication

**Signup** (create a new user):
```bash
curl -X POST https://your-service-name.onrender.com/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123",
    "name": "Test User"
  }'
```

Expected response (200 OK):
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "uuid-here",
    "email": "test@example.com",
    "name": "Test User",
    "created_at": "2026-02-06T00:00:00Z"
  }
}
```

**Signin** (authenticate existing user):
```bash
curl -X POST https://your-service-name.onrender.com/api/auth/signin \
  -H "Content-Type: application/json" \
  -d '{
    "email": "daniyalashraf9790@gmail.com",
    "password": "Danii@2160"
  }'
```

Expected response (200 OK):
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "uuid-here",
    "email": "daniyalashraf9790@gmail.com",
    "name": null,
    "created_at": "2026-02-06T00:00:00Z"
  }
}
```

## Troubleshooting

### Error: 500 Internal Server Error on `/api/auth/signin`

**Cause**: `BETTER_AUTH_SECRET` is not set or empty in Render environment variables.

**Solution**:
1. Go to your service in Render Dashboard
2. Click **Environment** tab
3. Verify `BETTER_AUTH_SECRET` exists and has a value (at least 32 characters)
4. If missing, add it using Step 3.2 above
5. Click **Save Changes**
6. Render will automatically redeploy

### Error: "Application startup failed"

**Cause**: One or more required environment variables are missing.

**Solution**:
1. Check the logs in Render Dashboard
2. Look for error messages about missing variables
3. Add the missing variables in the Environment tab
4. Save and wait for redeploy

### Error: Database connection failed

**Cause**: `DATABASE_URL` is incorrect or database doesn't exist.

**Solution**:
1. Verify database exists in Render Dashboard
2. Copy the Internal Database URL again
3. Update `DATABASE_URL` in service environment
4. Make sure it starts with `postgresql://` (Render will auto-convert to `postgresql+asyncpg://`)

### Error: Migration failed

**Cause**: Database schema issues or connection problems.

**Solution**:
1. Check logs for specific error
2. Verify `DATABASE_URL` is correct
3. Try running migrations manually:
   ```bash
   # SSH into the service (Render supports this)
   cd phase-II/backend
   alembic upgrade head
   ```

### Service keeps restarting

**Cause**: Application is crashing on startup.

**Solution**:
1. Check logs in Render Dashboard
2. Look for error during startup
3. Common issues:
   - Missing `BETTER_AUTH_SECRET`
   - Missing `DATABASE_URL`
   - Database connection failure
4. Fix environment variables and wait for redeploy

## Monitoring

### View Logs

1. Go to your service in Render Dashboard
2. Click **Logs** tab
3. Filter by level: INFO, WARNING, ERROR

### Check Metrics

1. Go to service → **Metrics** tab
2. Monitor:
   - CPU usage
   - Memory usage
   - Response times
   - Error rates

### Set Up Alerts

1. Go to service → **Settings** → **Alerts**
2. Configure alerts for:
   - High CPU usage (>80%)
   - High memory usage (>80%)
   - High error rate (>5%)
   - Service downtime

## Security Best Practices

1. **Never commit `.env` files** to git
2. **Use strong, random secrets** for `BETTER_AUTH_SECRET`
3. **Rotate secrets periodically** (every 90 days)
4. **Use different secrets** for development and production
5. **Enable SSL** (Render does this automatically)
6. **Set up CORS** correctly for your frontend domain
7. **Monitor logs** for suspicious activity
8. **Keep dependencies updated** regularly

## Next Steps

After successful backend deployment:

1. Deploy your frontend to Vercel
2. Update frontend API URL to point to Render backend
3. Configure CORS in `src/main.py` to allow your frontend domain
4. Test the full application end-to-end
5. Set up monitoring and alerts

## Support

If you encounter issues:

1. Check Render logs first
2. Review this guide's troubleshooting section
3. Check the [Render documentation](https://render.com/docs)
4. Open an issue in the GitHub repository

---

**Last Updated**: 2026-02-06
**Repository**: https://github.com/Danii9790/Q4-Hackhthon-II
