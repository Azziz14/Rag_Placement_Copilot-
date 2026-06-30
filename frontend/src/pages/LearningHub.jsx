import React, { useState, useEffect } from 'react';
import { learningApi } from '../services/api';
import { TopicHeatmap } from '../components/VisualElements';
import { 
  BookOpen, 
  Terminal, 
  Play, 
  CheckCircle, 
  Code, 
  Award, 
  Activity, 
  HelpCircle, 
  ChevronRight,
  ChevronDown,
  ChevronUp,
  TrendingUp,
  Sliders,
  Settings,
  Cpu,
  Layers,
  FileCode,
  CheckSquare,
  RefreshCw,
  Sparkles
} from 'lucide-react';

const LearningHub = () => {
  const [selectedDomain, setSelectedDomain] = useState('');
  const [level, setLevel] = useState('intermediate');
  const [targetRole, setTargetRole] = useState('Backend Engineer');
  const [targetCompany, setTargetCompany] = useState('FAANG');
  const [weakTopics, setWeakTopics] = useState('');
  
  const [prioritizing, setPrioritizing] = useState(false);
  const [prioritizedData, setPrioritizedData] = useState(null);
  
  const [selectedTopic, setSelectedTopic] = useState('');
  const [question, setQuestion] = useState(null);
  const [generatingQuestion, setGeneratingQuestion] = useState(false);
  
  // Submission & coding states
  const [userCode, setUserCode] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState('python');
  const [userTheoryAnswer, setUserTheoryAnswer] = useState('');
  const [userMCQIndex, setUserMCQIndex] = useState(-1);
  const [activeTab, setActiveTab] = useState('editor'); // editor | testcases | console
  
  const [grading, setGrading] = useState(false);
  const [gradeResult, setGradeResult] = useState(null);
  
  const [executingCode, setExecutingCode] = useState(false);
  const [executionResult, setExecutionResult] = useState(null);

  // Added States for LLM Study Guide & Market Trends
  const [trends, setTrends] = useState([]);
  const [loadingTrends, setLoadingTrends] = useState(false);
  const [explanation, setExplanation] = useState('');
  const [loadingExplanation, setLoadingExplanation] = useState(false);
  const [explanationTarget, setExplanationTarget] = useState('');
  const [expandedTrendIndex, setExpandedTrendIndex] = useState(null);

  const domainsList = [
    { id: 'dbms', name: 'Database Management Systems', desc: 'Indexes, transactions, normalization', icon: <Cpu size={20} /> },
    { id: 'sql', name: 'SQL Querying', desc: 'Joins, aggregations, windows', icon: <Terminal size={20} /> },
    { id: 'cn', name: 'Computer Networks', desc: 'TCP/IP, HTTP, routing, protocols', icon: <TrendingUp size={20} /> },
    { id: 'os', name: 'Operating Systems', desc: 'Scheduling, memory, virtualization', icon: <Layers size={20} /> },
    { id: 'oops', name: 'Object-Oriented Programming', desc: 'Design patterns, classes, inheritance', icon: <Award size={20} /> },
    { id: 'dsa', name: 'Data Structures & Algorithms', desc: 'Trees, dynamic programming, sorting', icon: <Code size={20} /> },
    { id: 'system_design', name: 'System Design', desc: 'Scalability, caching, distribution', icon: <BookOpen size={20} /> },
    { id: 'ml', name: 'Machine Learning', desc: 'Supervised, neural networks, NLP', icon: <Activity size={20} /> }
  ];

  const handleDomainSelect = async (domainId) => {
    setSelectedDomain(domainId);
    setPrioritizedData(null);
    setQuestion(null);
    setGradeResult(null);
    setSelectedTopic('');
    setExplanation('');
    setExplanationTarget('');
    setTrends([]);
    setExpandedTrendIndex(null);
    
    // Fetch trends automatically for the selected domain
    setLoadingTrends(true);
    try {
      const res = await learningApi.getTrends({ domain: domainId });
      if (res && res.trends) {
        setTrends(res.trends);
      }
    } catch (err) {
      console.error("Failed to load trends:", err);
    } finally {
      setLoadingTrends(false);
    }
  };

  const handleStudyBasics = async (topicName = null) => {
    const target = topicName || domainsList.find(d => d.id === selectedDomain)?.name || selectedDomain;
    setExplanationTarget(target);
    setExplanation('');
    setLoadingExplanation(true);
    try {
      const res = await learningApi.explainTopic({
        domain: selectedDomain,
        topic: topicName || undefined
      });
      if (res && res.explanation) {
        setExplanation(res.explanation);
      }
    } catch (err) {
      alert("Failed to load study guide. Please try again.");
    } finally {
      setLoadingExplanation(false);
    }
  };

  const handlePrioritize = async (e) => {
    e.preventDefault();
    if (!selectedDomain) return;
    try {
      setPrioritizing(true);
      const res = await learningApi.prioritizeTopics({
        domain: selectedDomain,
        level,
        target_role: targetRole,
        target_company: targetCompany,
        weak_topics: weakTopics ? weakTopics.split(',').map(t => t.trim()) : []
      });
      setPrioritizedData(res);
    } catch (err) {
      alert("Failed to prioritize topics. Please try again.");
    } finally {
      setPrioritizing(false);
    }
  };

  const handleFetchQuestion = async (topic, force = false) => {
    setSelectedTopic(topic);
    setQuestion(null);
    setGradeResult(null);
    setExecutionResult(null);
    setActiveTab('editor');
    try {
      setGeneratingQuestion(true);
      const res = await learningApi.generateQuestion({
        domain: selectedDomain,
        topic,
        difficulty: 'medium',
        preferred_language: selectedLanguage,
        force_refresh: force
      });
      setQuestion(res);
      if (res.is_coding) {
        setUserCode(res.starter_code || '');
      } else {
        setUserTheoryAnswer('');
        setUserMCQIndex(-1);
      }
    } catch (err) {
      alert("Failed to generate learning challenge.");
    } finally {
      setGeneratingQuestion(false);
    }
  };

  const handleExecuteCode = async () => {
    if (!question || !question.is_coding) return;
    setActiveTab('console');
    try {
      setExecutingCode(true);
      const res = await learningApi.executeCode({
        code: userCode,
        language: selectedLanguage,
        input_data: question.test_cases?.[0]?.input || ''
      });
      setExecutionResult(res);
    } catch (err) {
      setExecutionResult({ success: false, stderr: "Execution Wrapper Error." });
    } finally {
      setExecutingCode(false);
    }
  };

  const handleSubmitAnswer = async () => {
    if (!question) return;
    try {
      setGrading(true);
      
      let submissionData = {};
      if (question.is_coding) {
        submissionData = {
          code: userCode,
          language: selectedLanguage
        };
      } else if (question.type === 'mcq') {
        submissionData = {
          choice_index: userMCQIndex
        };
      } else {
        submissionData = {
          answer: userTheoryAnswer
        };
      }

      const res = await learningApi.submitAnswer({
        question_data: question,
        submission_data: submissionData
      });
      setGradeResult(res);
    } catch (err) {
      alert("Failed to grade submission.");
    } finally {
      setGrading(false);
    }
  };

  // Convert topics to array structure for heatmap component
  const getHeatmapTopics = () => {
    if (!prioritizedData) return [];
    return prioritizedData.important_topics.map((t, idx) => ({
      name: t,
      weight: prioritizedData.priority_score[idx] > 70 ? 'High' : (prioritizedData.priority_score[idx] > 40 ? 'Medium' : 'Low'),
      mastery: Math.round(50 + (prioritizedData.priority_score[idx] * 0.4))
    }));
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      
      {/* Title */}
      <div>
        <h1 className="title-gradient" style={{ fontSize: '2.5rem', marginBottom: '0.25rem', fontFamily: 'var(--font-heading)', fontWeight: '800' }}>
          CS Learning Hub
        </h1>
        <p className="subtitle">Interactive path customization and code compiler sandboxes.</p>
      </div>

      {/* Step 1: Select Domain */}
      <div>
        <h3 style={{ marginBottom: '1rem', fontSize: '1.1rem', color: '#ffffff', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ color: 'var(--accent-light)' }}>01 /</span> Select Core CS Domain
        </h3>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1rem' }}>
          {domainsList.map((d) => (
            <div 
              key={d.id} 
              onClick={() => handleDomainSelect(d.id)}
              className="glass-card" 
              style={{
                cursor: 'pointer',
                border: selectedDomain === d.id ? '1px solid var(--accent)' : '1px solid var(--border)',
                background: selectedDomain === d.id ? 'var(--bg-card-hover)' : 'var(--bg-card)',
                padding: '1.25rem',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '1rem'
              }}
            >
              <div style={{ 
                color: selectedDomain === d.id ? 'var(--accent-light)' : 'var(--text-secondary)',
                background: 'rgba(255,255,255,0.02)',
                padding: '0.6rem',
                borderRadius: '6px',
                border: '1px solid var(--border)'
              }}>
                {d.icon}
              </div>
              <div>
                <h4 style={{ fontSize: '0.95rem', fontWeight: '700' }}>{d.name}</h4>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>{d.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Domain Insights & Study Panel */}
      {selectedDomain && (
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.25rem' }} className="grid-2">
          {/* Study Guide Panel */}
          <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem', border: '1px solid var(--border)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Sparkles size={20} style={{ color: 'var(--accent-light)' }} />
                <h3 style={{ fontSize: '1.2rem', margin: 0 }}>Study Portal: {explanationTarget || domainsList.find(d => d.id === selectedDomain)?.name}</h3>
              </div>
              <button 
                onClick={() => handleStudyBasics()}
                className="btn-primary"
                style={{ padding: '0.5rem 1rem', fontSize: '0.85rem', background: 'linear-gradient(135deg, var(--accent) 0%, var(--accent-light) 100%)' }}
                disabled={loadingExplanation}
              >
                {loadingExplanation ? 'Preparing Guide...' : '📖 Study Domain Basics'}
              </button>
            </div>

            {loadingExplanation ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '3rem', gap: '1rem' }}>
                <div className="spinner"></div>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Tailoring a friendly explanation of the core concepts, importance, and everyday analogies...</p>
              </div>
            ) : explanation ? (
              <div style={{ 
                background: 'rgba(0, 0, 0, 0.2)', 
                border: '1px solid var(--border)', 
                padding: '1.5rem', 
                borderRadius: 'var(--radius-md)', 
                color: 'var(--text-primary)',
                fontSize: '0.9rem',
                lineHeight: '1.6',
                whiteSpace: 'pre-line',
                maxHeight: '400px',
                overflowY: 'auto'
              }}>
                {explanation}
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                <BookOpen size={32} style={{ opacity: 0.2, marginBottom: '0.5rem' }} />
                <p style={{ fontSize: '0.85rem' }}>Click "Study Domain Basics" or select a topic below and click "Study Topic Basics" to learn the essentials in a friendly way.</p>
              </div>
            )}
          </div>

          {/* Market Trends Panel */}
          <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem', border: '1px solid var(--border)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <TrendingUp size={20} style={{ color: 'var(--accent-light)' }} />
              <h3 style={{ fontSize: '1.2rem', margin: 0 }}>Market Trends</h3>
            </div>
            
            {loadingTrends ? (
              <div style={{ display: 'flex', justifyContent: 'center', padding: '2rem' }}>
                <div className="spinner"></div>
              </div>
            ) : trends.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                 {trends.map((trend, index) => (
                  <div 
                    key={index}
                    onClick={() => setExpandedTrendIndex(expandedTrendIndex === index ? null : index)}
                    style={{
                      background: expandedTrendIndex === index ? 'rgba(99, 102, 241, 0.08)' : 'rgba(255, 255, 255, 0.02)',
                      border: expandedTrendIndex === index ? '1px solid var(--accent)' : '1px solid var(--border)',
                      borderRadius: 'var(--radius-sm)',
                      padding: '1rem',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.5rem',
                      position: 'relative',
                      cursor: 'pointer',
                      transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                      transform: expandedTrendIndex === index ? 'translateY(-2px)' : 'translateY(0)',
                      boxShadow: expandedTrendIndex === index ? '0 4px 20px rgba(99, 102, 241, 0.15)' : 'none'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <span className="badge badge-danger" style={{ 
                        fontSize: '0.65rem', 
                        background: 'linear-gradient(135deg, #f59e0b 0%, #ef4444 100%)',
                        boxShadow: '0 0 10px rgba(239, 68, 68, 0.3)',
                        border: 'none',
                        color: '#ffffff'
                      }}>
                        🔥 New Trending
                      </span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <span className="badge badge-primary" style={{ fontSize: '0.65rem' }}>
                          {trend.impact_level} Impact
                        </span>
                        <span style={{ color: 'var(--text-secondary)', display: 'flex', alignItems: 'center' }}>
                          {expandedTrendIndex === index ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                        </span>
                      </div>
                    </div>
                    <h4 style={{ fontSize: '0.9rem', fontWeight: '700', color: '#ffffff', marginTop: '0.25rem' }}>{trend.title}</h4>
                    <p style={{ 
                      fontSize: '0.75rem', 
                      color: 'var(--text-primary)', 
                      lineHeight: '1.5',
                      display: expandedTrendIndex === index ? 'block' : '-webkit-box',
                      WebkitLineClamp: expandedTrendIndex === index ? 'unset' : 2,
                      WebkitBoxOrient: 'vertical',
                      overflow: expandedTrendIndex === index ? 'visible' : 'hidden',
                      maxHeight: expandedTrendIndex === index ? 'none' : '3em'
                    }}>
                      {trend.description}
                    </p>
                    {expandedTrendIndex === index && (
                      <div style={{ 
                        marginTop: '0.5rem', 
                        paddingTop: '0.5rem', 
                        borderTop: '1px solid rgba(255,255,255,0.05)', 
                        fontSize: '0.7rem',
                        color: 'var(--accent-light)'
                      }}>
                        💡 Click to collapse view
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textAlign: 'center', padding: '2rem' }}>No trending updates loaded.</p>
            )}
          </div>
        </div>
      )}

      {/* Section 2: Personalization & Roadmap */}
      {selectedDomain ? (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '1.25rem' }} className="grid-2">
          
          {/* Preferences form */}
          <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <h3 style={{ fontSize: '1.1rem', color: '#ffffff', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Sliders size={18} style={{ color: 'var(--accent-light)' }} />
              <span>Tailor Focus</span>
            </h3>
            
            <form onSubmit={handlePrioritize} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label>Target Level</label>
                <select className="form-control" value={level} onChange={(e) => setLevel(e.target.value)}>
                  <option value="beginner">Junior / Beginner</option>
                  <option value="intermediate">Mid-Level / Intermediate</option>
                  <option value="advanced">Senior / Expert</option>
                </select>
              </div>

              <div className="form-group" style={{ marginBottom: 0 }}>
                <label>Target Role</label>
                <input 
                  type="text" 
                  className="form-control" 
                  value={targetRole} 
                  onChange={(e) => setTargetRole(e.target.value)} 
                  placeholder="Backend Engineer"
                />
              </div>

              <div className="form-group" style={{ marginBottom: 0 }}>
                <label>Target Company Class</label>
                <select className="form-control" value={targetCompany} onChange={(e) => setTargetCompany(e.target.value)}>
                  <option value="FAANG">High-Scale Enterprise</option>
                  <option value="Startup">Early / Series A Startup</option>
                  <option value="Enterprise">Mid-Size Tech Firm</option>
                </select>
              </div>

              <div className="form-group" style={{ marginBottom: 0 }}>
                <label>Knowledge Gaps</label>
                <input 
                  type="text" 
                  className="form-control" 
                  value={weakTopics} 
                  onChange={(e) => setWeakTopics(e.target.value)} 
                  placeholder="e.g. transactions, indexes"
                />
              </div>

              <button type="submit" className="btn-primary" disabled={prioritizing} style={{ justifyContent: 'center', marginTop: '0.5rem' }}>
                <CheckCircle size={14} />
                <span>{prioritizing ? "Constructing..." : "Generate Roadmap"}</span>
              </button>
            </form>
          </div>

          {/* Topics Heatmap & Selection */}
          <div className="glass-card" style={{ minHeight: '380px', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <h3 style={{ fontSize: '1.1rem', color: '#ffffff' }}>Topic Mastery & Roadmap</h3>
            
            {!prioritizedData ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', flex: 1, color: 'var(--text-muted)' }}>
                <Settings size={36} style={{ marginBottom: '0.75rem', opacity: 0.2 }} />
                <p style={{ fontSize: '0.85rem' }}>Customize preferences on the left to review prioritize topics.</p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <TopicHeatmap topics={getHeatmapTopics()} />
                
                <h4 style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', borderTop: '1px solid var(--border)', paddingTop: '1rem', marginTop: '0.5rem' }}>
                  Select topic to study or start mock assessment:
                </h4>
                
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                  {prioritizedData.important_topics.map((topic, i) => (
                    <button 
                      key={topic}
                      onClick={() => setSelectedTopic(topic)}
                      className="btn-secondary"
                      style={{
                        padding: '0.5rem 0.85rem',
                        fontSize: '0.8rem',
                        borderColor: selectedTopic === topic ? 'var(--accent)' : 'var(--border)',
                        background: selectedTopic === topic ? 'rgba(99, 102, 241, 0.08)' : 'rgba(255,255,255,0.02)',
                        color: selectedTopic === topic ? '#ffffff' : 'var(--text-secondary)'
                      }}
                    >
                      <span>{topic}</span>
                    </button>
                  ))}
                </div>

                {selectedTopic && (
                  <div style={{ 
                    marginTop: '1rem', 
                    padding: '1rem', 
                    background: 'rgba(255,255,255,0.01)', 
                    border: '1px dashed var(--border)', 
                    borderRadius: 'var(--radius-sm)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.75rem'
                  }}>
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                      Selected Topic: <strong style={{ color: '#ffffff' }}>{selectedTopic}</strong>
                    </span>
                    <div style={{ display: 'flex', gap: '0.75rem' }}>
                      <button 
                        onClick={() => handleStudyBasics(selectedTopic)} 
                        className="btn-secondary"
                        style={{ flex: 1, justifyContent: 'center', fontSize: '0.8rem', padding: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}
                      >
                        <Sparkles size={12} style={{ color: 'var(--accent-light)' }} />
                        <span>Study Basics</span>
                      </button>
                      <button 
                        onClick={() => handleFetchQuestion(selectedTopic)} 
                        className="btn-primary"
                        style={{ flex: 1, justifyContent: 'center', fontSize: '0.8rem', padding: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}
                      >
                        <Terminal size={12} />
                        <span>Practice Challenge</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="glass-card" style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)', border: '1px solid var(--border)' }}>
          <BookOpen size={36} style={{ marginBottom: '0.75rem', opacity: 0.3 }} />
          <p style={{ fontSize: '0.9rem' }}>Select a domain from the catalog above to construct your curriculum roadmap.</p>
        </div>
      )}

      {/* Challenge Sandbox / IDE */}
      {selectedTopic && (
        <div className="glass-card" style={{ border: '1px solid var(--border)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '1rem' }}>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '1.1rem' }}>
              <Terminal size={18} style={{ color: 'var(--accent-light)' }} />
              <span>Practice Workspace: {selectedTopic}</span>
            </h3>
            <button 
              onClick={() => handleFetchQuestion(selectedTopic, true)}
              className="btn-secondary"
              style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}
            >
              <RefreshCw size={12} />
              <span>Next/New Question</span>
            </button>
          </div>

          {generatingQuestion ? (
            <div style={{ display: 'flex', justifyContent: 'center', padding: '4rem' }}>
              <div className="spinner"></div>
            </div>
          ) : question ? (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }} className="grid-2">
              
              {/* Left Side: Question instructions */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div style={{ background: 'rgba(0, 0, 0, 0.15)', border: '1px solid var(--border)', padding: '1.25rem', borderRadius: 'var(--radius-sm)' }}>
                  <span className="badge badge-primary" style={{ marginBottom: '0.75rem' }}>
                    {question.is_coding ? "Coding Session" : `Theory Question`}
                  </span>
                  <h4 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>
                    {question.is_coding ? question.title : "Concept check"}
                  </h4>
                  <p style={{ color: 'var(--text-secondary)', lineHeight: '1.5', fontSize: '0.85rem', whiteSpace: 'pre-line' }}>
                    {question.is_coding ? question.description : question.question}
                  </p>
                </div>

                {/* Conceptual validation answers */}
                {!question.is_coding && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {question.type === 'mcq' ? (
                      question.choices.map((choice, i) => (
                        <div 
                          key={i}
                          onClick={() => setUserMCQIndex(i)}
                          className="glass-card"
                          style={{
                            cursor: 'pointer',
                            padding: '0.85rem 1rem',
                            fontSize: '0.85rem',
                            border: userMCQIndex === i ? '1px solid var(--accent)' : '1px solid var(--border)',
                            background: userMCQIndex === i ? 'rgba(99, 102, 241, 0.05)' : 'rgba(0,0,0,0.1)'
                          }}
                        >
                          <strong style={{ marginRight: '0.5rem', color: userMCQIndex === i ? 'var(--accent-light)' : 'var(--text-secondary)' }}>
                            Option {i + 1}
                          </strong>
                          <span>{choice}</span>
                        </div>
                      ))
                    ) : (
                      <textarea
                        className="form-control"
                        rows={5}
                        placeholder="Provide details about your explanation..."
                        value={userTheoryAnswer}
                        onChange={(e) => setUserTheoryAnswer(e.target.value)}
                        style={{ fontSize: '0.85rem' }}
                      />
                    )}

                    <button 
                      onClick={handleSubmitAnswer} 
                      className="btn-primary" 
                      disabled={grading}
                      style={{ justifyContent: 'center', marginTop: '0.5rem' }}
                    >
                      <CheckCircle size={14} />
                      <span>{grading ? "Evaluating..." : "Submit Answer"}</span>
                    </button>
                  </div>
                )}
              </div>

              {/* Right Side: Code editor pane */}
              {question.is_coding && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  
                  {/* Editor Menu Bar */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(0,0,0,0.2)', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border)' }}>
                    
                    {/* Tabs */}
                    <div style={{ display: 'flex', gap: '0.25rem' }}>
                      <button 
                        onClick={() => setActiveTab('editor')}
                        style={{
                          background: activeTab === 'editor' ? 'rgba(255,255,255,0.05)' : 'none',
                          border: 'none',
                          color: activeTab === 'editor' ? '#ffffff' : 'var(--text-secondary)',
                          fontSize: '0.8rem',
                          padding: '0.4rem 0.75rem',
                          borderRadius: '3px',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.25rem'
                        }}
                      >
                        <FileCode size={12} />
                        <span>main.{selectedLanguage === 'javascript' ? 'js' : selectedLanguage === 'java' ? 'java' : selectedLanguage === 'c++' ? 'cpp' : 'py'}</span>
                      </button>

                      <button 
                        onClick={() => setActiveTab('testcases')}
                        style={{
                          background: activeTab === 'testcases' ? 'rgba(255,255,255,0.05)' : 'none',
                          border: 'none',
                          color: activeTab === 'testcases' ? '#ffffff' : 'var(--text-secondary)',
                          fontSize: '0.8rem',
                          padding: '0.4rem 0.75rem',
                          borderRadius: '3px',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.25rem'
                        }}
                      >
                        <CheckSquare size={12} />
                        <span>test_cases.json</span>
                      </button>
                    </div>

                    {/* Language selector */}
                    <select 
                      className="form-control" 
                      style={{ width: '120px', padding: '0.25rem 0.5rem', fontSize: '0.8rem', height: '28px' }} 
                      value={selectedLanguage}
                      onChange={(e) => setSelectedLanguage(e.target.value)}
                    >
                      <option value="python">Python</option>
                      <option value="javascript">JavaScript</option>
                      <option value="java">Java</option>
                      <option value="c++">C++</option>
                    </select>
                  </div>

                  {/* Tab contents */}
                  {activeTab === 'editor' && (
                    <textarea
                      className="form-control"
                      rows={12}
                      style={{
                        fontFamily: 'Consolas, Monaco, monospace',
                        fontSize: '0.85rem',
                        background: '#04060a',
                        borderColor: 'var(--border)',
                        color: '#93c5fd',
                        lineHeight: '1.4',
                        padding: '0.75rem'
                      }}
                      value={userCode}
                      onChange={(e) => setUserCode(e.target.value)}
                    />
                  )}

                  {activeTab === 'testcases' && (
                    <div style={{ 
                      background: '#04060a', 
                      border: '1px solid var(--border)', 
                      borderRadius: 'var(--radius-sm)', 
                      padding: '1rem', 
                      height: '245px', 
                      overflowY: 'auto',
                      fontFamily: 'monospace',
                      fontSize: '0.8rem'
                    }}>
                      <span style={{ color: 'var(--accent-light)' }}>// Test Case Configurations</span>
                      <pre style={{ marginTop: '0.5rem', color: 'var(--text-secondary)', whiteSpace: 'pre-wrap' }}>
                        {JSON.stringify(question.test_cases || [], null, 2)}
                      </pre>
                    </div>
                  )}

                  {activeTab === 'console' && (
                    <div style={{ 
                      background: '#04060a', 
                      border: '1px solid var(--border)', 
                      borderRadius: 'var(--radius-sm)', 
                      padding: '1rem', 
                      height: '245px', 
                      overflowY: 'auto',
                      fontFamily: 'monospace',
                      fontSize: '0.8rem'
                    }}>
                      <span style={{ color: 'var(--text-muted)' }}>// compiler stdout console</span>
                      {executingCode ? (
                        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginTop: '1rem' }}>
                          <div className="spinner" style={{ width: '14px', height: '14px' }} />
                          <span>Running solution test suites...</span>
                        </div>
                      ) : executionResult ? (
                        <pre style={{ marginTop: '0.5rem', color: executionResult.success ? 'var(--success)' : 'var(--danger)', whiteSpace: 'pre-wrap' }}>
                          {executionResult.success 
                            ? `SUCCESS\nstdout:\n${executionResult.stdout}`
                            : `COMPILER ERROR\nstderr:\n${executionResult.stderr || executionResult.error_type}`
                          }
                        </pre>
                      ) : (
                        <p style={{ color: 'var(--text-muted)', marginTop: '0.5rem' }}>No code has been executed yet.</p>
                      )}
                    </div>
                  )}

                  <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.25rem' }}>
                    <button 
                      onClick={handleExecuteCode} 
                      className="btn-secondary" 
                      disabled={executingCode}
                      style={{ flex: 1, justifyContent: 'center', padding: '0.6rem' }}
                    >
                      <Play size={14} />
                      <span>Run Code</span>
                    </button>
                    
                    <button 
                      onClick={handleSubmitAnswer} 
                      className="btn-primary" 
                      disabled={grading}
                      style={{ flex: 1, justifyContent: 'center', padding: '0.6rem' }}
                    >
                      <CheckCircle size={14} />
                      <span>Submit Solution</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
              <Terminal size={36} style={{ opacity: 0.2 }} />
              <div>
                <p style={{ fontSize: '0.95rem', fontWeight: 600, color: '#ffffff', marginBottom: '0.5rem' }}>Ready to Practice?</p>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Click <strong style={{ color: 'var(--accent-light)' }}>"Practice Challenge"</strong> above to generate a question for <strong style={{ color: '#ffffff' }}>{selectedTopic}</strong>.</p>
              </div>
              <button
                onClick={() => handleFetchQuestion(selectedTopic)}
                className="btn-primary"
                style={{ padding: '0.6rem 1.5rem', fontSize: '0.9rem' }}
              >
                <Terminal size={14} />
                <span>Generate Challenge Now</span>
              </button>
            </div>
          )}

          {/* Grading results */}
          {gradeResult && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', marginTop: '1.5rem' }}>
              <div 
                className="glass-card" 
                style={{ 
                  borderLeft: gradeResult.status === 'correct' ? '4px solid var(--success)' : '4px solid var(--danger)',
                  background: 'rgba(0,0,0,0.1)',
                  padding: '1.25rem'
                }}
              >
                <h4 style={{ fontSize: '1.05rem', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Award size={18} style={{ color: gradeResult.status === 'correct' ? 'var(--success)' : 'var(--danger)' }} />
                  <span>Result: {gradeResult.status?.toUpperCase()}</span>
                </h4>
                <h2 style={{ fontSize: '1.8rem', fontWeight: 800, marginBottom: '0.5rem' }}>Score: {gradeResult.score} / 100</h2>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', lineHeight: '1.4' }}>{gradeResult.feedback}</p>
              </div>

              {/* Reference/Model Solution Display */}
              <div className="glass-card" style={{ border: '1px solid var(--border)', padding: '1.25rem' }}>
                <h4 style={{ fontSize: '1rem', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent-light)' }}>
                  <Code size={16} />
                  <span>Reference / Model Solution</span>
                </h4>
                {question.is_coding ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Optimal reference implementation in {question.language || selectedLanguage}:</p>
                    <pre style={{ 
                      background: '#04060a', 
                      border: '1px solid var(--border)', 
                      borderRadius: 'var(--radius-sm)', 
                      padding: '1rem', 
                      overflowX: 'auto',
                      fontFamily: 'Consolas, Monaco, monospace',
                      fontSize: '0.8rem',
                      color: '#a7f3d0',
                      whiteSpace: 'pre-wrap'
                    }}>
                      {question.model_solution}
                    </pre>
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {question.type === 'mcq' ? (
                      <div>
                        <p style={{ fontSize: '0.85rem', marginBottom: '0.25rem' }}>
                          Correct Option: <strong style={{ color: 'var(--success)' }}>Option {question.correct_choice + 1}</strong>: {question.choices[question.correct_choice]}
                        </p>
                        {question.model_answer && (
                          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.5rem', whiteSpace: 'pre-wrap' }}>
                            <strong>Explanation:</strong> {question.model_answer}
                          </p>
                        )}
                      </div>
                    ) : (
                      <div>
                        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}><strong>Suggested Answer Key / Rubric:</strong></p>
                        <p style={{ 
                          fontSize: '0.85rem', 
                          background: 'rgba(0,0,0,0.2)', 
                          border: '1px solid var(--border)', 
                          borderRadius: 'var(--radius-sm)',
                          padding: '0.75rem',
                          marginTop: '0.25rem',
                          whiteSpace: 'pre-wrap',
                          color: '#e2e8f0'
                        }}>
                          {question.model_answer}
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default LearningHub;
