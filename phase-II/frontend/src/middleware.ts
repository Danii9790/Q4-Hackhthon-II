/**
 * Next.js Middleware for Route Protection
 *
 * This middleware protects authenticated routes by checking for the presence
 * of a JWT token in cookies. If no token is found, unauthenticated users
 * are redirected to the login page.
 *
 * Protected Routes:
 * - /dashboard - Main application dashboard
 * - /dashboard/* - All dashboard sub-routes
 *
 * Public Routes:
 * - / - Landing page
 * - /login - Login page
 * - /signup - Signup page
 * - /forgot-password - Password reset request
 * - /reset-password - Password reset form
 */

import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

/**
 * Session token key used in localStorage (mapped to cookie for middleware access)
 *
 * Note: Next.js middleware runs on the edge and cannot access localStorage.
 * We need to check cookies instead. The authentication flow should also
 * set the token as a cookie for middleware to read.
 */
const SESSION_TOKEN_KEY = 'better-auth.session_token'

/**
 * Routes that require authentication
 */
const PROTECTED_ROUTES = ['/dashboard']

/**
 * Routes that should redirect to dashboard if already authenticated
 */
const AUTH_ROUTES = ['/login', '/signup']

/**
 * Middleware function to protect routes
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Get the session token from cookies
  // Note: The auth forms need to set this cookie in addition to localStorage
  const sessionToken = request.cookies.get(SESSION_TOKEN_KEY)?.value

  const isAuthenticated = !!sessionToken

  // Protect authenticated routes
  if (PROTECTED_ROUTES.some(route => pathname.startsWith(route))) {
    if (!isAuthenticated) {
      // Redirect to login if not authenticated
      const loginUrl = new URL('/login', request.url)
      loginUrl.searchParams.set('redirect', pathname)
      return NextResponse.redirect(loginUrl)
    }
  }

  // Redirect authenticated users away from auth pages
  if (AUTH_ROUTES.some(route => pathname.startsWith(route))) {
    if (isAuthenticated) {
      // Redirect to dashboard if already authenticated
      return NextResponse.redirect(new URL('/dashboard', request.url))
    }
  }

  // Allow the request to proceed
  return NextResponse.next()
}

/**
 * Configure which routes the middleware should run on
 */
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder (public files)
     */
    '/((?!api|_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
}
