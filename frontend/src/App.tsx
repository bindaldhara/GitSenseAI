import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { AdminLayout } from '@/components/admin/AdminLayout'
import { AppLayout } from '@/components/AppLayout'
import { AuthProvider } from '@/context/AuthContext'
import { CacheAnalyticsPage } from '@/pages/admin/CacheAnalyticsPage'
import { GraphRagLabPage } from '@/pages/admin/GraphRagLabPage'
import { OpsDashboardPage } from '@/pages/admin/OpsDashboardPage'
import { RetrievalLabPage } from '@/pages/admin/RetrievalLabPage'
import { ChatPage } from '@/pages/ChatPage'
import { HomePage } from '@/pages/HomePage'
import { LoginPage } from '@/pages/LoginPage'
import { RegisterPage } from '@/pages/RegisterPage'
import { RepositoriesPage } from '@/pages/RepositoriesPage'
import { SearchPage } from '@/pages/SearchPage'

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="/" element={<HomePage />} />
            <Route path="/repositories" element={<RepositoriesPage />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/retrieval-lab" element={<Navigate to="/admin/retrieval-lab" replace />} />
          </Route>

          <Route path="/admin" element={<AdminLayout />}>
            <Route index element={<Navigate to="/admin/ops" replace />} />
            <Route path="ops" element={<OpsDashboardPage />} />
            <Route path="retrieval-lab" element={<RetrievalLabPage />} />
            <Route path="graph-rag-lab" element={<GraphRagLabPage />} />
            <Route path="cache" element={<CacheAnalyticsPage />} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
