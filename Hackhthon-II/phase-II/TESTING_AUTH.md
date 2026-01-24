# Testing Better Auth Implementation

This guide provides step-by-step instructions for testing the Better Auth implementation in your Todo application.

## Prerequisites

1. Backend server running on port 8000
2. Frontend server running on port 3000
3. PostgreSQL database (Neon) configured
4. All environment variables set correctly

## Setup

### 1. Configure Environment Variables

**Frontend** (`frontend/.env`):
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_AUTH_URL=http://localhost:3000
```

**Backend** (`backend/.env`):
```bash
BETTER_AUTH_SECRET=5QVFwF2Cb2uiHwmxWEd4uNF1R8fQFKJ3
DATABASE_URL=postgresql://neondb_owner:npg_YyJMvo0jbU6W@ep-fragrant-grass-aeghurw1-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require
APP_NAME=Todo API
DEBUG=True
```

### 2. Start Backend Server

```bash
cd backend
python -m uvicorn src.main:app --reload --port 8000
```

Verify backend is running:
```bash
curl http://localhost:8000/api/health
```

### 3. Start Frontend Server

```bash
cd frontend
npm run dev
```

Verify frontend is running: Open http://localhost:3000

## Test Cases

### Test 1: User Signup Flow

**Objective**: Verify new user can create account

**Steps**:
1. Navigate to http://localhost:3000/signup
2. Fill in the form:
   - Name: Test User
   - Email: test@example.com
   - Password: password123
   - Confirm Password: password123
3. Click "Create Account"
4. Observe loading spinner
5. Verify redirect to `/dashboard`
6. Open browser DevTools → Application → Local Storage
7. Verify items:
   - `better-auth.session_token`: JWT token
   - `better-auth.user_data`: JSON with user info

**Expected Results**:
- Account created successfully
- Redirected to dashboard
- Session token stored in localStorage
- User data stored in localStorage

**Backend Verification**:
```bash
# Check user in database
cd backend
python -c "
from src.db import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT email, name FROM users WHERE email = \"test@example.com\"'))
    print(result.fetchone())
"
```

### Test 2: User Signin Flow

**Objective**: Verify existing user can sign in

**Steps**:
1. Navigate to http://localhost:3000/login
2. Fill in the form:
   - Email: test@example.com
   - Password: password123
3. Click "Sign In"
4. Observe loading spinner
5. Verify redirect to `/dashboard`
6. Check localStorage for session token

**Expected Results**:
- Authentication successful
- Redirected to dashboard
- Session token stored in localStorage

### Test 3: Protected Route Access

**Objective**: Verify protected routes require authentication

**Steps**:
1. Sign out (if signed in)
2. Open DevTools → Console
3. Run: `localStorage.clear()`
4. Navigate to http://localhost:3000/dashboard
5. Verify redirect to `/login?redirect=/dashboard`
6. Sign in
7. Navigate to `/dashboard` again
8. Verify access granted

**Expected Results**:
- Unauthenticated users redirected to login
- Authenticated users can access dashboard

### Test 4: API Authentication

**Objective**: Verify API requests include JWT token

**Steps**:
1. Sign in to the application
2. Open DevTools → Network tab
3. Navigate to `/dashboard` (triggers API call)
4. Click on the API request (`/api/users/{user_id}/tasks`)
5. Check Request Headers:
   - Look for `Authorization: Bearer <token>`
6. Verify Response:
   - Should contain user's tasks
   - Status code: 200

**Expected Results**:
- Authorization header present
- JWT token valid
- API returns user's tasks

### Test 5: User Isolation

**Objective**: Verify users can only access their own data

**Steps**:
1. Sign out
2. Create account: user1@example.com
3. Create a task (e.g., "User 1 Task")
4. Sign out
5. Create account: user2@example.com
6. Try to access user1's tasks (not possible via UI)
7. Verify only user2's tasks are visible

**Backend Verification**:
```bash
# Use Postman or curl with user2's token to access user1's tasks
curl -H "Authorization: Bearer <user2_token>" \
     http://localhost:8000/api/users/<user1_id>/tasks

# Expected: 403 Forbidden or empty list (depending on implementation)
```

**Expected Results**:
- Each user sees only their own tasks
- No cross-user data access

### Test 6: Token Validation

**Objective**: Verify invalid/expired tokens are rejected

**Steps**:
1. Sign in to get valid token
2. Copy token from localStorage
3. Modify the token (change one character)
4. Replace token in localStorage
5. Navigate to `/dashboard`
6. Observe behavior

**Expected Results**:
- API request fails with 401
- Session cleared from localStorage
- Redirected to login page

### Test 7: Sign Out Flow

**Objective**: Verify sign out clears session

**Steps**:
1. Sign in to the application
2. Verify localStorage contains session data
3. Sign out (add sign out button if not present)
4. Verify localStorage is cleared
5. Try to access protected route
6. Verify redirect to login

**Expected Results**:
- Session cleared on sign out
- Protected routes inaccessible after sign out

### Test 8: Password Reset Flow

**Objective**: Verify password reset functionality

**Steps**:
1. Navigate to `/forgot-password`
2. Enter email: test@example.com
3. Submit form
4. Note the reset token in response (development only)
5. Navigate to `/reset-password?token=<token>`
6. Enter new password: newpassword123
7. Submit form
8. Try to sign in with old password (should fail)
9. Sign in with new password (should succeed)

**Expected Results**:
- Reset token generated and emailed (in prod)
- New password works
- Old password no longer works

## Automated Testing

### Frontend Tests

Create test file: `frontend/src/__tests__/auth.test.ts`

```typescript
import { signIn, signUp, signOut, isAuthenticated, getAuthToken, getCurrentUser } from '@/lib/auth';

