/**
 * Authentication middleware for protected routes.
 *
 * This middleware checks if a user is authenticated before allowing access
 * to protected routes. If not authenticated, redirects to the login page.
 *
 * Protected routes:
 * - /dashboard
 * - /tasks
 * - /profile
 *
 * Public routes:
 * - / (landing page)
 * - /login
 * - /signup
 * - /forgot-password
 * - /reset-password
 */
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/**
 * Protected routes that require authentication.
 */
const PROTECTED_ROUTES = ['/dashboard', '/tasks', '/profile'];

/**
 * Public routes that should redirect to dashboard if already authenticated.
 */
const PUBLIC_ROUTES = ['/login', '/signup'];

/**
 * Get the token from the request cookies.
 *
 * @param request - Next.js request object
 * @returns JWT token or null
 */
function getTokenFromRequest(request: NextRequest): string | null {
  // Check for token in cookie (set by auth utilities)
  const token = request.cookies.get('better-auth.session_token')?.value;
  return token || null;
}

/**
 * Middleware function to protect routes.
 *
 * @param request - Next.js request object
 * @returns NextResponse with redirect if needed
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Get token from request
  const token = getTokenFromRequest(request);
  const isAuthenticated = !!token;

  // Check if current path is a protected route
  const isProtectedRoute = PROTECTED_ROUTES.some((route) =>
    pathname.startsWith(route)
  );

  // Check if current path is a public route
  const isPublicRoute = PUBLIC_ROUTES.some((route) => pathname.startsWith(route));

  // Redirect unauthenticated users from protected routes to login
  if (isProtectedRoute && !isAuthenticated) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('redirect', pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Redirect authenticated users from public routes to dashboard
  if (isPublicRoute && isAuthenticated) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  // Allow request to proceed
  return NextResponse.next();
}

/**
 * Matcher configuration for middleware.
 *
 * This ensures the middleware runs on all routes except:
 * - API routes (handled by backend)
 * - Static files (images, fonts, etc.)
 * - Next.js internals (_next, _vercel)
 */
export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder files
     */
    '/((?!api|_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
};
