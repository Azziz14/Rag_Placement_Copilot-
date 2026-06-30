import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { resumeApi } from '../services/api';
import { Upload, FileText, CheckCircle, ArrowRight } from 'lucide-react';

const ResumeUpload = () => {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [parsedResume, setParsedResume] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    try {
      setLoading(true);
      setError(null);
      const res = await resumeApi.upload(file);
      setParsedResume(res);
      // Store resume ID in localStorage for match phase
      localStorage.setItem('current_resume_id', res.id);
    } catch (err) {
      setError(err.response?.data?.detail || "An error occurred while uploading the file. Make sure it is a valid PDF or DOCX under 10MB.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem', maxWidth: '800px', margin: '0 auto' }}>
      <div>
        <h1 className="title-gradient" style={{ fontSize: '2.5rem', fontFamily: 'var(--font-heading)' }}>
          Step 1: Upload your Resume
        </h1>
        <p className="subtitle">Upload your CV to extract skills, experience, and background details.</p>
      </div>

      {error && (
        <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: 'var(--radius-sm)', padding: '1rem', color: 'var(--danger)' }}>
          {error}
        </div>
      )}

      {!parsedResume ? (
        <form onSubmit={handleUpload} className="glass-card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1.5rem', borderStyle: 'dashed', borderWidth: '2px', borderColor: file ? 'var(--accent)' : 'var(--border)', padding: '3rem' }}>
          <div style={{ background: 'var(--accent-glow)', padding: '1.5rem', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Upload size={32} style={{ color: 'var(--accent-light)' }} />
          </div>
          
          <div style={{ textAlign: 'center' }}>
            <p style={{ fontWeight: '600', marginBottom: '0.25rem' }}>Drag & drop your file here, or click to browse</p>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Supports PDF & DOCX (Max 10MB)</span>
          </div>

          <input 
            type="file" 
            accept=".pdf,.docx" 
            onChange={handleFileChange}
            style={{ display: 'none' }}
            id="resume-file-input"
          />
          
          <label htmlFor="resume-file-input" className="btn-secondary" style={{ cursor: 'pointer' }}>
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
            {loading ? <div className="spinner" style={{ width: '20px', height: '20px' }} /> : "Parse Resume"}
          </button>
        </form>
      ) : (
        <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', background: 'rgba(16, 185, 129, 0.05)', border: '1px solid rgba(16, 185, 129, 0.15)', padding: '1rem', borderRadius: 'var(--radius-sm)' }}>
            <CheckCircle size={20} style={{ color: 'var(--success)' }} />
            <div>
              <strong style={{ color: '#ffffff' }}>Resume successfully parsed!</strong>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{parsedResume.original_filename}</p>
            </div>
            <button onClick={() => navigate('/upload-jd')} className="btn-primary" style={{ marginLeft: 'auto' }}>
              <span>Next Step</span>
              <ArrowRight size={16} />
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div>
              <h3 style={{ color: 'var(--accent-light)', marginBottom: '0.5rem' }}>Candidate Information</h3>
              <div className="grid-3" style={{ background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
                <div>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Full Name</span>
                  <p style={{ fontWeight: '600' }}>{parsedResume.full_name || 'N/A'}</p>
                </div>
                <div>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Email</span>
                  <p style={{ fontWeight: '600' }}>{parsedResume.email || 'N/A'}</p>
                </div>
                <div>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Phone</span>
                  <p style={{ fontWeight: '600' }}>{parsedResume.phone || 'N/A'}</p>
                </div>
              </div>
            </div>

            <div>
              <h3 style={{ color: 'var(--accent-light)', marginBottom: '0.5rem' }}>Extracted Skills & Technologies</h3>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                {parsedResume.skills?.map((s, i) => (
                  <span key={i} className="badge badge-primary">{s}</span>
                ))}
                {parsedResume.technologies?.map((t, i) => (
                  <span key={i} className="badge badge-success">{t}</span>
                ))}
              </div>
            </div>

            {parsedResume.experience?.length > 0 && (
              <div>
                <h3 style={{ color: 'var(--accent-light)', marginBottom: '0.5rem' }}>Work Experience</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {parsedResume.experience.map((exp, i) => (
                    <div key={i} style={{ padding: '1rem', background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)' }}>
                      <strong style={{ color: '#ffffff' }}>{exp.role || exp.title}</strong>
                      <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', display: 'block' }}>{exp.company} | {exp.duration || exp.dates}</span>
                      {exp.description && <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>{exp.description}</p>}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ResumeUpload;
