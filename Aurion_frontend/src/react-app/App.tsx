import { BrowserRouter as Router, Routes, Route } from "react-router";
import { AuthProvider } from '@/react-app/context/AuthContext';
import { AdminAuthProvider } from '@/react-app/context/AdminAuthContext';
import { TextSelectionProvider } from '@/react-app/context/TextSelectionContext';
import ProtectedRoute from '@/react-app/components/ProtectedRoute';
import HomePage from "@/react-app/pages/Home";
import ChatPage from "@/react-app/pages/ChatPage";
import AuthCallback from "@/react-app/pages/AuthCallback";
import TasksPage from "@/react-app/pages/TasksPage";
import ProfilePage from "@/react-app/pages/ProfilePage";
import SettingsPage from "@/react-app/pages/SettingsPage";
import HelpPage from "@/react-app/pages/HelpPage";
import AdminDashboard from "@/react-app/pages/admin/AdminDashboard";

export default function App() {
  return (
    <AuthProvider>
      <TextSelectionProvider>
        <Router>
          <Routes>
            {/* Public Routes */}
            <Route path="/" element={<HomePage />} />
            <Route path="/auth/callback" element={<AuthCallback />} />
            
            {/* Protected Routes */}
            <Route 
              path="/chat" 
              element={
                <ProtectedRoute>
                  <ChatPage />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/chat/:sessionId" 
              element={
                <ProtectedRoute>
                  <ChatPage />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/tasks" 
              element={
                <ProtectedRoute>
                  <TasksPage />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/profile" 
              element={
                <ProtectedRoute>
                  <ProfilePage />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/settings" 
              element={
                <ProtectedRoute>
                  <SettingsPage />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/help" 
              element={
                <ProtectedRoute>
                  <HelpPage />
                </ProtectedRoute>
              } 
            />
            
            {/* Admin Routes */}
            <Route 
              path="/admin/dashboard" 
              element={
                <AdminAuthProvider>
                  <AdminDashboard />
                </AdminAuthProvider>
              } 
            />
          </Routes>
        </Router>
      </TextSelectionProvider>
    </AuthProvider>
  );
}
