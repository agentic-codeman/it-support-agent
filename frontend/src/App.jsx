import { Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import KnowledgeListPage from './pages/KnowledgeListPage'
import KnowledgeDocumentsPage from './pages/KnowledgeDocumentsPage'
import KnowledgeChunksPage from './pages/KnowledgeChunksPage'
import ChatPage from './pages/ChatPage'
import TicketSubmissionPage from './pages/TicketSubmissionPage'
import { useAuthStore } from './store/authStore'

// Admin Layout and Pages
import AdminLayout from './components/AdminLayout'
import AdminKnowledgeBasePage from './pages/admin/KnowledgeBasePage'
import AdminIntentTreePage from './pages/admin/IntentTreePage'
import AdminIntentListPage from './pages/admin/IntentListPage'
import AdminKeywordMappingPage from './pages/admin/KeywordMappingPage'
import AdminUsersPage from './pages/admin/UsersPage'
import AdminSampleQuestionsPage from './pages/admin/SampleQuestionsPage'
import AdminSettingsPage from './pages/admin/SettingsPage'

function App() {
  const { isAuthenticated } = useAuthStore()

  return (
    <Routes>
      <Route path="/" element={
        isAuthenticated ? <Navigate to="/chat" replace /> : <Navigate to="/login" />
      } />
      <Route path="/login" element={
        isAuthenticated ? <Navigate to="/chat" /> : <Login />
      } />
      <Route path="/register" element={
        isAuthenticated ? <Navigate to="/chat" /> : <Register />
      } />
      <Route path="/dashboard" element={
        isAuthenticated ? <Dashboard /> : <Navigate to="/login" />
      } />
      <Route path="/chat" element={
        isAuthenticated ? <ChatPage /> : <Navigate to="/login" />
      } />
      <Route path="/ticket" element={
        isAuthenticated ? <TicketSubmissionPage /> : <Navigate to="/login" />
      } />
      <Route path="/admin" element={
        isAuthenticated ? <AdminLayout /> : <Navigate to="/login" />
      }>
        <Route index element={<Navigate to="/admin/knowledge" replace />} />
        <Route path="knowledge" element={<AdminKnowledgeBasePage />} />
        <Route path="knowledge/:id" element={<KnowledgeDocumentsPage />} />
        <Route path="knowledge/:kbId/doc/:docId/chunks" element={<KnowledgeChunksPage />} />
        <Route path="intent-tree" element={<AdminIntentTreePage />} />
        <Route path="intent-list" element={<AdminIntentListPage />} />
        <Route path="mappings" element={<AdminKeywordMappingPage />} />
        <Route path="users" element={<AdminUsersPage />} />
        <Route path="sample-questions" element={<AdminSampleQuestionsPage />} />
        <Route path="settings" element={<AdminSettingsPage />} />
      </Route>
      
      <Route path="*" element={
        isAuthenticated ? <Navigate to="/chat" /> : <Navigate to="/login" />
      } />
    </Routes>
  )
}

export default App
