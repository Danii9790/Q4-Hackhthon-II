# Better Auth Integration Guide

This document explains how Better Auth is integrated into the Todo application with FastAPI backend.

## Architecture Overview

This application uses a **hybrid authentication approach**:

1. **Frontend (Next.js)**: Better Auth client for session management
2. **Backend (FastAPI)**: JWT-based authentication with bcrypt password hashing
3. **Integration**: JWT tokens issued by FastAPI are stored by Better Auth session utilities

### Authentication Flow

```
┌─────────────┐
│   User      │
└──────┬──────┘
       │
       │ 1. Sign In / Sign Up
       ▼
┌─────────────────────────────────────────────────┐
│  Frontend (Next.js + Better Auth Utilities)    │
│  - auth.ts: signIn(), signUp(), signOut()      │
│  - Forms: LoginForm, SignupForm                │
└──────────────────┬──────────────────────────────┘
                   │
                   │ 2. POST /api/auth/signin or /signup
                   ▼
┌─────────────────────────────────────────────────┐
│  Backend (FastAPI)                              │
│  - auth.py: Issues JWT token with user data    │
│  - Token includes: sub (user_id), email, name  │
│  - Token expires in 7 days                     │
└──────────────────┬──────────────────────────────┘
                   │
                   │ 3. Response: { token, user }
                   ▼
┌─────────────────────────────────────────────────┐
│  Frontend (Session Storage)                     │
│  - localStorage.setItem('better-auth.session_token', token) │
│  - localStorage.setItem('better-auth.user_data', user)      │
└──────────────────┬──────────────────────────────┘
                   │
                   │ 4. API Request with Authorization header
                   ▼
┌─────────────────────────────────────────────────┐
│  API Client (axios)                             │
│  - Interceptor adds: Authorization: Bearer <token> │
└──────────────────┬──────────────────────────────┘
                   │
                   │ 5. Request with JWT token
                   ▼
┌─────────────────────────────────────────────────┐
│  Backend (FastAPI Middleware)                   │
│  - get_current_user dependency verifies JWT     │
│  - Extracts user_id from token (sub claim)     │
│  - Fetches user from database                  │
│  - Enforces user isolation (user owns resources) │
└─────────────────────────────────────────────────┘
```

## Frontend Configuration

### Environment Variables

**File**: `frontend/.env`

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=https://q4-hackhthon-ii.onrender.com

# Better Auth Configuration
NEXT_PUBLIC_AUTH_URL=http://localhost:3000  # Frontend URL for local dev
NEXT_PUBLIC_BETTER_AUTH_URL=http://localhost:8000/auth  # Not currently used
```

**Production Environment Variables** (Vercel):

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=https://q4-hackhthon-ii.onrender.com

# Better Auth Configuration
NEXT_PUBLIC_AUTH_URL=https://q4-hackhthon-ii.vercel.app
```

### Key Files

#### 1. Auth Configuration (`frontend/src/lib/auth.config.ts`)
- Defines AUTH_ENDPOINTS for FastAPI backend
- Exports session storage keys

#### 2. Auth Utilities (`frontend/src/lib/auth.ts`)
- `signIn(email, password)`: Authenticate and store session
- `signUp(email, password, name)`: Create account and store session
- `signOut()`: Clear session data
- `getAuthToken()`: Retrieve JWT token for API requests
- `getCurrentUser()`: Retrieve user data from session
- `isAuthenticated()`: Check if user has valid session

#### 3. API Client (`frontend/src/lib/api.ts`)
- Axios instance configured with base URL
- Request interceptor adds JWT token to all requests
- Response interceptor handles 401 errors (clears session, redirects to login)

#### 4. Authentication Forms
- `LoginForm.tsx`: Uses `auth.signIn()`
- `SignupForm.tsx`: Uses `auth.signUp()`

#### 5. Route Protection
- `middleware.ts`: Next.js middleware for protected routes
- `AuthGuard.tsx`: Client-side component for additional protection

## Backend Configuration

### Environment Variables

**File**: `backend/.env`

```bash
# Better Auth Configuration (Shared Secret)
BETTER_AUTH_SECRET=5QVFwF2Cb2uiHwmxWEd4uNF1R8fQFKJ3

# Database
DATABASE_URL=postgresql://neondb_owner:npg_YyJMvo0jbU6W@ep-fragrant-grass-aeghurw1-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require

# Application Settings
APP_NAME=Todo API
DEBUG=True
```

**IMPORTANT**: The `BETTER_AUTH_SECRET` must be the same on both frontend and backend for JWT verification to work.

### Key Files

#### 1. Authentication Routes (`backend/src/api/routes/auth.py`)
- `POST /api/auth/signup`: Create user, issue JWT token
- `POST /api/auth/signin`: Verify credentials, issue JWT token
- `POST /api/auth/forgot-password`: Generate reset token
- `POST /api/auth/reset-password`: Reset password with token

#### 2. JWT Dependencies (`backend/src/api/dependencies/auth.py`)
- `get_current_user`: Verify JWT, return User object
- `get_current_user_id`: Verify JWT, return user ID string
- `require_auth`: Verify JWT, return token payload
- `get_optional_user`: Optional authentication (returns None if no token)

#### 3. Protected Routes
All protected endpoints use authentication dependencies:

