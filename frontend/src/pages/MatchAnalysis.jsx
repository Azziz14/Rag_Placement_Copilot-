import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { matcherApi, tailorApi } from '../services/api';
import { ScoreMeter } from '../components/VisualElements';
import { 
  CheckCircle, 
  AlertTriangle, 
  Play, 
  Download, 
  Sparkles, 
  ArrowRight,
  RefreshCw,
  FileText,
  FileCheck,
  Zap
} from 'lucide-react';

const MatchAnalysis = () => {
  const navigate = useNavigate();
  const [matchData, setMatchData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tailorForm, setTailorForm] = useState({
    target_role: '',
    focus_areas: '',
    tone: 'professional',
    custom_instructions: '',
  });
  const [tailoring, setTailoring] = useState(false);
  const [tailoredResume, setTailoredResume] = useState(null);
  const [tailorError, setTailorError] = useState(null);

  useEffect(() => {
    const resumeId = localStorage.getItem('current_resume_id');
    const jdId = localStorage.getItem('current_jd_id');

    if (!resumeId || !jdId) {
      setError("Please complete Resume Upload and JD Upload before analyzing matches.");
      setLoading(false);
      return;
    }

    const runAnalysis = async () => {
      try {
        setLoading(true);
        const res = await matcherApi.analyze(resumeId, jdId);
        setMatchData(res);
        localStorage.setItem('current_match_id', res.id);
      } catch (err) {
        setError(err.response?.data?.detail || "An unexpected error occurred during match analysis.");
      } finally {
        setLoading(false);
      }
    };

    runAnalysis();
  }, []);

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
        <AlertTriangle size={44} style={{ color: 'var(--danger)', marginBottom: '1.25rem' }} />
        <h3 style={{ marginBottom: '0.75rem', fontSize: '1.25rem' }}>Incomplete Setup</h3>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem', fontSize: '0.9rem', lineHeight: '1.5' }}>{error}</p>
        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
          <Link to="/upload-resume" className="btn-primary">Upload Resume</Link>
          <Link to="/upload-jd" className="btn-secondary">Upload JD</Link>
        </div>
      </div>
    );
  }

  const handleTailorChange = (field, value) => {
    setTailorForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleGenerateTailoredResume = async (e) => {
    e.preventDefault();
    const resumeId = localStorage.getItem('current_resume_id');
    const jdId = localStorage.getItem('current_jd_id');

    try {
      setTailoring(true);
      setTailorError(null);
      const res = await tailorApi.generate({
        resume_id: resumeId,
        jd_id: jdId,
        target_role: tailorForm.target_role || 'Target Role',
        focus_areas: tailorForm.focus_areas
          .split(',')
          .map((item) => item.trim())
          .filter(Boolean),
        exclude_sections: [],
        tone: tailorForm.tone,
        preserve_format: true,
        custom_instructions: tailorForm.custom_instructions,
      });
      setTailoredResume(res);
    } catch (err) {
      setTailorError(err.response?.data?.detail || 'Could not generate the tailored resume.');
    } finally {
      setTailoring(false);
    }
  };

  const handleDownloadTailoredResume = async () => {
    if (!tailoredResume?.tailored_resume_id) return;
    const blob = await tailorApi.download(tailoredResume.tailored_resume_id);
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'tailored_resume.docx';
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      
      {/* Title */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 className="title-gradient" style={{ fontSize: '2.5rem', fontFamily: 'var(--font-heading)', fontWeight: '800' }}>
            Resume-JD Compatibility
          </h1>
          <p className="subtitle">Detailed breakdown of skills match, gap analysis, and tailored versions.</p>
        </div>
        <button onClick={() => navigate('/interview-session')} className="btn-primary">
          <Play size={16} />
          <span>Start Interview Session</span>
        </button>
      </div>

      {/* Side-by-Side Diff View / Match score */}
      {!tailoredResume ? (
        <div className="glass-card" style={{ display: 'flex', alignItems: 'center', gap: '2rem', flexWrap: 'wrap' }}>
          <ScoreMeter score={Math.round(matchData.match_score)} size={110} strokeWidth={9} />
          <div style={{ flex: 1, minWidth: '280px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
              <h2 style={{ fontSize: '1.5rem' }}>Compatibility Score</h2>
              <span className="badge badge-primary">Active Analysis</span>
            </div>
            <p style={{ color: 'var(--text-secondary)', lineHeight: 1.5, fontSize: '0.9rem' }}>
              Your resume exhibits a compatibility match of {Math.round(matchData.match_score)}% for the target job requirements. Use the tailoring utility below to address missing skill gaps.
            </p>
          </div>
        </div>
      ) : (
        <div className="glass-card" style={{ border: '1px solid rgba(16, 185, 129, 0.2)', background: 'rgba(21, 27, 44, 0.4)' }}>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
            <Zap size={20} style={{ color: 'var(--success)' }} />
            <h3 style={{ fontSize: '1.25rem' }}>Resume Tailoring Optimization Report</h3>
            <button onClick={handleDownloadTailoredResume} className="btn-primary" style={{ marginLeft: 'auto' }}>
              <Download size={14} />
              <span>Download Tailored Resume</span>
            </button>
          </div>

          <div className="grid-3" style={{ marginBottom: '1.5rem', background: 'rgba(0,0,0,0.15)', padding: '1.25rem', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Original ATS Score</span>
              <ScoreMeter score={Math.round(tailoredResume.original_score)} size={80} strokeWidth={6} />
            </div>
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
              <ArrowRight size={24} style={{ color: 'var(--success)' }} />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Tailored ATS Score</span>
              <ScoreMeter score={Math.round(tailoredResume.improved_score)} size={80} strokeWidth={6} />
            </div>
          </div>

          {/* Interactive side-by-side visual diff */}
          <div className="grid-2">
            <div style={{ background: 'rgba(255, 255, 255, 0.01)', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', padding: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>
                <FileText size={16} style={{ color: 'var(--text-secondary)' }} />
                <h4 style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Original Resume Key Gaps</h4>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {matchData.missing_skills?.slice(0, 5).map((s, i) => (
                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', color: 'var(--danger)', background: 'rgba(239, 68, 68, 0.03)', padding: '0.4rem 0.6rem', borderRadius: '4px' }}>
                    <span>{s}</span>
                    <span>Missing</span>
                  </div>
                ))}
                {matchData.missing_technologies?.slice(0, 5).map((t, i) => (
                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', color: 'var(--warning)', background: 'rgba(245, 158, 11, 0.03)', padding: '0.4rem 0.6rem', borderRadius: '4px' }}>
                    <span>{t}</span>
                    <span>Missing Tech</span>
                  </div>
                ))}
              </div>
            </div>

            <div style={{ background: 'rgba(16, 185, 129, 0.01)', border: '1px solid rgba(16, 185, 129, 0.1)', borderRadius: 'var(--radius-sm)', padding: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem', borderBottom: '1px solid rgba(16, 185, 129, 0.1)', paddingBottom: '0.5rem' }}>
                <FileCheck size={16} style={{ color: 'var(--success)' }} />
                <h4 style={{ fontSize: '0.9rem', color: 'var(--success)' }}>Optimized Inclusions & Adjustments</h4>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {tailoredResume.changed_sections?.map((sec, i) => (
                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', color: 'var(--success)', background: 'rgba(16, 185, 129, 0.04)', padding: '0.4rem 0.6rem', borderRadius: '4px' }}>
                    <span style={{ textTransform: 'capitalize' }}>{sec} Section</span>
                    <span>Enhanced & Aligned</span>
                  </div>
                ))}
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.5rem', lineHeight: '1.4' }}>
                  Missing keywords matching job description qualifiers were naturally incorporated into summary, experience, and project descriptions.
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tailoring Control Panel */}
      <form onSubmit={handleGenerateTailoredResume} className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <div>
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '1.25rem' }}>
            <Sparkles size={18} style={{ color: 'var(--accent-light)' }} />
            <span>Generate JD-Tailored Resume</span>
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '0.25rem' }}>
            Refine how the LLM tailors your qualifications for the target organization.
          </p>
        </div>

        {tailorError && (
          <div style={{ background: 'rgba(239, 68, 68, 0.05)', border: '1px solid rgba(239, 68, 68, 0.15)', borderRadius: 'var(--radius-sm)', padding: '0.75rem', color: 'var(--danger)', fontSize: '0.85rem' }}>
            {tailorError}
          </div>
        )}

        <div className="grid-2">
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label htmlFor="target-role">Target Role Title</label>
            <input
              id="target-role"
              className="form-control"
              value={tailorForm.target_role}
              onChange={(e) => handleTailorChange('target_role', e.target.value)}
              placeholder="e.g. Senior Frontend Engineer"
            />
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label htmlFor="tone">Tone Preference</label>
            <select
              id="tone"
              className="form-control"
              value={tailorForm.tone}
              onChange={(e) => handleTailorChange('tone', e.target.value)}
            >
              <option value="professional">Professional & Direct</option>
              <option value="concise">Concise & Action-oriented</option>
              <option value="impact-focused">Metrics & Impact-focused</option>
              <option value="technical">Highly Technical</option>
            </select>
          </div>
        </div>

        <div className="form-group" style={{ marginBottom: 0 }}>
          <label htmlFor="focus-areas">Core Focus Keywords (Comma separated)</label>
          <input
            id="focus-areas"
            className="form-control"
            value={tailorForm.focus_areas}
            onChange={(e) => handleTailorChange('focus_areas', e.target.value)}
            placeholder="e.g. React, Next.js, API Integration"
          />
        </div>

        <div className="form-group" style={{ marginBottom: 0 }}>
          <label htmlFor="custom-instructions">Custom Directives / Prompt Directions</label>
          <textarea
            id="custom-instructions"
            className="form-control"
            rows={3}
            value={tailorForm.custom_instructions}
            onChange={(e) => handleTailorChange('custom_instructions', e.target.value)}
            placeholder="e.g. Keep resume to exactly one page. Highlight Kubernetes expertise in projects."
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <button type="submit" className="btn-primary" disabled={tailoring}>
            {tailoring ? <div className="spinner" style={{ width: '16px', height: '16px' }} /> : <Sparkles size={14} />}
            <span>{tailoring ? 'Processing...' : 'Tailor Profile'}</span>
          </button>
        </div>
      </form>

      {/* Skills Match Overview */}
      <div className="grid-2">
        <div className="glass-card">
          <h3 style={{ marginBottom: '1rem', color: 'var(--success)', display: 'flex', gap: '0.5rem', alignItems: 'center', fontSize: '1.05rem' }}>
            <CheckCircle size={18} />
            <span>Overlapping Competencies ({matchData.matched_skills?.length || 0})</span>
          </h3>
          <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
            {matchData.matched_skills?.length > 0 ? (
              matchData.matched_skills.map((s, i) => (
                <span key={i} className="badge badge-success" style={{ textTransform: 'none' }}>{s}</span>
              ))
            ) : (
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>No direct overlapping skills detected.</p>
            )}
          </div>
        </div>

        <div className="glass-card">
          <h3 style={{ marginBottom: '1rem', color: 'var(--danger)', display: 'flex', gap: '0.5rem', alignItems: 'center', fontSize: '1.05rem' }}>
            <AlertTriangle size={18} />
            <span>Identified Skill Gaps ({ (matchData.missing_skills?.length || 0) + (matchData.missing_technologies?.length || 0) })</span>
          </h3>
          <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
            {matchData.missing_skills?.map((s, i) => (
              <span key={i} className="badge badge-danger" style={{ textTransform: 'none' }}>{s}</span>
            ))}
            {matchData.missing_technologies?.map((t, i) => (
              <span key={i} className="badge badge-warning" style={{ textTransform: 'none' }}>{t}</span>
            ))}
            {(!matchData.missing_skills?.length && !matchData.missing_technologies?.length) && (
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>No major skill gaps identified.</p>
            )}
          </div>
        </div>
      </div>

      {/* Improvement recommendations */}
      {matchData.improvement_areas?.length > 0 && (
        <div className="glass-card">
          <h3 style={{ marginBottom: '1.25rem', fontSize: '1.1rem', color: 'var(--accent-light)' }}>Recommended Improvement Focus Areas</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
            {matchData.improvement_areas.map((area, i) => (
              <div key={i} style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start', background: 'rgba(255,255,255,0.01)', border: '1px solid var(--border)', padding: '0.85rem', borderRadius: 'var(--radius-sm)' }}>
                <span style={{
                  background: 'rgba(99, 102, 241, 0.15)',
                  color: 'var(--accent-light)',
                  width: '22px',
                  height: '22px',
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '0.75rem',
                  fontWeight: 'bold',
                  flexShrink: 0
                }}>{i + 1}</span>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', lineHeight: '1.5' }}>{area}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default MatchAnalysis;
