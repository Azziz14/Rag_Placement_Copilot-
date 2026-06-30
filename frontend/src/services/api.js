import axios from 'axios';
import { supabase } from './supabaseClient';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
});

// Request interceptor to automatically add Supabase JWT Bearer token
api.interceptors.request.use(
  async (config) => {
    const { data: { session } } = await supabase.auth.getSession();
    if (session?.access_token) {
      config.headers.Authorization = `Bearer ${session.access_token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export const resumeApi = {
  upload: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/resume/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

export const jdApi = {
  upload: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/jd/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  analyzeText: async (rawText) => {
    const response = await api.post('/jd/analyze-text', { raw_text: rawText });
    return response.data;
  },
};

export const matcherApi = {
  analyze: async (resumeId, jdId) => {
    const response = await api.post('/match/analyze', {
      resume_id: resumeId,
      job_description_id: jdId,
    });
    return response.data;
  },
};

export const questionApi = {
  generate: async (matchId) => {
    const response = await api.post('/questions/generate', { match_id: matchId });
    return response.data;
  },
};

export const interviewApi = {
  start: async (matchId) => {
    const response = await api.post('/interview/start', { match_id: matchId });
    return response.data;
  },
  submitAnswer: async (sessionId, answerText) => {
    const response = await api.post('/interview/answer', {
      session_id: sessionId,
      answer: answerText,
    });
    return response.data;
  },
  end: async (sessionId) => {
    const response = await api.post('/interview/end', { session_id: sessionId });
    return response.data;
  },
};

export const evaluationApi = {
  analyze: async (sessionId) => {
    const response = await api.post('/evaluation/analyze', { session_id: sessionId });
    return response.data;
  },
};

export const weaknessApi = {
  analyze: async (sessionId) => {
    const response = await api.post('/weakness/analyze', { session_id: sessionId });
    return response.data;
  },
};

export const roadmapApi = {
  generate: async (sessionId) => {
    const response = await api.post('/roadmap/generate', { session_id: sessionId });
    return response.data;
  },
};

export const progressApi = {
  getDashboard: async (userId) => {
    const response = await api.get(`/progress/dashboard/${userId}`);
    return response.data;
  },
  getHistory: async (userId) => {
    const response = await api.get(`/progress/history/${userId}`);
    return response.data;
  },
};

export const tailorApi = {
  generate: async (payload) => {
    const response = await api.post('/tailor/generate', payload);
    return response.data;
  },
  download: async (tailoredResumeId) => {
    const response = await api.get(`/tailor/download/${tailoredResumeId}`, {
      responseType: 'blob',
    });
    return response.data;
  },
};

export const adaptiveApi = {
  generateProfile: async (userId, force = false) => {
    const response = await api.post('/adaptive/generate', { user_id: userId, force_refresh: force });
    return response.data;
  },
};

export const learningApi = {
  getDomainTopics: async (domain) => {
    const response = await api.post('/learning/domain', { domain });
    return response.data;
  },
  prioritizeTopics: async (payload) => {
    const response = await api.post('/learning/topics', payload);
    return response.data;
  },
  generateQuestion: async (payload) => {
    const response = await api.post('/learning/questions', payload);
    return response.data;
  },
  submitAnswer: async (payload) => {
    const response = await api.post('/learning/submit', payload);
    return response.data;
  },
  executeCode: async (payload) => {
    const response = await api.post('/learning/code/execute', payload);
    return response.data;
  },
  explainTopic: async (payload) => {
    const response = await api.post('/learning/explain', payload);
    return response.data;
  },
  getTrends: async (payload) => {
    const response = await api.post('/learning/trends', payload);
    return response.data;
  },
};

export default api;