```python
from src.api.dependencies import CurrentUser, CurrentUserId

@app.get("/api/users/me")
async def get_me(user: CurrentUser):
    return user

@app.get("/api/tasks")
async def get_tasks(user_id: CurrentUserId):
    return tasks.filter(user_id=user_id)
```

## JWT Token Structure

The JWT token issued by FastAPI contains:

```json
{
  "sub": "user-uuid-here",      // User ID (subject)
  "email": "user@example.com",  // User email
  "name": "John Doe",           // User display name (optional)
  "iat": 1234567890,            // Issued at timestamp
  "exp": 1235172690             // Expiration timestamp (7 days)
}
```

- **Algorithm**: HS256
- **Secret**: BETTER_AUTH_SECRET environment variable
- **Expiration**: 7 days from issuance

## User Isolation

All user-specific resources are isolated by user ID:

1. **Frontend**: API client includes user ID in request URLs
2. **Backend**: JWT verification extracts user ID from token
3. **Database**: All queries filter by user_id to ensure data isolation

Example task flow:
```
Frontend: GET /api/users/{user_id}/tasks
    ↓
Backend: Extract user_id from JWT (sub claim)
    ↓
Backend: Verify user_id in URL matches user_id in JWT
    ↓
Backend: Query database: SELECT * FROM tasks WHERE user_id = ?
    ↓
Backend: Return only tasks belonging to authenticated user
```

## Security Best Practices

### 1. Password Storage
- Passwords hashed with bcrypt (12 rounds)
- Bcrypt has 72-byte limit (handled in code)
- Passwords NEVER stored in plaintext or returned in API responses

### 2. JWT Token Security
- Signed with secret key using HS256
- Expires after 7 days
- Verified on every protected request
- Invalidated on sign out (client-side only)

### 3. HTTPS Required
- Production URLs use HTTPS
- Never send tokens over HTTP
- Cookies should be HttpOnly in production (future enhancement)

### 4. CORS Configuration
- Backend should only allow requests from trusted frontend domains
- Configure CORS origins in FastAPI settings

## Development vs Production

### Local Development
```bash
# Frontend (http://localhost:3000)
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_AUTH_URL=http://localhost:3000

# Backend (http://localhost:8000)
BETTER_AUTH_SECRET=5QVFwF2Cb2uiHwmxWEd4uNF1R8fQFKJ3
```

### Production
```bash
# Frontend (https://q4-hackhthon-ii.vercel.app)
NEXT_PUBLIC_API_URL=https://q4-hackhthon-ii.onrender.com
NEXT_PUBLIC_AUTH_URL=https://q4-hackhthon-ii.vercel.app

# Backend (https://q4-hackhthon-ii.onrender.com)
BETTER_AUTH_SECRET=<same-secret-as-local>
```

## Troubleshooting

### "Invalid or expired token" Error

**Cause**: JWT token verification failed

**Solutions**:
1. Check BETTER_AUTH_SECRET matches on frontend and backend
2. Ensure token hasn't expired (7-day limit)
3. Verify Authorization header format: `Bearer <token>`
4. Check token is being sent in API requests (browser dev tools → Network)

### 401 Unauthorized on Protected Routes

**Cause**: User not authenticated or token invalid

**Solutions**:
1. Sign in again to get fresh token
2. Check localStorage for `better-auth.session_token`
3. Verify API client interceptor is adding Authorization header
4. Check backend JWT verification is working

### CORS Errors

**Cause**: Backend rejecting requests from frontend domain

**Solutions**:
1. Configure CORS in FastAPI to allow frontend origin
2. Add frontend URL to CORS origins list
3. Ensure credentials are included if using cookies

## Future Enhancements

1. **HttpOnly Cookies**: Store JWT in HttpOnly cookies instead of localStorage
2. **Token Refresh**: Implement refresh token rotation for enhanced security
3. **Session Management**: Add server-side session store for token invalidation
4. **OAuth Integration**: Add social login providers (Google, GitHub)
5. **2FA**: Implement two-factor authentication
6. **Email Verification**: Require email verification before account activation
7. **Rate Limiting**: Add rate limiting to auth endpoints
8. **Audit Logging**: Log all authentication events for security monitoring

## Testing

### Manual Testing Steps

1. **Sign Up Flow**:
   - Navigate to `/signup`
   - Fill in email, password, name
   - Submit form
   - Verify redirect to `/dashboard`
   - Check localStorage for session token and user data

2. **Sign In Flow**:
   - Navigate to `/login`
   - Fill in email and password
   - Submit form
   - Verify redirect to `/dashboard`
   - Check localStorage for session token and user data

3. **Protected Route Access**:
   - Sign out
   - Try to access `/dashboard`
   - Verify redirect to `/login`
   - Sign in
   - Verify access to `/dashboard`

4. **API Request Authentication**:
   - Sign in
   - Open browser DevTools → Network
   - Navigate to `/dashboard` (triggers task API call)
   - Verify Authorization header: `Bearer <token>`
   - Verify response contains user's tasks

5. **Token Expiration**:
   - Manually expire token by modifying BETTER_AUTH_SECRET on backend
   - Try to access protected route
   - Verify redirect to `/login`
   - Check localStorage is cleared

## Additional Resources

- [Better Auth Documentation](https://better-auth.com)
- [JWT.io](https://jwt.io) - JWT debugger and documentation
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [FastAPI Security Tutorial](https://fastapi.tiangolo.com/tutorial/security/)
