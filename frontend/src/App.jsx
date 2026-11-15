import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './AuthContext';
import SignIn from './pages/SignIn';
import StudentDashboard from './pages/StudentDashboard';
import WardenDashboard from './pages/WardenDashboard';
import MentorDashboard from './pages/MentorDashboard';
import HodDashboard from './pages/HodDashboard';
import SecurityDesk from './pages/SecurityDesk';
import AdminDashboard from './pages/AdminDashboard';

/**
 * Route guard: only renders children if the user is logged in
 * with the required role. Otherwise redirects to sign-in.
 */
function ProtectedRoute({ role, children }) {
  const { user, loading } = useAuth();

  if (loading) return <div className="loading">Loading...</div>;
  if (!user) return <Navigate to="/" replace />;
  if (role && user.role !== role) return <Navigate to="/" replace />;

  return children;
}

function AppRoutes() {
  const { user, loading } = useAuth();

  if (loading) return <div className="loading">Loading...</div>;

  return (
    <Routes>
      {/* Sign-in: redirect to dashboard if already logged in */}
      <Route
        path="/"
        element={
          user ? <Navigate to={`/${user.role.toLowerCase()}`} replace /> : <SignIn />
        }
      />

      <Route
        path="/student/*"
        element={
          <ProtectedRoute role="Student">
            <StudentDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/warden/*"
        element={
          <ProtectedRoute role="Warden">
            <WardenDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/mentor/*"
        element={
          <ProtectedRoute role="Mentor">
            <MentorDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/hod/*"
        element={
          <ProtectedRoute role="HOD">
            <HodDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/security"
        element={
          <ProtectedRoute role="Security">
            <SecurityDesk />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/*"
        element={
          <ProtectedRoute role="Admin">
            <AdminDashboard />
          </ProtectedRoute>
        }
      />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
