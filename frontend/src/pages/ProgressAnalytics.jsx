import React, { useEffect, useState } from 'react';
import { progressApi, adaptiveApi } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { ScoreMeter } from '../components/VisualElements';
import { TrendingUp, Sparkles, RefreshCw, BarChart2, Star, Briefcase, ClipboardList } from 'lucide-react';

const ProgressAnalytics = () => {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [history, setHistory] = useState({ jd_scores: [], session_scores: [] });
  const [adaptiveProfile, setAdaptiveProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loopLoading, setLoopLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchAnalyticsData = async () => {
    if (!user?.id) return;
    try {
      setLoading(true);
      setError(null);
      
      const progressRes = await progressApi.getDashboard(user.id);
      setData(progressRes);

      const historyRes = await progressApi.getHistory(user.id);
      setHistory(historyRes);

      try {
        const adRes = await adaptiveApi.generateProfile(user.id);
        setAdaptiveProfile(adRes);
      } catch (profileErr) {
        setAdaptiveProfile(null);
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Make sure you have completed at least one mock interview session before viewing analytics.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user?.id) {
      fetchAnalyticsData();
    }
  }, [user?.id]);

  const handleUpdateLoop = async () => {
    if (!user?.id) return;
    try {
      setLoopLoading(true);
      const res = await adaptiveApi.generateProfile(user.id);
      setAdaptiveProfile(res);
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to regenerate adaptive profile loop.");
    } finally {
      setLoopLoading(false);
    }
  };

  const formatDate = (value) => {
    if (!value) return 'N/A';
    return new Date(value).toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const scoreColor = (score) => {
    if (score >= 80) return 'var(--success)';
    if (score >= 60) return 'var(--accent-light)';
    if (score >= 40) return 'var(--warning)';
    return 'var(--danger)';
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
        <div className="spinner"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-card" style={{ textAlign: 'center', padding: '3.5rem 2rem', maxWidth: '600px', margin: '3rem auto' }}>
        <BarChart2 size={44} style={{ color: 'var(--danger)', marginBottom: '1.25rem' }} />
        <h3 style={{ marginBottom: '0.75rem', fontSize: '1.2rem' }}>No Analytics Found</h3>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem', fontSize: '0.9rem', lineHeight: '1.5' }}>{error}</p>
        <button onClick={fetchAnalyticsData} className="btn-primary">
          <RefreshCw size={14} />
          <span>Retry Loading</span>
        </button>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1.5rem' }}>
        <div>
          <h1 className="title-gradient" style={{ fontSize: '2.5rem', fontFamily: 'var(--font-heading)', fontWeight: '800' }}>
            Analytics & Loop
          </h1>
          <p className="subtitle">Chronological trend analysis and dynamic interface adaptation profile.</p>
        </div>
        
        <button 
          onClick={handleUpdateLoop} 
          className="btn-primary" 
          disabled={loopLoading}
          style={{ gap: '0.5rem' }}
        >
          <RefreshCw size={14} className={loopLoading ? "spinner" : ""} />
          <span>Regenerate Loop Profile</span>
        </button>
      </div>

      {/* Main Score Over Time Graph */}
      <div className="glass-card">
        <h3 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '1.1rem' }}>
          <TrendingUp size={18} style={{ color: 'var(--accent-light)' }} />
          <span>Chronological Score Trend</span>
        </h3>
        
        {data.score_trend?.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div style={{
              display: 'flex',
              alignItems: 'flex-end',
              justifyContent: 'space-around',
              height: '240px',
              padding: '1.5rem 0',
              borderBottom: '1px solid var(--border)',
              background: 'rgba(0,0,0,0.15)',
              borderRadius: 'var(--radius-sm)',
              position: 'relative'
            }}>
              {data.score_trend.map((point, index) => (
                <div key={index} style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  width: '60px',
                  height: '100%',
                  justifyContent: 'flex-end'
                }}>
                  <div style={{
                    height: `${point.average_score}%`,
                    width: '28px',
                    background: 'linear-gradient(to top, var(--accent), var(--accent-light))',
                    borderRadius: '4px 4px 0 0',
                    boxShadow: '0 0 10px var(--accent-glow)',
                    display: 'flex',
                    alignItems: 'flex-start',
                    justifyContent: 'center',
                    paddingTop: '0.4rem',
                    transition: 'all 0.5s ease-out'
                  }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 'bold', color: '#ffffff' }}>
                      {Math.round(point.average_score)}
                    </span>
                  </div>
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: '0.5rem', overflow: 'hidden', maxWidth: '100%', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    Session {index + 1}
                  </span>
                </div>
              ))}
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textAlign: 'center' }}>
              Horizontal Axis: Chronological Session Sequence | Vertical Axis: Average Evaluation Score (%)
            </p>
          </div>
        ) : (
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Complete multiple interviews to build your trend chart.</p>
        )}
      </div>

      <div className="grid-2">
        <div className="glass-card">
          <h3 style={{ marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '1.1rem' }}>
            <Briefcase size={18} style={{ color: 'var(--teal)' }} />
            <span>JD Score History</span>
          </h3>

          {history.jd_scores?.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {history.jd_scores.map((item) => (
                <div key={item.match_id} style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: '1rem', alignItems: 'center', padding: '1rem', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', background: 'rgba(255,255,255,0.02)' }}>
                  <div style={{ minWidth: 0 }}>
                    <strong style={{ color: '#ffffff', display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: '0.9rem' }}>
                      {item.job_title || 'Untitled JD'}
                    </strong>
                    <span style={{ color: 'var(--text-secondary)', fontSize: '0.75rem' }}>
                      {item.company_name || 'Company not specified'} | {formatDate(item.created_at)}
                    </span>
                    <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', marginTop: '0.5rem' }}>
                      <span className="badge badge-success">{item.matched_skills_count} matched</span>
                      <span className="badge badge-warning">{item.missing_skills_count} gaps</span>
                    </div>
                  </div>
                  <div style={{ color: scoreColor(item.match_score), fontSize: '1.5rem', fontWeight: 800, fontFamily: 'var(--font-heading)' }}>
                    {Math.round(item.match_score)}%
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Analyze resumes against job descriptions to build JD score history.</p>
          )}
        </div>

        <div className="glass-card">
          <h3 style={{ marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '1.1rem' }}>
            <ClipboardList size={18} style={{ color: 'var(--accent-light)' }} />
            <span>Previous Session Scores</span>
          </h3>

          {history.session_scores?.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {history.session_scores.map((item) => (
                <div key={item.session_id} style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: '1rem', alignItems: 'center', padding: '1rem', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', background: 'rgba(255,255,255,0.02)' }}>
                  <div style={{ minWidth: 0 }}>
                    <strong style={{ color: '#ffffff', display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: '0.9rem' }}>
                      {item.job_title || 'Interview Session'}
                    </strong>
                    <span style={{ color: 'var(--text-secondary)', fontSize: '0.75rem' }}>
                      {item.company_name || 'Company not specified'} | {formatDate(item.started_at)}
                    </span>
                    <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', marginTop: '0.5rem' }}>
                      <span className={item.status === 'completed' ? 'badge badge-success' : 'badge badge-primary'}>{item.status}</span>
                      <span className="badge badge-primary">{item.evaluation_count} evaluated</span>
                    </div>
                  </div>
                  <div style={{ color: scoreColor(item.average_score), fontSize: '1.5rem', fontWeight: 800, fontFamily: 'var(--font-heading)' }}>
                    {Math.round(item.average_score)}%
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Complete practice interviews to build previous session score history.</p>
          )}
        </div>
      </div>

      {/* Adaptive loop recommendations */}
      {adaptiveProfile && (
        <div className="glass-card" style={{ border: '1px solid var(--border-active)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.25rem' }}>
            <Sparkles size={18} style={{ color: 'var(--accent-light)' }} />
            <h3 style={{ fontSize: '1.25rem' }}>Next Session Recommendations</h3>
          </div>
          
          <div className="grid-2">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <h4 style={{ color: 'var(--text-primary)', borderBottom: '1px solid var(--border)', paddingBottom: '0.4rem', fontSize: '0.95rem' }}>Target focus areas</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                {adaptiveProfile.next_focus_areas.map((f, i) => (
                  <div key={i} style={{ background: 'rgba(255, 255, 255, 0.01)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                      <strong style={{ color: '#ffffff', fontSize: '0.85rem' }}>{f.area}</strong>
                      <span className={`badge ${f.priority === 'High' ? 'badge-danger' : 'badge-warning'}`}>{f.priority}</span>
                    </div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{f.reason}</span>
                  </div>
                ))}
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <h4 style={{ color: 'var(--text-primary)', borderBottom: '1px solid var(--border)', paddingBottom: '0.4rem', fontSize: '0.95rem' }}>Target Questions & Templates</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                {adaptiveProfile.priority_questions.map((q, i) => (
                  <div key={i} style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', background: 'rgba(255, 255, 255, 0.01)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
                    <Star size={12} style={{ color: 'var(--warning)', flexShrink: 0 }} />
                    <div style={{ flex: 1 }}>
                      <strong style={{ color: '#ffffff', fontSize: '0.85rem', display: 'block' }}>{q.topic}</strong>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                        Category: {q.category} | Complexity: {q.recommended_complexity}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProgressAnalytics;
