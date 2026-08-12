import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'

import { useAuth } from '@/context/AuthContext'
import { GoogleSignInButton } from '@/components/GoogleSignInButton'
import { PageHeader } from '@/components/PageHeader'
import { isAdminEmail } from '@/lib/admin'

export function RegisterPage() {
  const { register, isAuthenticated, isAdmin, isLoading } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (!isLoading && isAuthenticated) {
    return <Navigate to={isAdmin ? '/admin/ops' : '/chat'} replace />
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setIsSubmitting(true)
    try {
      await register(email, password)
      navigate(isAdminEmail(email) ? '/admin/ops' : '/chat')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="mx-auto max-w-md px-6 py-10">
      <PageHeader
        eyebrow="Account"
        title="Create account"
        description="Register to save repositories and chat history."
      />
      <form onSubmit={handleSubmit} className="ui-card space-y-4 rounded-2xl border border-white/10 p-6">
        {error ? <p className="text-sm text-red-300">{error}</p> : null}
        <GoogleSignInButton />
        <div className="relative py-1">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-white/10" />
          </div>
          <p className="relative text-center text-xs text-slate-500">or register with email</p>
        </div>
        <label className="block space-y-1">
          <span className="text-sm text-slate-300">Email</span>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-white"
          />
        </label>
        <label className="block space-y-1">
          <span className="text-sm text-slate-300">Password (min 8 characters)</span>
          <input
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-white"
          />
        </label>
        <button
          type="submit"
          disabled={isSubmitting}
          className="ui-button w-full rounded-lg bg-indigo-600 py-2 font-medium text-white hover:bg-indigo-500"
        >
          {isSubmitting ? 'Creating account…' : 'Register'}
        </button>
        <p className="text-center text-sm text-slate-400">
          Already have an account?{' '}
          <Link to="/login" className="text-indigo-300 hover:text-indigo-200">
            Sign in
          </Link>
        </p>
      </form>
    </div>
  )
}
