import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { jdApi } from '../services/api';
import { Upload, Briefcase, FileText, CheckCircle, ArrowRight } from 'lucide-react';

const JDUpload = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('text'); // 'text' or 'file'
  const [jdText, setJdText] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [jobTitle, setJobTitle] = useState('');
  const [file, setFile] = useState(null);
  
  const [loading, setLoading] = useState(false);
  const [parsedJd, setParsedJd] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleSubmitText = async (e) => {
    e.preventDefault();
    if (!jdText.trim()) return;

    try {
      setLoading(true);
      setError(null);
      // Wait, endpoint is POST /jd/analyze-text
      const res = await jdApi.analyzeText(jdText);
      setParsedJd(res);
      localStorage.setItem('current_jd_id', res.id);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to analyze job description text.");
    } finally {
      setLoading(false);
    }
  };

  const handleUploadFile = async (e) => {
    e.preventDefault();
    if (!file) return;

    try {
      setLoading(true);
      setError(null);
      const res = await jdApi.upload(file);
      setParsedJd(res);
      localStorage.setItem('current_jd_id', res.id);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to upload and analyze job description file.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem', maxWidth: '800px', margin: '0 auto' }}>
      <div>
        <h1 className="title-gradient" style={{ fontSize: '2.5rem', fontFamily: 'var(--font-heading)' }}>
          Step 2: Provide Target Job Description
        </h1>
        <p className="subtitle">Paste the description text or upload the JD file to evaluate matching requirements.</p>
      </div>

      {error && (
        <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: 'var(--radius-sm)', padding: '1rem', color: 'var(--danger)' }}>
          {error}
        </div>
      )}

      {!parsedJd ? (
        <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
          {/* Tabs */}
          <div style={{ display: 'flex', borderBottom: '1px solid var(--border)' }}>
            <button 
              onClick={() => setActiveTab('text')}
              style={{
                flex: 1,
                padding: '1.25rem',
                background: activeTab === 'text' ? 'rgba(255,255,255,0.02)' : 'transparent',
                border: 'none',
                borderBottom: activeTab === 'text' ? '2px solid var(--accent)' : '2px solid transparent',
                color: activeTab === 'text' ? '#ffffff' : 'var(--text-secondary)',
                fontWeight: '600',
                cursor: 'pointer',
                fontFamily: 'var(--font-heading)'
              }}
            >
              Paste JD Text
            </button>
            <button 
              onClick={() => setActiveTab('file')}
              style={{
                flex: 1,
                padding: '1.25rem',
                background: activeTab === 'file' ? 'rgba(255,255,255,0.02)' : 'transparent',
                border: 'none',
                borderBottom: activeTab === 'file' ? '2px solid var(--accent)' : '2px solid transparent',
                color: activeTab === 'file' ? '#ffffff' : 'var(--text-secondary)',
                fontWeight: '600',
                cursor: 'pointer',
                fontFamily: 'var(--font-heading)'
              }}
            >
              Upload JD File
            </button>
          </div>

          <div style={{ padding: '2rem' }}>
            {activeTab === 'text' ? (
              <form onSubmit={handleSubmitText} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                <div className="form-group" style={{ margin: 0 }}>
                  <label>Paste Raw JD Text</label>
                  <textarea 
                    className="form-control" 
                    rows={8}
                    required
                    placeholder="We are looking for a Senior React Engineer with experience in Node.js, system design, and microservices..."
                    value={jdText}
                    onChange={(e) => setJdText(e.target.value)}
                    style={{ resize: 'vertical' }}
                  />
                </div>

                <button 
                  type="submit" 
                  className="btn-primary" 
                  disabled={!jdText.trim() || loading}
                  style={{ width: '100%', justifyContent: 'center' }}
                >
                  {loading ? <div className="spinner" style={{ width: '20px', height: '20px' }} /> : "Analyze Text"}
                </button>
              </form>
            ) : (
              <form onSubmit={handleUploadFile} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1.5rem' }}>
                <div style={{ background: 'var(--accent-glow)', padding: '1.5rem', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Upload size={32} style={{ color: 'var(--accent-light)' }} />
                </div>
                
                <div style={{ textAlign: 'center' }}>
                  <p style={{ fontWeight: '600', marginBottom: '0.25rem' }}>Drag & drop target description file here</p>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Supports PDF & DOCX (Max 10MB)</span>
                </div>

                <input 
                  type="file" 
                  accept=".pdf,.docx" 
                  onChange={handleFileChange}
                  style={{ display: 'none' }}
                  id="jd-file-input"
                />
                
                <label htmlFor="jd-file-input" className="btn-secondary" style={{ cursor: 'pointer' }}>
                  Choose File
                </label>

                {file && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(255,255,255,0.05)', padding: '0.5rem 1rem', borderRadius: 'var(--radius-sm)' }}>
                    <FileText size={16} />
                    <span style={{ fontSize: '0.9rem' }}>{file.name}</span>
                  </div>
                )}

                <button 
                  type="submit" 
                  className="btn-primary" 
                  disabled={!file || loading}
                  style={{ width: '100%', justifyContent: 'center', marginTop: '1rem' }}
                >
                  {loading ? <div className="spinner" style={{ width: '20px', height: '20px' }} /> : "Upload & Analyze"}
                </button>
              </form>
            )}
          </div>
        </div>
      ) : (
        <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', background: 'rgba(16, 185, 129, 0.05)', border: '1px solid rgba(16, 185, 129, 0.15)', padding: '1rem', borderRadius: 'var(--radius-sm)' }}>
            <CheckCircle size={20} style={{ color: 'var(--success)' }} />
            <div>
              <strong style={{ color: '#ffffff' }}>Job Description analyzed!</strong>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                {parsedJd.company_name ? `${parsedJd.company_name} - ` : ''}{parsedJd.job_title}
              </p>
            </div>
            <button onClick={() => navigate('/match-analysis')} className="btn-primary" style={{ marginLeft: 'auto' }}>
              <span>Match Analysis</span>
              <ArrowRight size={16} />
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div>
              <h3 style={{ color: 'var(--accent-light)', marginBottom: '0.5rem' }}>Role Specifications</h3>
              <div className="grid-3" style={{ background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
                <div>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Job Title</span>
                  <p style={{ fontWeight: '600' }}>{parsedJd.job_title}</p>
                </div>
                <div>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Company</span>
                  <p style={{ fontWeight: '600' }}>{parsedJd.company_name || 'N/A'}</p>
                </div>
                <div>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Experience Required</span>
                  <p style={{ fontWeight: '600' }}>{parsedJd.experience_required || 'N/A'}</p>
                </div>
              </div>
            </div>

            <div>
              <h3 style={{ color: 'var(--accent-light)', marginBottom: '0.5rem' }}>Required Skills</h3>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                {parsedJd.required_skills?.map((s, i) => (
                  <span key={i} className="badge badge-primary">{s}</span>
                ))}
                {parsedJd.technologies?.map((t, i) => (
                  <span key={i} className="badge badge-success">{t}</span>
                ))}
              </div>
            </div>

            {parsedJd.responsibilities?.length > 0 && (
              <div>
                <h3 style={{ color: 'var(--accent-light)', marginBottom: '0.5rem' }}>Responsibilities</h3>
                <ul style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', paddingLeft: '1.25rem', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                  {parsedJd.responsibilities.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default JDUpload;
