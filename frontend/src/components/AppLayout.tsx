import { FolderGit2, Home, LayoutDashboard, LogIn, LogOut, MessageSquare, Search } from 'lucide-react'
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'

import { useAuth } from '@/context/AuthContext'

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  ['nav-pill ui-button inline-flex items-center gap-2', isActive ? 'nav-pill-active' : ''].join(' ')

export function AppLayout() {
  const location = useLocation()
  const { isAuthenticated, user, logout, isLoading, isAdmin } = useAuth()

  return (
    <div className="app-shell min-h-screen">
      <header className="sticky top-0 z-50 border-b border-white/10 bg-[#070b14]/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-6 py-4">
          <Link to="/" className="group flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500 to-violet-600 text-lg font-bold text-white shadow-lg shadow-brand-600/30 transition group-hover:scale-105">
              G
            </div>
            <div>
              <h1 className="text-lg font-semibold text-white">GitSense AI</h1>
              <p className="text-xs text-slate-400">Agentic Software Intelligence</p>
            </div>
          </Link>

          <nav className="flex items-center gap-1 rounded-full border border-white/10 bg-white/5 p-1">
            <NavLink to="/" end className={navLinkClass}>
              <Home className="h-4 w-4" />
              Home
            </NavLink>
            <NavLink to="/repositories" className={navLinkClass}>
              <FolderGit2 className="h-4 w-4" />
              Repositories
            </NavLink>
            <NavLink to="/chat" className={navLinkClass}>
              <MessageSquare className="h-4 w-4" />
              Chat
            </NavLink>
            <NavLink to="/search" className={navLinkClass}>
              <Search className="h-4 w-4" />
              Search
            </NavLink>
            {isAdmin ? (
              <NavLink to="/admin/ops" className={navLinkClass}>
                <LayoutDashboard className="h-4 w-4" />
                Admin
              </NavLink>
            ) : null}
          </nav>

          <div className="flex items-center gap-2">
            {isLoading ? null : isAuthenticated ? (
              <>
                <span className="hidden text-xs text-slate-400 sm:inline">{user?.email}</span>
                <button
                  type="button"
                  onClick={logout}
                  className="ui-button inline-flex items-center gap-1.5 rounded-full border border-white/10 px-3 py-2 text-xs text-slate-300 hover:bg-white/5"
                >
                  <LogOut className="h-3.5 w-3.5" />
                  Log out
                </button>
              </>
            ) : (
              <NavLink to="/login" className={navLinkClass}>
                <LogIn className="h-4 w-4" />
                Sign in
              </NavLink>
            )}
          </div>
        </div>
      </header>

      <div key={location.pathname} className="page-enter">
        <Outlet />
      </div>
    </div>
  )
}
