/**
 * Signup page for Todo Application.
 *
 * This page renders the SignupForm component for user registration.
 * New users can create an account with email, password, and optional name.
 */
import { Metadata } from 'next'
import SignupForm from '@/components/auth/SignupForm'

export const metadata: Metadata = {
  title: 'Sign Up - Todo App',
  description: 'Create a new account to start managing your tasks',
}

export default function SignupPage() {
  return <SignupForm />
}
