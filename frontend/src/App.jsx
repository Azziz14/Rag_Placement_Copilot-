import React from 'react';
import { BrowserRouter, Routes, Route, Outlet } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Navbar from './components/Navbar';

// Pages
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import ResumeUpload from './pages/ResumeUpload';
import JDUpload from './pages/JDUpload';
import MatchAnalysis from './pages/MatchAnalysis';
import InterviewSession from './pages/InterviewSession';
import EvaluationResults from './pages/EvaluationResults';
import Roadmap from './pages/Roadmap';
import ProgressAnalytics from './pages/ProgressAnalytics';
import LearningHub from './pages/LearningHub';

// Private Layout wrapping Protected routes with Sidebar Navbar
const AppLayout = () => {
  return (
    <div className="app-container">
      <Navbar />
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
};

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Login Route */}
          <Route path="/login" element={<Login />} />

          {/* Protected Main Routes */}
          <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/upload-resume" element={<ResumeUpload />} />
            <Route path="/upload-jd" element={<JDUpload />} />
            <Route path="/match-analysis" element={<MatchAnalysis />} />
            <Route path="/interview-session" element={<InterviewSession />} />
            <Route path="/evaluation-results/:sessionId" element={<EvaluationResults />} />
            <Route path="/roadmap/:sessionId" element={<Roadmap />} />
            <Route path="/progress-analytics" element={<ProgressAnalytics />} />
            <Route path="/learning-hub" element={<LearningHub />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
