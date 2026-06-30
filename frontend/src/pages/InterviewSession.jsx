import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { interviewApi } from '../services/api';
import { Send, Clock, Sparkles, AlertOctagon, Mic, MicOff, Volume2, VolumeX, RefreshCw } from 'lucide-react';

const InterviewSession = () => {
  const navigate = useNavigate();
  const [sessionId, setSessionId] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [questionCount, setQuestionCount] = useState(1);
  const [timer, setTimer] = useState(0); // in seconds
  const [error, setError] = useState(null);

  // Audio / Speech State
  const [isMuted, setIsMuted] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [recognitionSupported, setRecognitionSupported] = useState(false);
  const recognitionRef = useRef(null);

  // 1. Initialize Speech Recognition
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      setRecognitionSupported(true);
      const rec = new SpeechRecognition();
      rec.continuous = true;
      rec.interimResults = true;
      rec.lang = 'en-US';

      rec.onresult = (event) => {
        const speechText = Array.from(event.results)
          .map(result => result[0])
          .map(result => result.transcript)
          .join('');
        setAnswer(speechText);
      };

      rec.onerror = (event) => {
        console.error("Speech recognition error", event.error);
        if (event.error !== 'no-speech') {
          setIsListening(false);
        }
      };

      rec.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = rec;
    }
  }, []);

  // 2. Start session on mount
  useEffect(() => {
    const matchId = localStorage.getItem('current_match_id');
    if (!matchId) {
      setError("Please run a Match Analysis to create a target job profile before beginning an interview.");
      setLoading(false);
      return;
    }

    const initInterview = async () => {
      try {
        setLoading(true);
        const res = await interviewApi.start(matchId);
        setSessionId(res.session_id);
        setCurrentQuestion(res.current_question);
        localStorage.setItem('current_session_id', res.session_id);
      } catch (err) {
        setError(err.response?.data?.detail || "Could not initialize interview session.");
      } finally {
        setLoading(false);
      }
    };

    initInterview();
  }, []);

  // 3. Text-to-Speech (TTS) effect on question change
  const speakQuestion = (textToSpeak) => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      if (!isMuted && textToSpeak) {
        const utterance = new SpeechSynthesisUtterance(textToSpeak);
        utterance.rate = 0.95; // Slightly slower, more natural pace
        
        // Try to pick a premium/natural sounding voice if available
        const voices = window.speechSynthesis.getVoices();
        const preferredVoice = voices.find(voice => 
          voice.name.includes('Google US English') || 
          voice.name.includes('Microsoft David') || 
          voice.lang.startsWith('en-US')
        );
        if (preferredVoice) utterance.voice = preferredVoice;

        window.speechSynthesis.speak(utterance);
      }
    }
  };

  useEffect(() => {
    if (!loading && currentQuestion) {
      speakQuestion(currentQuestion);
    }
    return () => {
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, [currentQuestion, loading, isMuted]);

  // 4. Timer effect
  useEffect(() => {
    if (loading || submitting || error) return;
    const interval = setInterval(() => {
      setTimer((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, [loading, submitting, error]);

  const formatTime = (secs) => {
    const m = Math.floor(secs / 60).toString().padStart(2, '0');
    const s = (secs % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  // Toggle listening
  const handleToggleListening = () => {
    if (!recognitionRef.current) {
      alert("Speech Recognition is not supported in this browser. Please use Google Chrome or Edge.");
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      try {
        recognitionRef.current.start();
        setIsListening(true);
      } catch (err) {
        console.error(err);
      }
    }
  };

  const handleNext = async (e) => {
    if (e) e.preventDefault();
    if (!answer.trim() || submitting) return;

    // Stop listening before submitting
    if (isListening && recognitionRef.current) {
      recognitionRef.current.stop();
      setIsListening(false);
    }

    try {
      setSubmitting(true);
      const res = await interviewApi.submitAnswer(sessionId, answer);
      
      if (res.is_finished) {
        // Automatically wrap up session
        await interviewApi.end(sessionId);
        navigate(`/evaluation-results/${sessionId}`);
      } else {
        setCurrentQuestion(res.next_question);
        setAnswer('');
        setQuestionCount((prev) => prev + 1);
      }
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to submit answer.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleEndSession = async () => {
    if (!window.confirm("Are you sure you want to end this interview session? You will receive evaluation on completed questions only.")) return;
    
    if (isListening && recognitionRef.current) {
      recognitionRef.current.stop();
      setIsListening(false);
    }

    try {
      setLoading(true);
      await interviewApi.end(sessionId);
      navigate(`/evaluation-results/${sessionId}`);
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to terminate session.");
      setLoading(false);
    }
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
      <div className="glass-card" style={{ textAlign: 'center', padding: '3rem', maxWidth: '600px', margin: '2rem auto' }}>
        <AlertOctagon size={48} style={{ color: 'var(--danger)', marginBottom: '1rem' }} />
        <h3 style={{ marginBottom: '1rem' }}>Initialization Error</h3>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>{error}</p>
        <button onClick={() => navigate('/match-analysis')} className="btn-primary">Return to Match Analysis</button>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem', maxWidth: '900px', margin: '0 auto' }}>
      {/* Top Banner */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span className="badge badge-primary">Active Interview</span>
          <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Question {questionCount}</span>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', background: 'rgba(255,255,255,0.05)', padding: '0.5rem 0.8rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
            <Clock size={16} style={{ color: 'var(--accent-light)' }} />
            <span style={{ fontFamily: 'monospace', fontWeight: 'bold' }}>{formatTime(timer)}</span>
          </div>
          <button onClick={handleEndSession} className="btn-secondary" style={{ color: 'var(--danger)', borderColor: 'rgba(239,68,68,0.2)' }}>
            End Session
          </button>
        </div>
      </div>

      {/* Main Dialogue Card */}
      <div className="glass-card" style={{ border: '1px solid var(--border-active)', boxShadow: '0 8px 32px var(--accent-glow)', position: 'relative' }}>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start', marginBottom: '1rem' }}>
          <div style={{ background: 'var(--accent)', color: '#ffffff', padding: '0.6rem', borderRadius: 'var(--radius-sm)', fontWeight: 'bold', fontSize: '0.85rem' }}>AI</div>
          <div style={{ flex: 1 }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', fontWeight: 600 }}>Interviewer</span>
            <p style={{ fontSize: '1.25rem', color: '#ffffff', lineHeight: 1.5, marginTop: '0.25rem', paddingRight: '3rem' }}>{currentQuestion}</p>
          </div>
        </div>

        {/* Audio controls in the question box */}
        <div style={{ position: 'absolute', top: '1.25rem', right: '1.25rem', display: 'flex', gap: '0.5rem' }}>
          <button 
            onClick={() => speakQuestion(currentQuestion)}
            className="btn-icon" 
            title="Read Question Aloud"
            style={{ padding: '0.4rem', background: 'rgba(255,255,255,0.05)', borderRadius: '50%', border: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', color: 'var(--text-primary)' }}
          >
            <RefreshCw size={14} />
          </button>
          <button 
            onClick={() => setIsMuted(prev => !prev)} 
            className="btn-icon" 
            title={isMuted ? "Unmute AI Voice" : "Mute AI Voice"}
            style={{ padding: '0.4rem', background: 'rgba(255,255,255,0.05)', borderRadius: '50%', border: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', color: isMuted ? 'var(--text-muted)' : 'var(--accent-light)' }}
          >
            {isMuted ? <VolumeX size={14} /> : <Volume2 size={14} />}
          </button>
        </div>
      </div>

      {/* Answer Area */}
      <form onSubmit={handleNext} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        <div className="glass-card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem', border: isListening ? '1px solid var(--accent)' : '1px solid var(--border)', transition: 'border 0.3s ease' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)' }}>Your Response</span>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              {recognitionSupported ? "Speak or type your response clearly." : "Type your response clearly."}
            </span>
          </div>

          <div style={{ position: 'relative' }}>
            <textarea
              className="form-control"
              rows={6}
              required
              placeholder={isListening ? "Listening... start speaking your answer." : "Click the microphone to speak, or start typing..."}
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              disabled={submitting}
              style={{ fontSize: '1.05rem', lineHeight: '1.5', resize: 'vertical', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', width: '100%', padding: '1rem' }}
            />
            
            {/* Listening Waveform Overlay */}
            {isListening && (
              <div style={{ position: 'absolute', bottom: '0.75rem', left: '1rem', display: 'flex', gap: '4px', alignItems: 'center' }}>
                <span className="pulse-dot" style={{ width: '8px', height: '8px', background: 'var(--accent)', borderRadius: '50%', animation: 'ping 1s cubic-bezier(0, 0, 0.2, 1) infinite' }}></span>
                <span style={{ fontSize: '0.75rem', color: 'var(--accent-light)', fontWeight: 600 }}>Mic Active</span>
              </div>
            )}
          </div>

          {/* Voice Control & Submitting Bar */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
            {recognitionSupported ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <button
                  type="button"
                  onClick={handleToggleListening}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '0.5rem',
                    padding: '0.75rem 1.25rem',
                    borderRadius: '30px',
                    border: 'none',
                    fontWeight: 600,
                    cursor: 'pointer',
                    background: isListening ? 'var(--danger)' : 'var(--accent)',
                    color: '#ffffff',
                    boxShadow: isListening ? '0 0 15px rgba(239,68,68,0.4)' : 'none',
                    transition: 'all 0.3s ease'
                  }}
                >
                  {isListening ? (
                    <>
                      <MicOff size={16} />
                      <span>Stop Listening</span>
                    </>
                  ) : (
                    <>
                      <Mic size={16} />
                      <span>Speak Answer</span>
                    </>
                  )}
                </button>
                {isListening && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
                    <div style={{ height: '3px', width: '3px', background: 'var(--accent-light)', borderRadius: '50%', animation: 'bounce 0.6s infinite alternate' }}></div>
                    <div style={{ height: '7px', width: '3px', background: 'var(--accent-light)', borderRadius: '50%', animation: 'bounce 0.6s infinite alternate 0.2s' }}></div>
                    <div style={{ height: '4px', width: '3px', background: 'var(--accent-light)', borderRadius: '50%', animation: 'bounce 0.6s infinite alternate 0.4s' }}></div>
                  </div>
                )}
              </div>
            ) : (
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Voice input requires Chrome/Edge/Safari.
              </div>
            )}

            <button
              type="submit"
              className="btn-primary"
              disabled={!answer.trim() || submitting}
              style={{ gap: '0.75rem', padding: '0.75rem 1.5rem' }}
            >
              {submitting ? (
                <div className="spinner" style={{ width: '20px', height: '20px' }} />
              ) : (
                <>
                  <span>Submit Answer</span>
                  <Send size={16} />
                </>
              )}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};

export default InterviewSession;
