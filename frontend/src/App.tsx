import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAuthStore } from './store/authStore'
import AppLayout from './components/layout/AppLayout'
import LoginPage from './pages/LoginPage'
import ProjectsPage from './pages/ProjectsPage'
import QueryPage from './pages/QueryPage'

const queryClient = new QueryClient()

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.accessToken)
  return token ? <>{children}</> : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={
            <PrivateRoute>
              <AppLayout />
            </PrivateRoute>
          }>
            <Route path="/" element={<ProjectsPage />} />
            <Route path="/projects/:projectId" element={<QueryPage />} />
            <Route path="/settings" element={<div className="p-8 text-gray-500">Settings coming soon</div>} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}