import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'

import { fetchCurrentUser } from '@/api/auth'
import { isAdminEmail } from '@/lib/admin'
import { supabase } from '@/lib/supabase'
import type { User } from '@/types/auth'

type AuthContextValue = {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  isAdmin: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string) => Promise<void>
  loginWithGoogle: () => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

async function loadAppUser(): Promise<User | null> {
  const { data } = await supabase.auth.getSession()
  if (!data.session) {
    return null
  }
  return fetchCurrentUser()
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const navigate = useNavigate()
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let active = true

    void loadAppUser()
      .then((appUser) => {
        if (active) {
          setUser(appUser)
        }
      })
      .finally(() => {
        if (active) {
          setIsLoading(false)
        }
      })

    const { data: authListener } = supabase.auth.onAuthStateChange((_event, session) => {
      if (!session) {
        setUser(null)
        return
      }
      void fetchCurrentUser()
        .then((appUser) => setUser(appUser))
        .catch(async () => {
          await supabase.auth.signOut()
          setUser(null)
        })
    })

    return () => {
      active = false
      authListener.subscription.unsubscribe()
    }
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const { data, error } = await supabase.auth.signInWithPassword({ email, password })
    if (error) {
      throw error
    }
    if (!data.session) {
      throw new Error('Sign-in succeeded but no session was returned.')
    }
    try {
      const appUser = await fetchCurrentUser()
      setUser(appUser)
    } catch (meError) {
      await supabase.auth.signOut()
      throw meError instanceof Error
        ? new Error(`Signed in with Supabase but the API rejected the token: ${meError.message}`)
        : meError
    }
  }, [])

  const register = useCallback(async (email: string, password: string) => {
    const { data, error } = await supabase.auth.signUp({ email, password })
    if (error) {
      throw error
    }
    if (!data.session) {
      throw new Error('Check your email to confirm your account, then sign in.')
    }
    const appUser = await fetchCurrentUser()
    setUser(appUser)
  }, [])

  const loginWithGoogle = useCallback(async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/login`,
      },
    })
    if (error) {
      throw error
    }
  }, [])

  const logout = useCallback(async () => {
    await supabase.auth.signOut()
    setUser(null)
    navigate('/', { replace: true })
  }, [navigate])

  const value = useMemo(
    () => ({
      user,
      isLoading,
      isAuthenticated: Boolean(user),
      isAdmin: Boolean(user && isAdminEmail(user.email)),
      login,
      register,
      loginWithGoogle,
      logout,
    }),
    [user, isLoading, login, register, loginWithGoogle, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
