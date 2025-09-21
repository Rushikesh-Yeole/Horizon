// Central configuration for backend server URLs
export const API_CONFIG = {
  // Main backend server (for user management, auth, etc.)
  MAIN_BACKEND: {
    BASE_URL: 'http://127.0.0.1:8000',
    ENDPOINTS: {
      AUTH: {
        LOGIN: '/auth/login',
        REGISTER: '/user/register',
        LOGOUT: '/auth/logout'
      },
      USER: {
        PROFILE: '/user/profile',
        RESUME: '/user/resume',
        QUESTIONS: '/user/questions',
        ANSWERS: '/user/answers'
      }
    }
  },
  
  // JobForge backend server (for job recommendations and search)
  JOBFORGE_BACKEND: {
    BASE_URL: 'http://127.0.0.1:8001',
    ENDPOINTS: {
      RECOMMEND: '/recommend',
      SEARCH: '/search'
    }
  }
};

// Helper functions to build full URLs
export const buildMainBackendUrl = (endpoint: string) => {
  return `${API_CONFIG.MAIN_BACKEND.BASE_URL}${endpoint}`;
};

export const buildJobForgeUrl = (endpoint: string) => {
  return `${API_CONFIG.JOBFORGE_BACKEND.BASE_URL}${endpoint}`;
};

// Specific endpoint builders
export const getAuthUrl = (endpoint: keyof typeof API_CONFIG.MAIN_BACKEND.ENDPOINTS.AUTH) => {
  return buildMainBackendUrl(API_CONFIG.MAIN_BACKEND.ENDPOINTS.AUTH[endpoint]);
};

export const getUserUrl = (endpoint: keyof typeof API_CONFIG.MAIN_BACKEND.ENDPOINTS.USER) => {
  return buildMainBackendUrl(API_CONFIG.MAIN_BACKEND.ENDPOINTS.USER[endpoint]);
};

export const getJobForgeUrl = (endpoint: keyof typeof API_CONFIG.JOBFORGE_BACKEND.ENDPOINTS) => {
  return buildJobForgeUrl(API_CONFIG.JOBFORGE_BACKEND.ENDPOINTS[endpoint]);
};
