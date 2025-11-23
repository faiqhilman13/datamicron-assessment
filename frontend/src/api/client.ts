import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface Source {
  type: 'internal' | 'web';
  title: string;
  author?: string;
  url?: string;
  relevance_score: number;
  sentiment?: string;
}

export interface JudgeScores {
  relevance: number;
  factuality: number;
  completeness: number;
}

export interface ChatRequest {
  query: string;
  enable_web_search?: boolean;
}

export interface ChatResponse {
  response_id: string;
  answer: string;
  sources: Source[];
  confidence: number;
  judge_scores: JudgeScores;
  retrieval_method: string;
  web_search_triggered: boolean;
  timestamp: string;
}

export interface AnalyticsRequest {
  query: string;
}

export interface AnalyticsResponse {
  answer: string;
  data: Record<string, any>;
  query_type: string;
}

export interface HealthResponse {
  status: string;
  indexes_loaded: boolean;
  message: string;
}

export interface FeedbackRequest {
  response_id: string;
  query: string;
  answer: string;
  sources: Source[];
  feedback_type: 'positive' | 'negative';
  confidence: number;
  judge_scores: JudgeScores;
  retrieval_method: string;
  web_search_triggered: boolean;
  comment?: string;
}

export interface FeedbackResponse {
  status: string;
  feedback_id: string;
  message: string;
}

export interface FeedbackStats {
  total_feedback: number;
  positive: number;
  negative: number;
  positive_rate: number;
  web_search_feedback: any;
  confidence_correlation: any;
}

export const api = {
  async chat(request: ChatRequest): Promise<ChatResponse> {
    const response = await apiClient.post<ChatResponse>('/chat', request);
    return response.data;
  },

  async analytics(request: AnalyticsRequest): Promise<AnalyticsResponse> {
    const response = await apiClient.post<AnalyticsResponse>('/analytics', request);
    return response.data;
  },

  async health(): Promise<HealthResponse> {
    const response = await apiClient.get<HealthResponse>('/health');
    return response.data;
  },

  async submitFeedback(request: FeedbackRequest): Promise<FeedbackResponse> {
    const response = await apiClient.post<FeedbackResponse>('/feedback', request);
    return response.data;
  },

  async getFeedbackStats(): Promise<FeedbackStats> {
    const response = await apiClient.get<FeedbackStats>('/feedback/stats');
    return response.data;
  },

  async getRecommendations(): Promise<any> {
    const response = await apiClient.get<any>('/feedback/recommendations');
    return response.data;
  },
};

export default api;
