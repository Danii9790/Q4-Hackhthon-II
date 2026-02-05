/**
 * Sign Out Page
 *
 * Signs out the user and redirects to sign-in page.
 */

'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/router'
import { useAuth } from '@/hooks/useAuth'

/**
 * Sign out page component
 */
export default function SignOutPage() {
  const router = useRouter()
  const { signOut } = useAuth()

  useEffect(() => {
    async function handleSignOut() {
      await signOut()
      router.push('/signin')
    }

    handleSignOut()
  }, [signOut, router])

  return (
    <div className="flex items-center justify-center h-screen bg-gray-50 dark:bg-gray-950">
      <div className="text-center">
        <div className="inline-block h-12 w-12 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent align-[-0.125em]" />
        <p className="mt-4 text-gray-600 dark:text-gray-400">Signing out...</p>
      </div>
    </div>
  )
}
