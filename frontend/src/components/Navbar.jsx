import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  LayoutDashboard, 
  FileText, 
  Briefcase, 
  GitCompare, 
  TrendingUp, 
  LogOut,
  BookOpen,
  Menu,
  X
} from 'lucide-react';

const Navbar = () => {
  const { signOut, user } = useAuth();
  const [isOpen, setIsOpen] = useState(false);

  const activeStyle = ({ isActive }) => ({
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    padding: '0.75rem 1rem',
    borderRadius: 'var(--radius-md)',
    color: isActive ? '#ffffff' : 'var(--text-secondary)',
    background: isActive ? 'linear-gradient(135deg, rgba(99, 102, 241, 0.12), rgba(79, 70, 229, 0.25))' : 'transparent',
    boxShadow: isActive ? 'inset 2px 2px 4px rgba(255, 255, 255, 0.05), inset -2px -2px 4px rgba(0, 0, 0, 0.3), 3px 3px 6px rgba(0, 0, 0, 0.1)' : 'none',
    borderLeft: isActive ? '3px solid var(--accent)' : '3px solid transparent',
    textDecoration: 'none',
    fontWeight: '600',
    fontSize: '0.9rem',
    transition: 'all 0.25s cubic-bezier(0.16, 1, 0.3, 1)',
  });

  return (
    <>
      {/* Mobile Top Header */}
      <header style={{
        display: 'none',
        justifyContent: 'space-between',
        alignItems: 'center',
        background: 'var(--bg-space)',
        borderBottom: '1px solid var(--border)',
        padding: '1rem 1.25rem',
        position: 'sticky',
        top: 0,
        zIndex: 50,
      }} className="mobile-header">
        <div>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 800, background: 'linear-gradient(135deg, #ffffff 0%, var(--accent-light) 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', fontFamily: 'var(--font-heading)' }}>
            InterviewPilot AI
          </h2>
        </div>
        <button 
          onClick={() => setIsOpen(!isOpen)}
          style={{ background: 'none', border: 'none', color: '#ffffff', cursor: 'pointer' }}
        >
          {isOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </header>

      {/* Sidebar Navigation */}
      <aside style={{
        width: '260px',
        background: 'var(--bg-space)',
        borderRight: '1px solid var(--border)',
        padding: '2rem 1.5rem',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        minHeight: '100vh',
        position: 'sticky',
        top: 0,
        zIndex: 40,
        transition: 'transform 0.3s ease',
      }} className={`sidebar-nav ${isOpen ? 'open' : ''}`}>
        <div>
          <div style={{ marginBottom: '2.5rem', display: 'flex', flexDirection: 'column', gap: '0.25rem' }} className="sidebar-logo">
            <h2 style={{ fontSize: '1.35rem', fontWeight: 800, background: 'linear-gradient(135deg, #ffffff 0%, var(--accent-light) 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', fontFamily: 'var(--font-heading)' }}>
              InterviewPilot
            </h2>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
              Career Intelligence
            </span>
          </div>

          <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }} onClick={() => setIsOpen(false)}>
            <NavLink to="/" style={activeStyle}>
              <LayoutDashboard size={16} />
              <span>Dashboard</span>
            </NavLink>

            <NavLink to="/upload-resume" style={activeStyle}>
              <FileText size={16} />
              <span>Resume Upload</span>
            </NavLink>

            <NavLink to="/upload-jd" style={activeStyle}>
              <Briefcase size={16} />
              <span>JD Upload</span>
            </NavLink>

            <NavLink to="/match-analysis" style={activeStyle}>
              <GitCompare size={16} />
              <span>Match Analysis</span>
            </NavLink>

            <NavLink to="/progress-analytics" style={activeStyle}>
              <TrendingUp size={16} />
              <span>Analytics & Loop</span>
            </NavLink>

            <NavLink to="/learning-hub" style={activeStyle}>
              <BookOpen size={16} />
              <span>Learning Hub</span>
            </NavLink>
          </nav>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', borderTop: '1px solid var(--border)', paddingTop: '1.5rem', marginTop: '2rem' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.1rem' }}>
            <span style={{ fontSize: '0.85rem', color: '#ffffff', fontWeight: '600', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {user?.user_metadata?.full_name || 'Candidate'}
            </span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {user?.email}
            </span>
          </div>

          <button 
            onClick={signOut} 
            className="btn-secondary" 
            style={{
              justifyContent: 'center',
              width: '100%',
              padding: '0.6rem',
              fontSize: '0.85rem',
              background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.08), rgba(220, 38, 38, 0.15))',
              color: '#f87171',
              boxShadow: '4px 4px 10px rgba(0, 0, 0, 0.25), inset 2px 2px 4px rgba(255, 255, 255, 0.05), inset -2px -2px 4px rgba(0, 0, 0, 0.35)',
              border: '1px solid rgba(239, 68, 68, 0.15)',
              borderRadius: 'var(--radius-md)'
            }}
          >
            <LogOut size={14} />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Overlay for mobile drawer */}
      {isOpen && (
        <div 
          onClick={() => setIsOpen(false)}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.5)',
            backdropFilter: 'blur(4px)',
            zIndex: 30,
          }}
          className="mobile-overlay"
        />
      )}

      {/* Responsive Styles Injection */}
      <style>{`
        @media (max-width: 900px) {
          .mobile-header {
            display: flex !important;
          }
          .sidebar-nav {
            position: fixed !important;
            transform: translateX(-100%);
            height: 100vh;
            box-shadow: 10px 0 30px rgba(0,0,0,0.5);
          }
          .sidebar-nav.open {
            transform: translateX(0);
          }
          .sidebar-logo {
            display: none !important;
          }
        }
      `}</style>
    </>
  );
};

export default Navbar;

