import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { AdminLayout } from '@/components/admin/AdminLayout'
import { AppLayout } from '@/components/AppLayout'
import { OpsDashboardPage } from '@/pages/admin/OpsDashboardPage'
import { RetrievalLabPage } from '@/pages/admin/RetrievalLabPage'
import { ChatPage } from '@/pages/ChatPage'
import { HomePage } from '@/pages/HomePage'
import { RepositoriesPage } from '@/pages/RepositoriesPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/repositories" element={<RepositoriesPage />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/retrieval-lab" element={<Navigate to="/admin/retrieval-lab" replace />} />
        </Route>

        <Route path="/admin" element={<AdminLayout />}>
          <Route index element={<Navigate to="/admin/ops" replace />} />
          <Route path="ops" element={<OpsDashboardPage />} />
          <Route path="retrieval-lab" element={<RetrievalLabPage />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
