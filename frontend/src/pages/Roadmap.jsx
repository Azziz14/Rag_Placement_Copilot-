import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { roadmapApi } from '../services/api';
import { Map, ArrowRight, LayoutDashboard, Bookmark, ExternalLink } from 'lucide-react';

const Roadmap = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const [roadmap, setRoadmap] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchRoadmap = async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await roadmapApi.generate(sessionId);
        setRoadmap(res);
      } catch (err) {
        setError(err.response?.data?.detail || "Could not retrieve roadmap details.");
      } finally {
        setLoading(false);
      }
    };

    fetchRoadmap();
  }, [sessionId]);

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
        <div className="spinner"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-card" style={{ textAlign: 'center', padding: '3rem', maxWidth: '600px', margin: '2rem auto' }}>
        <Map size={48} style={{ color: 'var(--danger)', marginBottom: '1rem' }} />
        <h3 style={{ marginBottom: '1rem' }}>Roadmap Not Available</h3>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>{error}</p>
        <button onClick={() => navigate('/')} className="btn-primary">Return to Dashboard</button>
      </div>
    );
  }

  const renderPlan = (plan, title) => {
    if (!plan || plan.length === 0) return null;
    return (
      <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <h3 style={{ color: 'var(--accent-light)', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>
          {title}
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {plan.map((item, index) => (
            <div key={index} style={{ background: 'rgba(255,255,255,0.01)', border: '1px solid var(--border)', padding: '1rem', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                <span className="badge badge-primary">{item.term || item.priority || 'Short Term'}</span>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Goal {index + 1}</span>
              </div>
              <strong style={{ display: 'block', color: '#ffffff', marginBottom: '0.25rem' }}>
                {item.goal || item.title || item}
              </strong>
              {item.action_steps && (
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                  {item.action_steps}
                </p>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1.5rem' }}>
        <div>
          <h1 className="title-gradient" style={{ fontSize: '2.5rem', fontFamily: 'var(--font-heading)' }}>
            Personalized Improvement Roadmap
          </h1>
          <p className="subtitle">Prioritized study roadmap based on your weaknesses and matching requirements.</p>
        </div>
        
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button onClick={() => navigate('/')} className="btn-secondary">
            <LayoutDashboard size={16} />
            <span>Dashboard</span>
          </button>
          
          <button onClick={() => navigate('/progress-analytics')} className="btn-primary">
            <span>Adaptive Loop</span>
            <ArrowRight size={16} />
          </button>
        </div>
      </div>

      {/* Grid of plans */}
      <div className="grid-3">
        {renderPlan(roadmap.technical_plan, "Technical Track")}
        {renderPlan(roadmap.dsa_plan, "DSA & Problem Solving")}
        {renderPlan(roadmap.behavioral_plan, "Behavioral & Delivery")}
      </div>

      {/* Resource recommendations */}
      {roadmap.resource_recommendations?.length > 0 && (
        <div className="glass-card">
          <h3 style={{ marginBottom: '1.25rem', color: 'var(--success)', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <Bookmark size={20} />
            <span>Recommended Learning Resources</span>
          </h3>
          <div className="grid-2">
            {roadmap.resource_recommendations.map((resource, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(255,255,255,0.01)', border: '1px solid var(--border)', padding: '1rem', borderRadius: 'var(--radius-sm)' }}>
                <div>
                  <strong style={{ color: '#ffffff', display: 'block' }}>{resource.title || resource.name}</strong>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    Type: {resource.type || 'Article/Tutorial'} | Priority: {resource.priority || 'High'}
                  </span>
                </div>
                {resource.url && (
                  <a href={resource.url} target="_blank" rel="noopener noreferrer" className="btn-secondary" style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem', gap: '0.25rem' }}>
                    <span>Learn</span>
                    <ExternalLink size={12} />
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Roadmap;
