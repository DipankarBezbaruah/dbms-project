import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import SignIn from './pages/SignIn';
import StudentDashboard from './pages/StudentDashboard';
import WardenDashboard from './pages/WardenDashboard';
import MentorDashboard from './pages/MentorDashboard';
import HodDashboard from './pages/HodDashboard';
import SecurityDesk from './pages/SecurityDesk';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<SignIn />} />
        <Route path="/student/*" element={<StudentDashboard />} />
        <Route path="/warden/*" element={<WardenDashboard />} />
        <Route path="/mentor/*" element={<MentorDashboard />} />
        <Route path="/hod/*" element={<HodDashboard />} />
        <Route path="/security" element={<SecurityDesk />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
