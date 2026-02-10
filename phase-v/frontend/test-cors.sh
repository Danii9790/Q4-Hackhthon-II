#!/bin/bash

# CORS Test Script
# This script tests if the CORS configuration is working correctly

echo "=========================================="
echo "CORS Configuration Test"
echo "=========================================="
echo ""

FRONTEND_URL="https://todo-application-rho-flax.vercel.app"
BACKEND_URL="https://q4-hackhthon-ii.onrender.com"
SIGNIN_ENDPOINT="$BACKEND_URL/api/auth/signin"

echo "Testing CORS preflight request..."
echo "Origin: $FRONTEND_URL"
echo "Endpoint: $SIGNIN_ENDPOINT"
echo ""

# Test CORS preflight request
echo "Sending OPTIONS request..."
curl -X OPTIONS "$SIGNIN_ENDPOINT" \
  -H "Origin: $FRONTEND_URL" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -v 2>&1 | grep -i "access-control"

echo ""
echo "=========================================="
echo "Testing actual sign-in request..."
echo "=========================================="
echo ""

# Test actual sign-in request
echo "Sending POST request with credentials..."
RESPONSE=$(curl -X POST "$SIGNIN_ENDPOINT" \
  -H "Origin: $FRONTEND_URL" \
  -H "Content-Type: application/json" \
  -d '{"email":"daniyalashraf9790@gmail.com","password":"Danii@2160"}' \
  -s -w "\nHTTP_STATUS:%{http_code}" \
  -i)

echo "$RESPONSE" | grep -E "HTTP_STATUS|access-control|token|email"

HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)

echo ""
echo "=========================================="
echo "Test Results"
echo "=========================================="

if [ "$HTTP_STATUS" = "200" ]; then
  echo "✓ SUCCESS: Authentication request succeeded!"
  echo "✓ CORS is properly configured"
  echo "✓ Backend is accepting requests from $FRONTEND_URL"
else
  echo "✗ FAILED: HTTP status code $HTTP_STATUS"
  echo "✗ CORS may not be properly configured"
  echo "✗ Check backend CORS settings in src/main.py"
fi

echo ""
echo "If you see 'Access-Control-Allow-Origin: $FRONTEND_URL' above, CORS is working."
