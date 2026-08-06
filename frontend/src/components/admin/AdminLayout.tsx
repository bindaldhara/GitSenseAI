import { Activity, ArrowLeft, Database, FlaskConical, LayoutDashboard, Network } from 'lucide-react'
import { Link, NavLink, Outlet } from 'react-router-dom'

const adminNavClass = ({ isActive }: { isActive: boolean }) =>
  [
    'flex items-center gap-2 rounded-xl px-3 py-2.5 text-sm font-medium transition',
    isActive
      ? 'bg-brand-500/15 text-brand-100 ring-1 ring-brand-400/30'
      : 'text-slate-400 hover:bg-white/5 hover:text-white',
  ].join(' ')

export function AdminLayout() {
  return (
    <div className="min-h-screen bg-[#05080f]">
      <header className="border-b border-white/10 bg-[#070b14]/90 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-violet-600/20 text-violet-200">
              <Activity className="h-4 w-4" />
            </div>
            <div>
              <p className="text-xs uppercase tracking-wider text-slate-500">Internal</p>
              <h1 className="text-lg font-semibold text-white">GitSense Admin</h1>
            </div>
          </div>
          <Link to="/" className="ui-button inline-flex items-center gap-2 text-sm text-slate-300 hover:text-white">
            <ArrowLeft className="h-4 w-4" />
            Back to app
          </Link>
        </div>
      </header>

      <div className="mx-auto grid max-w-6xl gap-8 px-6 py-8 lg:grid-cols-[220px_1fr]">
        <aside className="glass-panel h-fit rounded-2xl p-3">
          <p className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
            Admin tools
          </p>
          <nav className="space-y-1">
            <NavLink to="/admin/ops" className={adminNavClass}>
              <LayoutDashboard className="h-4 w-4" />
              Ops dashboard
            </NavLink>
            <NavLink to="/admin/retrieval-lab" className={adminNavClass}>
              <FlaskConical className="h-4 w-4" />
              Retrieval lab
            </NavLink>
            <NavLink to="/admin/graph-rag-lab" className={adminNavClass}>
              <Network className="h-4 w-4" />
              Graph RAG lab
            </NavLink>
            <NavLink to="/admin/cache" className={adminNavClass}>
              <Database className="h-4 w-4" />
              Cache analytics
            </NavLink>
          </nav>
        </aside>

        <div className="min-w-0">
          <Outlet />
        </div>
      </div>
    </div>
  )
}