describe('Authentication Utilities', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  test('signUp stores token and user data', async () => {
    const user = await signUp('test@example.com', 'password123', 'Test User');
    expect(user).toHaveProperty('id');
    expect(user).toHaveProperty('email', 'test@example.com');
    expect(getAuthToken()).toBeTruthy();
    expect(getCurrentUser()).toEqual(user);
  });

  test('signIn authenticates existing user', async () => {
    await signUp('test@example.com', 'password123', 'Test User');
    localStorage.clear(); // Sign out

    const user = await signIn('test@example.com', 'password123');
    expect(user).toHaveProperty('id');
    expect(isAuthenticated()).toBe(true);
  });

  test('signOut clears session data', async () => {
    await signUp('test@example.com', 'password123', 'Test User');
    expect(isAuthenticated()).toBe(true);

    await signOut();
    expect(isAuthenticated()).toBe(false);
    expect(getAuthToken()).toBeNull();
    expect(getCurrentUser()).toBeNull();
  });
});
```

### Backend Tests

Create test file: `backend/tests/test_auth.py`

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.db import Base, get_session

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_session():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_session] = override_get_session
client = TestClient(app)

def test_signup():
    response = client.post("/api/auth/signup", json={
        "email": "test@example.com",
        "password": "password123",
        "name": "Test User"
    })
    assert response.status_code == 201
    data = response.json()
    assert "token" in data
    assert "user" in data
    assert data["user"]["email"] == "test@example.com"

def test_signin():
    # First create a user
    client.post("/api/auth/signup", json={
        "email": "test@example.com",
        "password": "password123"
    })

    # Then sign in
    response = client.post("/api/auth/signin", json={
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert "user" in data

def test_protected_route_without_token():
    response = client.get("/api/users/test-id/tasks")
    assert response.status_code == 401

def test_protected_route_with_token():
    # Create user and get token
    signup_response = client.post("/api/auth/signup", json={
        "email": "test@example.com",
        "password": "password123"
    })
    token = signup_response.json()["token"]
    user_id = signup_response.json()["user"]["id"]

    # Access protected route
    response = client.get(
        f"/api/users/{user_id}/tasks",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
```

## Debugging Tips

### Check JWT Token Contents

Use jwt.io to decode and inspect your JWT token:

1. Copy token from localStorage (`better-auth.session_token`)
2. Paste at https://jwt.io
3. Verify payload contains:
   - `sub`: user ID
   - `email`: user email
   - `name`: user name
   - `exp`: expiration timestamp
   - `iat`: issued timestamp

### Verify Backend Secret

Python script to check backend secret:

```python
# backend/check_secret.py
import os
from dotenv import load_dotenv

load_dotenv()

secret = os.getenv("BETTER_AUTH_SECRET")
print(f"Backend BETTER_AUTH_SECRET: {secret[:10]}...")  # Print first 10 chars
```

### Verify Frontend Token

Browser Console:
```javascript
// Check if token exists
localStorage.getItem('better-auth.session_token')

// Check if user data exists
JSON.parse(localStorage.getItem('better-auth.user_data'))

// Check authentication status
// (in your app code)
```

### Network Request Debugging

1. Open DevTools → Network tab
2. Filter by "Fetch/XHR"
3. Click on failed requests
4. Check:
   - Request URL
   - Request Headers (especially Authorization)
   - Response Status Code
   - Response Body

## Common Issues and Solutions

### Issue: "Invalid or expired token"

**Cause**: JWT verification failed

**Solutions**:
1. Verify BETTER_AUTH_SECRET matches frontend and backend
2. Check token hasn't expired (7-day limit)
3. Ensure Authorization header format is correct

### Issue: 401 Unauthorized on all requests

**Cause**: Token not being sent

**Solutions**:
1. Check localStorage contains `better-auth.session_token`
2. Verify axios interceptor is running
3. Check Network tab for Authorization header

### Issue: CORS errors

**Cause**: Backend rejecting frontend requests

**Solutions**:
1. Configure CORS in FastAPI
2. Add frontend URL to allowed origins
3. Ensure backend is running

### Issue: User not found after signup

**Cause**: Database issue

**Solutions**:
1. Check database connection string
2. Verify database is accessible
3. Check database logs

## Success Criteria

All tests pass when:
- [ ] User can sign up successfully
- [ ] User can sign in successfully
- [ ] Protected routes require authentication
- [ ] API requests include JWT token
- [ ] Users can only access their own data
- [ ] Invalid tokens are rejected
- [ ] Sign out clears session
- [ ] Password reset works correctly

## Next Steps

After testing locally:
1. Update environment variables for production
2. Deploy frontend to Vercel
3. Deploy backend to Render
4. Test production deployment
5. Set up monitoring and error tracking
