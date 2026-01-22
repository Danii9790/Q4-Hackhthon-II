/**
 * Login page for Todo Application.
 *
 * This page renders the LoginForm component for user authentication.
 * Users can sign in with their email and password.
 */
import { Metadata } from 'next'
import LoginForm from '@/components/auth/LoginForm'

export const metadata: Metadata = {
  title: 'Sign In - Todo App',
  description: 'Sign in to your account to manage your tasks',
}

export default function LoginPage() {
  return <LoginForm />
}
