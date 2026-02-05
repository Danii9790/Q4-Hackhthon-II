# Security Hardening Documentation

This document describes the security features implemented in the Todo AI Chatbot backend API as part of tasks T083-T085.

## Overview

The backend implements three layers of security hardening:

1. **Rate Limiting (T083)**: Prevents abuse and ensures fair resource allocation
2. **Message Validation (T084)**: Protects against injection attacks and oversized payloads
3. **CORS Configuration (T085)**: Restricts cross-origin requests to trusted domains only

## 1. Rate Limiting (T083)

### Implementation

Rate limiting is implemented using `slowapi`, a rate limiting extension for FastAPI.

**Location**: `/home/xdev/Hackhthon-II/phase-III/backend/src/api/security.py`

**Key Features**:
- Sliding window algorithm for accurate rate limiting
- Per-user rate limiting based on IP + user_id
- Returns HTTP 429 (Too Many Requests) when limit exceeded
- Includes `X-RateLimit-*` headers in responses
- In-memory storage (Redis for production)

### Configuration

Environment Variables:

```bash
# Maximum requests per minute per user
RATE_LIMIT_PER_MINUTE=10  # Default: 10

# Optional: Redis for distributed rate limiting (multi-instance deployments)
REDIS_RATE_LIMIT_URL=redis://localhost:6379/0
```

### Usage Example

The chat endpoint is protected with rate limiting:

```python
@router.post("/api/{user_id}/chat")
@limiter.limit("10/minute")  # 10 requests per minute
async def chat_endpoint(request_obj: Request, ...):
    ...
```

### Response Headers

When rate limit is active, responses include:

```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1641234567
```

### Rate Limit Exceeded Response

```json
{
  "error": "Too Many Requests",
  "message": "Rate limit exceeded. Please try again in 60 seconds.",
  "code": "RATE_LIMIT_EXCEEDED",
  "details": {
    "retry_after": 60
  }
}
```

HTTP Status: 429 Too Many Requests

### Production Recommendations

1. **Use Redis for distributed deployments**:
   ```bash
   REDIS_RATE_LIMIT_URL=redis://your-redis-host:6379/0
   ```

2. **Adjust rate limits based on usage patterns**:
   - Development: 10/minute (default)
   - Staging: 30/minute
   - Production: 60/minute or higher

3. **Monitor rate limit violations**:
   - Check logs for "Rate limit exceeded" warnings
   - Set up alerts for excessive violations

## 2. Message Validation (T084)

### Implementation

Message validation and sanitization protects against injection attacks and oversized payloads.

**Location**: `/home/xdev/Hackhthon-II/phase-III/backend/src/api/security.py`

### Validation Rules

1. **Length Validation**:
   - Maximum: 10,000 characters (configurable)
   - Enforced before processing
   - Returns 400 Bad Request if exceeded

2. **Input Sanitization**:
   - Removes null bytes (`\x00`)
   - Removes control characters (except `\n`, `\t`, `\r`)
   - Normalizes whitespace
   - Trims leading/trailing whitespace

### Configuration

Environment Variable:

```bash
# Maximum message length in characters
MAX_MESSAGE_LENGTH=10000  # Default: 10,000
```

### Validation Process

```python
# 1. Validate message length
validate_message_length(request.message)

# 2. Sanitize message content
sanitized_message = sanitize_message(request.message)
```

### Error Responses

**Message Too Long** (400 Bad Request):

```json
{
  "error": "Bad Request",
  "message": "Message exceeds maximum length of 10000 characters. Your message is 15000 characters long. Please shorten your message and try again.",
  "code": "BAD_REQUEST"
}
```

**Empty After Sanitization** (400 Bad Request):

```json
{
  "error": "Bad Request",
  "message": "Message cannot be empty",
  "code": "BAD_REQUEST"
}
```

### Security Benefits

1. **Prevents Buffer Overflow**: Enforces size limits
2. **Prevents Injection Attacks**: Removes dangerous characters
3. **Prevents DoS**: Limits processing resources per request
4. **Maintains Data Quality**: Normalizes whitespace and formatting

### Production Recommendations

1. **Keep message length under 10,000 characters** for optimal performance
2. **Monitor validation failures** for potential attack patterns
3. **Log sanitization changes** for security auditing
4. **Consider additional validation** for specific use cases (e.g., HTML/JSON content)

## 3. CORS Configuration (T085)

### Implementation

CORS (Cross-Origin Resource Sharing) restricts which domains can access the API.

**Location**: `/home/xdev/Hackhthon-II/phase-III/backend/src/main.py`

### Configuration

Environment Variables:

```bash
# Comma-separated list of allowed frontend origins
FRONTEND_URL=http://localhost:3000,https://staging.example.com,https://example.com

# Environment (controls credentials)
ENVIRONMENT=development  # Options: development, production
```

### Behavior

**Development Mode**:
- Allows credentials (cookies, authorization headers)
- Permissive for local testing
- Includes localhost by default

