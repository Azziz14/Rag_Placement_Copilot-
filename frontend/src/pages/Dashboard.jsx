import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { progressApi, adaptiveApi } from '../services/api';
import { ScoreMeter, ResumeTimeline } from '../components/VisualElements';
import { 
  FileText, 
  Briefcase, 
  GitCompare, 
  AlertTriangle, 
  TrendingUp, 
  Play, 
  RefreshCw, 
  Sparkles, 
  CheckCircle,
  HelpCircle,
  Award,
  BookOpen
} from 'lucide-react';

const Dashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [adaptiveProfile, setAdaptiveProfile] = useState(null);
  const [history, setHistory] = useState({ jd_scores: [], session_scores: [] });
  const [loading, setLoading] = useState(true);
  const [loopLoading, setLoopLoading] = useState(false);
  const [loopSuccess, setLoopSuccess] = useState(false);
  const [loopError, setLoopError] = useState(null);
  const [error, setError] = useState(null);

  const fetchDashboardData = async () => {
    if (!user?.id) return;
    try {
      setLoading(true);
      setError(null);
      const res = await progressApi.getDashboard(user.id);
      setData(res);
      
      // Fetch history versions
      try {
        const histRes = await progressApi.getHistory(user.id);
        if (histRes) {
          setHistory(histRes);
        }
      } catch (histErr) {
        console.warn("Could not load history versions.", histErr);
      }

      // Fetch adaptive profile
      try {
        const adRes = await adaptiveApi.generateProfile(user.id);
        setAdaptiveProfile(adRes);
      } catch (adErr) {
        console.warn("Could not load adaptive profile yet, user might have no history.", adErr);
      }
    } catch (err) {
      setError(err.response?.data?.detail || "You need to upload a resume and JD, then complete at least one mock interview to view analytics.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user?.id) {
      fetchDashboardData();
    }
  }, [user?.id]);

  const handleTriggerLoop = async () => {
    if (!user?.id) return;
    setLoopError(null);
    setLoopSuccess(false);
    try {
      setLoopLoading(true);
      const res = await adaptiveApi.generateProfile(user.id, true);
      setAdaptiveProfile(res);
      setLoopSuccess(true);
      setTimeout(() => setLoopSuccess(false), 4000);
    } catch (err) {
      setLoopError(err.response?.data?.detail || 'Failed to generate adaptive profile.');
      setTimeout(() => setLoopError(null), 5000);
    } finally {
      setLoopLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 className="title-gradient" style={{ fontSize: '2.5rem', fontFamily: 'var(--font-heading)', fontWeight: '800' }}>
            Welcome, {user?.user_metadata?.full_name || 'Candidate'}
          </h1>
          <p className="subtitle">Here is your personal career intelligence dashboard.</p>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.5rem' }}>
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button 
              onClick={handleTriggerLoop} 
              className="btn-secondary" 
              style={{ color: 'var(--accent-light)', borderColor: 'var(--accent-glow)', position: 'relative' }}
              disabled={loopLoading}
            >
              <Sparkles size={16} style={{ animation: loopLoading ? 'spin 1s linear infinite' : 'none' }} />
              <span>{loopLoading ? 'Regenerating...' : 'Generate Adaptive Profile'}</span>
            </button>
            <Link to="/upload-resume" className="btn-primary">
              <Play size={16} />
              <span>Practice Session</span>
            </Link>
          </div>
          {loopSuccess && (
            <span style={{ fontSize: '0.8rem', color: 'var(--success)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <CheckCircle size={13} /> Profile regenerated successfully!
            </span>
          )}
          {loopError && (
            <span style={{ fontSize: '0.8rem', color: 'var(--danger)', fontWeight: 600 }}>
              ⚠ {loopError}
            </span>
          )}
        </div>
      </div>

      {error ? (
        <div className="glass-card" style={{ textAlign: 'center', padding: '3.5rem 2rem', border: '1px solid rgba(99, 102, 241, 0.15)' }}>
          <HelpCircle size={48} style={{ color: 'var(--accent-light)', marginBottom: '1.25rem' }} />
          <h3 style={{ marginBottom: '0.5rem', fontSize: '1.25rem' }}>Get Started with InterviewPilot AI</h3>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem', maxWidth: '500px', margin: '0 auto 2rem', fontSize: '0.95rem', lineHeight: '1.5' }}>
            Upload your resume and target job description to unlock your personalized analysis. Mock interviews and practice sessions will enrich the intelligence center.
          </p>
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
            <Link to="/upload-resume" className="btn-primary">
              Upload Resume
            </Link>
            <Link to="/upload-jd" className="btn-secondary">
              Upload Job Description
            </Link>
          </div>
        </div>
      ) : (
        <>
          {/* Top Level Cards */}
          <div className="grid-3">
            <div className="glass-card" style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
              <ScoreMeter score={data?.overall_progress || 0} size={85} strokeWidth={8} />
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 700 }}>
                  Overall Progress
                </span>
                <h3 style={{ fontSize: '1.5rem', fontWeight: 800, marginTop: '0.25rem' }}>Mastery Level</h3>
                <span className="badge badge-primary" style={{ marginTop: '0.5rem' }}>Live profile</span>
              </div>
            </div>

            <div className="glass-card" style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
              <ScoreMeter score={data?.roadmap_completion?.completion_percentage || 0} size={85} strokeWidth={8} />
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 700 }}>
                  Roadmap Completion
                </span>
                <h3 style={{ fontSize: '1.5rem', fontWeight: 800, marginTop: '0.25rem' }}>
                  {data?.roadmap_completion?.completed_goals} / {data?.roadmap_completion?.total_goals} Goals
                </h3>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block', marginTop: '0.25rem' }}>Achieved objectives</span>
              </div>
            </div>

            <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 700 }}>
                  Active Focus Areas
                </span>
                <AlertTriangle size={18} style={{ color: 'var(--danger)' }} />
              </div>
              <h2 style={{ fontSize: '2.2rem', fontWeight: 800 }}>{data?.persistent_weaknesses?.length}</h2>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Key weaknesses remaining</span>
            </div>
          </div>

          {/* Main Dashboard Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.25rem' }} className="grid-2">
            
            {/* Left Side: Loop Plan & Focus */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              {adaptiveProfile && (
                <div className="glass-card" style={{ border: '1px solid rgba(99, 102, 241, 0.15)', background: 'rgba(21, 27, 44, 0.6)' }}>
                  <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginBottom: '1.25rem' }}>
                    <Sparkles size={20} style={{ color: 'var(--accent-light)' }} />
                    <h3 style={{ fontSize: '1.2rem' }}>Adaptive Interview Loop Plan</h3>
                  </div>
                  
                  <div className="grid-2">
                    <div>
                      <h4 style={{ color: 'var(--accent-light)', marginBottom: '0.75rem', fontSize: '0.95rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Next Focus Areas</h4>
                      <ul style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem', listStyle: 'none' }}>
                        {adaptiveProfile.next_focus_areas.map((f, i) => (
                          <li key={i} style={{ background: 'rgba(255, 255, 255, 0.01)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                              <strong style={{ color: '#ffffff', fontSize: '0.9rem' }}>{f.area}</strong>
                              <span className={`badge ${f.priority === 'High' ? 'badge-danger' : 'badge-warning'}`}>{f.priority}</span>
                            </div>
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{f.reason}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                      <div>
                        <h4 style={{ color: 'var(--accent-light)', marginBottom: '0.5rem', fontSize: '0.95rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Adjustments</h4>
                        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                          {adaptiveProfile.difficulty_adjustments.map((d, i) => (
                            <div key={i} style={{ background: 'rgba(0, 0, 0, 0.15)', padding: '0.4rem 0.6rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', fontSize: '0.8rem' }}>
                              <span style={{ textTransform: 'capitalize', color: 'var(--text-secondary)' }}>{d.section}: </span>
                              <strong style={{ color: '#ffffff' }}>{d.level}</strong>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div>
                        <h4 style={{ color: 'var(--accent-light)', marginBottom: '0.5rem', fontSize: '0.95rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Recommended Track</h4>
                        <p style={{ background: 'rgba(99, 102, 241, 0.04)', border: '1px solid rgba(99, 102, 241, 0.1)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', color: '#ffffff', fontWeight: 'bold', fontSize: '0.9rem' }}>
                          {adaptiveProfile.recommended_interview_type}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Weaknesses and Improvements */}
              <div className="grid-2">
                <div className="glass-card">
                  <h3 style={{ marginBottom: '1rem', display: 'flex', gap: '0.5rem', alignItems: 'center', fontSize: '1.05rem' }}>
                    <AlertTriangle size={16} style={{ color: 'var(--danger)' }} />
                    <span>Focus Weaknesses</span>
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {data?.persistent_weaknesses?.length > 0 ? (
                      data.persistent_weaknesses.map((w, i) => (
                        <div key={i} style={{ padding: '0.6rem 0.75rem', background: 'rgba(239, 68, 68, 0.02)', border: '1px solid rgba(239, 68, 68, 0.08)', borderRadius: 'var(--radius-sm)', fontSize: '0.85rem' }}>
                          {w}
                        </div>
                      ))
                    ) : (
                      <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>No weaknesses detected.</p>
                    )}
                  </div>
                </div>

                <div className="glass-card">
                  <h3 style={{ marginBottom: '1rem', display: 'flex', gap: '0.5rem', alignItems: 'center', fontSize: '1.05rem' }}>
                    <CheckCircle size={16} style={{ color: 'var(--success)' }} />
                    <span>Improved Competencies</span>
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {data?.improved_areas?.length > 0 ? (
                      data.improved_areas.map((a, i) => (
                        <div key={i} style={{ padding: '0.6rem 0.75rem', background: 'rgba(16, 185, 129, 0.02)', border: '1px solid rgba(16, 185, 129, 0.08)', borderRadius: 'var(--radius-sm)', fontSize: '0.85rem' }}>
                          {a}
                        </div>
                      ))
                    ) : (
                      <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Keep practicing to show improvements!</p>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Right Side: Tailored Resumes History */}
            <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                <FileText size={18} style={{ color: 'var(--accent)' }} />
                <h3 style={{ fontSize: '1.1rem' }}>Tailoring History</h3>
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Historical matching and tailored resume variations:</p>
              <ResumeTimeline 
                versions={history?.jd_scores || []} 
                onSelect={(v) => navigate('/match-analysis')} 
              />
            </div>

          </div>
        </>
      )}
    </div>
  );
};

export default Dashboard;
