import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000'
});

api.interceptors.request.use((config) => {
  const demoId = localStorage.getItem('demo_session_id');
  if (demoId) {
    config.headers['X-Demo-Session-ID'] = demoId;
  }
  return config;
});

api.interceptors.response.use(
  (res) => {
    if (res.headers['x-credits-remaining']) {
      window.dispatchEvent(new CustomEvent('meter-update', { 
        detail: { 
          remaining: res.headers['x-credits-remaining'], 
          cost: res.headers['x-cost-this-run'] 
        } 
      }));
    }
    return res;
  },
  (error) => {
    if (error.response?.status === 402) {
      window.dispatchEvent(new Event('meter-exhausted'));
    }
    return Promise.reject(error);
  }
);

export default api;