**Production Mode**:
- Disables credentials for security
- Only allows explicitly configured origins
- Strict origin validation

### Allowed Methods

Only safe HTTP methods are allowed:

```
GET, POST, PUT, PATCH, DELETE
```

### Allowed Headers

Only necessary headers are allowed:

```
Content-Type
Authorization
X-Request-ID
X-Client-Version
```

### Production Configuration

**Development** (`.env`):

```bash
FRONTEND_URL=http://localhost:3000
ENVIRONMENT=development
```

**Staging**:

```bash
FRONTEND_URL=https://staging.example.com
ENVIRONMENT=production
```

**Production**:

```bash
FRONTEND_URL=https://example.com,https://www.example.com
ENVIRONMENT=production
```

### Multiple Origins

Support for multiple frontend environments:

```bash
FRONTEND_URL=http://localhost:3000,https://staging.example.com,https://example.com
```

### Security Benefits

1. **Prevents CSRF**: Restricts origins to trusted domains
2. **Prevents Unauthorized Access**: Blocks requests from unknown sources
3. **Controls Data Exposure**: Limits which sites can access API responses
4. **Secure by Default**: Explicit allowlist approach

## Environment Variables Reference

### Security Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `FRONTEND_URL` | string | `http://localhost:3000` | Comma-separated allowed origins |
| `RATE_LIMIT_PER_MINUTE` | integer | `10` | Max requests per minute per user |
| `MAX_MESSAGE_LENGTH` | integer | `10000` | Max characters per message |
| `ENVIRONMENT` | string | `development` | `development` or `production` |
| `REDIS_RATE_LIMIT_URL` | string | `memory://` | Redis URL for distributed rate limiting |

## Testing Security Features

### 1. Test Rate Limiting

```bash
# Send 11 requests rapidly (should fail on 11th)
for i in {1..11}; do
  curl -X POST http://localhost:8000/api/{user_id}/chat \
    -H "Content-Type: application/json" \
    -d '{"message": "test"}'
done
```

Expected: Last request returns 429 status.

### 2. Test Message Length Validation

```bash
# Send message exceeding 10,000 characters
curl -X POST http://localhost:8000/api/{user_id}/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "AAAAAAAAAA... (>10000 chars)"}'
```

Expected: Returns 400 status with length error.

### 3. Test CORS Configuration

```bash
# Test from disallowed origin
curl -X POST http://localhost:8000/api/{user_id}/chat \
  -H "Origin: https://evil.com" \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}' \
  -v
```

Expected: No `Access-Control-Allow-Origin` header in response.

## Monitoring and Logging

### Rate Limit Violations

Logs include:
- Request ID
- Client IP
- Path and method
- Timestamp

Example log entry:

```
WARNING: Rate limit exceeded
request_id=abc123 path=/api/{user_id}/chat method=POST client_ip=192.168.1.100
```

### Validation Failures

Logs include:
- Request ID
- Validation error details
- Message length
- Sanitization changes

Example log entry:

```
WARNING: Message validation failed: Message exceeds maximum length
request_id=def456 message_length=15000 max_length=10000
```

## Security Checklist

Before deploying to production:

- [ ] Set `FRONTEND_URL` to production domain(s)
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure `RATE_LIMIT_PER_MINUTE` appropriate for expected load
- [ ] Set up Redis for distributed rate limiting (if multi-instance)
- [ ] Review and adjust `MAX_MESSAGE_LENGTH` if needed
- [ ] Test rate limiting with production load
- [ ] Test message validation with edge cases
- [ ] Verify CORS configuration with production frontend
- [ ] Set up monitoring for security events
- [ ] Configure alerts for excessive rate limit violations
- [ ] Review logs for validation failures

## Troubleshooting

### Issue: Rate limiting too aggressive

**Solution**: Increase `RATE_LIMIT_PER_MINUTE`:

```bash
RATE_LIMIT_PER_MINUTE=60
```

### Issue: Frontend cannot connect (CORS errors)

**Solution**: Verify `FRONTEND_URL` includes your frontend domain:

```bash
FRONTEND_URL=https://your-frontend-domain.com
```

### Issue: Messages rejected as too long

**Solution**: Increase `MAX_MESSAGE_LENGTH` if legitimate use case:

```bash
MAX_MESSAGE_LENGTH=50000
```

### Issue: Rate limit not working across multiple instances

**Solution**: Configure Redis for distributed rate limiting:

```bash
REDIS_RATE_LIMIT_URL=redis://your-redis-host:6379/0
```

## References

- **Task T083**: Rate Limiting Implementation
- **Task T084**: Message Length Validation
- **Task T085**: CORS Configuration
- **slowapi Documentation**: https://slowapi.readthedocs.io/
- **FastAPI Security Guide**: https://fastapi.tiangolo.com/tutorial/security/
- **OWASP Rate Limiting**: https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html

## Changelog

### 2026-02-02
- Initial security hardening implementation
- Added rate limiting with slowapi
- Added message validation and sanitization
- Configured environment-based CORS
- Created comprehensive documentation
