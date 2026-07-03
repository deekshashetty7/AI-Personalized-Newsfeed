import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add token
apiClient.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      if (typeof window !== 'undefined') {
        const refreshToken = localStorage.getItem('refresh_token');
        
        if (refreshToken) {
          try {
            // Attempt to refresh token
            const response = await axios.post(`${API_URL}/auth/refresh/`, {
              refresh: refreshToken,
            });

            const { access } = response.data;
            localStorage.setItem('access_token', access);

            originalRequest.headers.Authorization = `Bearer ${access}`;
            return apiClient(originalRequest);
          } catch (refreshError) {
            // Refresh failed, logout user
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/login';
            return Promise.reject(refreshError);
          }
        }
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;

// API Functions

// Auth
export const authAPI = {
  verifyEmail: (email: string) => {
    console.log('📧 Verifying email:', email);
    return apiClient.post('/auth/verify-email/', { email });
  },

  register: (data: {
    name: string;
    email: string;
    password: string;
    confirm_password: string;
    interests?: string[];
  }) => {
    console.log('📝 Registering user:', { ...data, password: '***', confirm_password: '***' });
    return apiClient.post('/auth/register/', data);
  },

  login: (email: string, password: string) => {
    console.log('🔐 Logging in user:', email);
    return apiClient.post('/auth/login/', { email, password });
  },

  getProfile: () => apiClient.get('/user/profile/'),

  updateProfile: (data: { name?: string; interests?: string[]; profile_photo?: string }) =>
    apiClient.put('/user/profile/update/', data),

  changePassword: (data: { old_password: string; new_password: string }) =>
    apiClient.post('/user/change-password/', data),

  updateActiveTime: (timeSeconds: number, isSessionEnd: boolean = false) =>
    apiClient.post('/user/active-time/', { time_seconds: timeSeconds, is_session_end: isSessionEnd }),

  getSessionData: () => 
    apiClient.get('/user/session/'),

  requestPasswordReset: (email: string) =>
    apiClient.post('/auth/forgot-password/', { email }),

  verifyResetOTP: (email: string, otp: string) =>
    apiClient.post('/auth/verify-reset-otp/', { email, otp }),

  resetPasswordWithOTP: (email: string, otp: string, newPassword: string) =>
    apiClient.post('/auth/reset-password-otp/', { email, otp, new_password: newPassword }),

  resetPassword: (token: string, newPassword: string) =>
    apiClient.post('/auth/reset-password/', { token, new_password: newPassword }),
};

// News
export const newsAPI = {
  getArticles: (params?: { category?: string; search?: string; page?: number; page_size?: number; unlimited?: boolean }) => {
    // Add cache-busting timestamp
    const requestParams = { 
      page_size: 500, 
      unlimited: true, 
      ...params,
      _t: Date.now() // Prevent browser caching
    };
    console.log('🌐 API Request params:', requestParams);
    return apiClient.get('/news/', { params: requestParams });
  },

  getArticle: (id: string) => apiClient.get(`/news/${id}/`),

  refreshNews: (category?: string) =>
    apiClient.post('/news/refresh/', { category }),

  getCategories: () => apiClient.get('/categories/'),

  getTrending: () => apiClient.get('/trending/'),

  fetchFullContent: (url: string, title?: string) => {
    const params: any = { url };
    if (title) params.title = title;
    return apiClient.get('/news/fetch-content/', { params });
  },

  getRecommendations: () => apiClient.get('/recommendations/'),

  recordInteraction: (article_id: string, action: string, comment_text?: string, dwell_time?: number) => {
    const data: any = { article_id, action };
    if (comment_text) data.comment_text = comment_text;
    if (dwell_time) data.dwell_time = dwell_time;
    return apiClient.post('/interactions/', data);
  },
};

// Knowledge Box
export const knowledgeBoxAPI = {
  getKnowledgeBox: () => apiClient.get('/knowledge-box/'),
};

// Interactions
export const interactionAPI = {
  recordInteraction: (article_id: string, action: string, comment_text?: string) =>
    apiClient.post('/interactions/', { article_id, action, comment_text }),

  create: (data: { article_id: string; action: string; comment_text?: string; dwell_time?: number }) =>
    apiClient.post('/interactions/', data),

  remove: (article_id: string, action: string) =>
    apiClient({
      method: 'delete',
      url: '/interactions/remove/',
      data: { article_id, action }
    }),

  getUserInteractions: (action?: string) =>
    apiClient.get('/interactions/my/', { params: { action } }),

  getArticleComments: (articleId: string) =>
    apiClient.get('/interactions/comments/', { params: { article_id: articleId } }),

  generateAiSnapshot: (article_id: string) =>
    apiClient.post('/interactions/ai-snapshot/', { article_id }),
};

// Recommendations
export const recommendationAPI = {
  get: () => apiClient.get('/recommendations/'),
};

// Streak
export const streakAPI = {
  getUserStreak: () => apiClient.get('/user/streak/'),
};
