import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { evaluationApi, weaknessApi, roadmapApi, adaptiveApi } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { ScoreMeter } from '../components/VisualElements';
import { Award, CheckCircle2, AlertTriangle, ArrowRight, Sparkles, LayoutDashboard } from 'lucide-react';

const EvaluationResults = () => {
  const { sessionId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [evaluation, setEvaluation] = useState(null);
  const [weakness, setWeakness] = useState(null);
  const [loading, setLoading] = useState(true);
  const [progressMsg, setProgressMsg] = useState('');
  const [error, setError] = useState(null);

  useEffect(() => {
    const runEvaluationPipeline = async () => {
      if (!user?.id) return;
      try {
        setLoading(true);
        setError(null);
        
        setProgressMsg('Evaluating interview responses...');
        const evalRes = await evaluationApi.analyze(sessionId);
        setEvaluation(evalRes);
        
        try {
          setProgressMsg('Running weakness pattern analysis...');
          const weakRes = await weaknessApi.analyze(sessionId);
          setWeakness(weakRes);
          
          setProgressMsg('Generating personalized study roadmap...');
          await roadmapApi.generate(sessionId);
          
          setProgressMsg('Updating adaptive profile loop...');
          await adaptiveApi.generateProfile(user.id);
        } catch (subErr) {
          console.warn("Sub-pipeline analysis failed, but base evaluations succeeded.", subErr);
        }

      } catch (err) {
        setError(err.response?.data?.detail || "Failed to retrieve evaluation results.");
      } finally {
        setLoading(false);
      }
    };

    if (user?.id) {
      runEvaluationPipeline();
    }
  }, [sessionId, user?.id]);

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', minHeight: '80vh', gap: '1rem' }}>
        <div className="spinner"></div>
        <p style={{ color: 'var(--text-secondary)', fontWeight: '600', fontSize: '0.9rem' }}>{progressMsg}</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-card" style={{ textAlign: 'center', padding: '3.5rem 2rem', maxWidth: '600px', margin: '3rem auto' }}>
        <AlertTriangle size={44} style={{ color: 'var(--danger)', marginBottom: '1.25rem' }} />
        <h3 style={{ marginBottom: '0.75rem', fontSize: '1.2rem' }}>Evaluation Failed</h3>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem', fontSize: '0.9rem' }}>{error}</p>
        <button onClick={() => navigate('/')} className="btn-primary">Return to Dashboard</button>
      </div>
    );
  }

  const averageScore = Math.round(
    evaluation.evaluations?.reduce((acc, ev) => acc + ev.overall_score, 0) / (evaluation.evaluations?.length || 1)
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Header Banner */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1.5rem' }}>
        <div>
          <span className="badge badge-success" style={{ marginBottom: '0.5rem' }}>Session Complete</span>
          <h1 className="title-gradient" style={{ fontSize: '2.5rem', fontFamily: 'var(--font-heading)', fontWeight: '800' }}>
            Evaluation Report
          </h1>
          <p className="subtitle">Detailed evaluation breakdown based on your mock interview responses.</p>
        </div>
        
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button onClick={() => navigate('/')} className="btn-secondary">
            <LayoutDashboard size={14} />
            <span>Dashboard</span>
          </button>
          
          <button onClick={() => navigate(`/roadmap/${sessionId}`)} className="btn-primary">
            <span>View Roadmap</span>
            <ArrowRight size={14} />
          </button>
        </div>
      </div>

      {/* Summary Score Card */}
      <div className="glass-card" style={{ display: 'flex', alignItems: 'center', gap: '2rem', flexWrap: 'wrap' }}>
        <ScoreMeter score={averageScore || 0} size={110} strokeWidth={9} />
        <div style={{ flex: 1, minWidth: '280px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
            <h2 style={{ fontSize: '1.5rem' }}>Overall Performance</h2>
            <span className="badge badge-primary">{averageScore >= 80 ? 'Distinguished' : 'Proficient'}</span>
          </div>
          <p style={{ color: 'var(--text-secondary)', lineHeight: 1.5, fontSize: '0.9rem' }}>
            Your answers were graded against target JD qualifiers. Check below for individual question breakdowns, key strengths, and missing engineering concepts.
          </p>
        </div>
      </div>

      {/* Answer-by-Answer Evaluation */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <h2 style={{ fontSize: '1.25rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>Individual Question Analysis</h2>
        
        {evaluation.evaluations?.map((ev, index) => (
          <div key={index} className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.75rem' }}>
              <div>
                <strong style={{ color: 'var(--accent-light)', fontSize: '0.75rem', textTransform: 'uppercase' }}>
                  Question {index + 1}
                </strong>
                <p style={{ fontSize: '1rem', color: '#ffffff', fontWeight: '600', marginTop: '0.2rem' }}>
                  {ev.question || `Question Detail`}
                </p>
              </div>
              <span className="badge badge-primary" style={{ fontSize: '0.8rem', padding: '0.3rem 0.6rem' }}>
                Score: {ev.overall_score}%
              </span>
            </div>

            <div style={{ background: 'rgba(0,0,0,0.15)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', textTransform: 'uppercase', fontWeight: 600 }}>Your Answer</span>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-primary)', marginTop: '0.25rem', lineHeight: 1.4 }}>
                {ev.answer}
              </p>
            </div>

            {/* Keywords Matching Analysis */}
            {ev.key_phrases && ev.key_phrases.length > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', background: 'rgba(255,255,255,0.02)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', textTransform: 'uppercase', fontWeight: 600 }}>Expected Concept / Keyword Matching</span>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.25rem' }}>
                  {ev.key_phrases.map((kp, idx) => {
                    const isMatched = ev.matched_key_phrases?.some(m => m.toLowerCase() === kp.toLowerCase());
                    return (
                      <span 
                        key={idx} 
                        style={{
                          fontSize: '0.8rem',
                          padding: '0.25rem 0.6rem',
                          borderRadius: '12px',
                          fontWeight: 500,
                          background: isMatched ? 'rgba(34, 197, 94, 0.12)' : 'rgba(239, 68, 68, 0.08)',
                          color: isMatched ? '#4ade80' : '#f87171',
                          border: isMatched ? '1px solid rgba(34, 197, 94, 0.25)' : '1px solid rgba(239, 68, 68, 0.15)',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.25rem'
                        }}
                      >
                        <span style={{ 
                          width: '6px', 
                          height: '6px', 
                          borderRadius: '50%', 
                          background: isMatched ? '#22c55e' : '#ef4444' 
                        }}></span>
                        {kp}
                      </span>
                    );
                  })}
                </div>
              </div>
            )}

            <div className="grid-2">
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                <strong style={{ color: 'var(--success)', fontSize: '0.85rem', display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                  <CheckCircle2 size={14} /> Strengths
                </strong>
                <ul style={{ paddingLeft: '1rem', fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                  {ev.strengths?.map((str, idx) => <li key={idx}>{str}</li>) || <li>Demonstrated correct baseline terminology.</li>}
                </ul>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                <strong style={{ color: 'var(--danger)', fontSize: '0.85rem', display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                  <AlertTriangle size={14} /> Weaknesses
                </strong>
                <ul style={{ paddingLeft: '1rem', fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                  {ev.weaknesses?.map((wk, idx) => <li key={idx}>{wk}</li>) || <li>Opportunities to provide deeper design details.</li>}
                </ul>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default EvaluationResults;
