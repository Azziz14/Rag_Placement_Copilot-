import React from 'react';
import { Calendar, Award, CheckCircle, FileText } from 'lucide-react';

/**
 * ScoreMeter - A premium circular SVG progress indicator
 */
export const ScoreMeter = ({ score = 0, size = 120, strokeWidth = 10, title = "" }) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (Math.min(100, Math.max(0, score)) / 100) * circumference;

  return (
    <div style={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'center', gap: '0.75rem' }}>
      <div style={{ position: 'relative', width: size, height: size }}>
        <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="rgba(255, 255, 255, 0.03)"
            strokeWidth={strokeWidth}
          />
          {/* Progress circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="url(#scoreGradient)"
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 0.8s ease-in-out' }}
          />
          <defs>
            <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="var(--accent)" />
              <stop offset="100%" stopColor="var(--accent-light)" />
            </linearGradient>
          </defs>
        </svg>
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
        }}>
          <span style={{ fontSize: `${size * 0.22}px`, fontWeight: 800, fontFamily: 'var(--font-heading)', color: '#ffffff' }}>
            {score}%
          </span>
        </div>
      </div>
      {title && (
        <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600, textAlign: 'center' }}>
          {title}
        </span>
      )}
    </div>
  );
};

/**
 * SkillGapChart - Horizontal comparative gap analysis map
 */
export const SkillGapChart = ({ gaps = [] }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', width: '100%' }}>
      {gaps.map((item, idx) => {
        const userVal = item.userScore || 0;
        const targetVal = item.targetScore || 100;
        return (
          <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.9rem', fontWeight: 600, color: '#ffffff' }}>{item.skill}</span>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                Match: <strong style={{ color: 'var(--accent-light)' }}>{userVal}/{targetVal}</strong>
              </span>
            </div>
            <div style={{ position: 'relative', height: '8px', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '4px', overflow: 'hidden' }}>
              {/* Target Indicator */}
              <div style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: `${(targetVal / 100) * 100}%`,
                height: '100%',
                background: 'rgba(255, 255, 255, 0.1)',
                borderRadius: '4px',
              }} />
              {/* User Level */}
              <div style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: `${(userVal / 100) * 100}%`,
                height: '100%',
                background: 'linear-gradient(90deg, var(--accent) 0%, var(--accent-light) 100%)',
                borderRadius: '4px',
                transition: 'width 0.6s ease',
              }} />
            </div>
          </div>
        );
      })}
    </div>
  );
};

/**
 * TopicHeatmap - Clean, aesthetic grid of domain mastery / topic weights
 */
export const TopicHeatmap = ({ topics = [] }) => {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '0.75rem', width: '100%' }}>
      {topics.map((t, idx) => {
        const weight = t.weight || 'Medium';
        let bg = 'rgba(255, 255, 255, 0.02)';
        let border = '1px solid rgba(255, 255, 255, 0.05)';
        let badgeColor = 'badge-primary';

        if (weight === 'High') {
          bg = 'rgba(99, 102, 241, 0.05)';
          border = '1px solid rgba(99, 102, 241, 0.15)';
          badgeColor = 'badge-danger';
        } else if (weight === 'Low') {
          badgeColor = 'badge-success';
        }

        return (
          <div key={idx} style={{
            background: bg,
            border: border,
            borderRadius: 'var(--radius-sm)',
            padding: '1rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.5rem',
            transition: 'all 0.2s ease',
          }}>
            <span style={{ fontSize: '0.9rem', fontWeight: 600, color: '#ffffff', lineBreak: 'anywhere' }}>{t.name}</span>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto' }}>
              <span className={`badge ${badgeColor}`}>{weight} Priority</span>
              {t.mastery !== undefined && (
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{t.mastery}% Mastered</span>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};

/**
 * ResumeTimeline - Historical tailored versions timeline
 */
export const ResumeTimeline = ({ versions = [], onSelect }) => {
  const safeVersions = Array.isArray(versions) ? versions : [];
  if (safeVersions.length === 0) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
        <FileText size={32} style={{ opacity: 0.3, marginBottom: '0.5rem' }} />
        <p style={{ fontSize: '0.85rem' }}>No tailoring history available yet.</p>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', position: 'relative', paddingLeft: '1rem', borderLeft: '1px solid var(--border)' }}>
      {safeVersions.map((v, idx) => (
        <div key={idx} style={{ position: 'relative', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
          {/* Node point */}
          <div style={{
            position: 'absolute',
            left: '-1.35rem',
            top: '4px',
            width: '10px',
            height: '10px',
            borderRadius: '50%',
            background: 'var(--accent)',
            border: '2px solid var(--bg-card)',
          }} />
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            background: 'rgba(255, 255, 255, 0.02)',
            padding: '0.75rem 1rem',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border)',
            cursor: onSelect ? 'pointer' : 'default',
            transition: 'all 0.2s ease',
          }}
          onClick={() => onSelect && onSelect(v)}>
            <div>
              <h5 style={{ color: '#ffffff', fontSize: '0.9rem' }}>Version {versions.length - idx}</h5>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                <Calendar size={12} />
                {new Date(v.created_at || Date.now()).toLocaleDateString()}
              </span>
            </div>
            <div style={{ textAlign: 'right' }}>
              <span className="badge badge-success">Score: {v.score || v.match_score}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
