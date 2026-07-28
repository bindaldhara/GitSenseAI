import { NavLink, Outlet } from 'react-router-dom'

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  [
    'rounded-lg px-3 py-2 text-sm font-medium transition',
    isActive
      ? 'bg-brand-600/20 text-brand-100'
      : 'text-slate-300 hover:bg-white/5 hover:text-white',
  ].join(' ')

export function AppLayout() {
  return (
    <div className="min-h-screen">
      <header className="border-b border-white/10 bg-black/20 backdrop-blur-sm">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-600 text-lg font-bold text-white">
              G
            </div>
            <div>
              <h1 className="text-xl font-semibold text-white">GitSense AI</h1>
              <p className="text-xs text-slate-400">Agentic Software Intelligence</p>
            </div>
          </div>

          <nav className="flex items-center gap-2">
            <NavLink to="/" end className={navLinkClass}>
              Home
            </NavLink>
            <NavLink to="/repositories" className={navLinkClass}>
              Repositories
            </NavLink>
          </nav>
        </div>
      </header>

      <Outlet />
    </div>
  )
}
