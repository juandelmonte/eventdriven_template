import axios from 'axios';
import { jwtDecode } from 'jwt-decode'; // Updated import syntax for v4
import config from './config';

// Create axios instance with base URL
const apiClient = axios.create({
  baseURL: `http://${config.backend.host}:${config.backend.port}/api`,
});

// Add request interceptor to add JWT token to requests
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor to handle token refresh
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refreshToken');
        if (!refreshToken) {
          throw new Error('No refresh token available');
        }
        
        const response = await axios.post(
          `http://${config.backend.host}:${config.backend.port}/api/users/token/refresh/`,
          { refresh: refreshToken }
        );
        
        const { access } = response.data;
        localStorage.setItem('accessToken', access);
        
        originalRequest.headers['Authorization'] = `Bearer ${access}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        // Refresh token failed, logout
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

const authService = {
  login: async (username, password) => {
    const response = await axios.post(
      `http://${config.backend.host}:${config.backend.port}/api/users/login/`,
      { username, password }
    );
    
    const { access, refresh } = response.data;
    localStorage.setItem('accessToken', access);
    localStorage.setItem('refreshToken', refresh);
    
    return jwtDecode(access);
  },
  
  register: async (userData) => {
    const response = await axios.post(
      `http://${config.backend.host}:${config.backend.port}/api/users/register/`,
      userData
    );
    return response.data;
  },
  
  logout: () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
  },
  
  isAuthenticated: () => {
    const token = localStorage.getItem('accessToken');
    if (!token) return false;
    
    try {
      const decoded = jwtDecode(token);
      const currentTime = Date.now() / 1000;
      
      return decoded.exp > currentTime;
    } catch (error) {
      return false;
    }
  },
  
  getCurrentUser: () => {
    const token = localStorage.getItem('accessToken');
    if (!token) return null;
    
    try {
      return jwtDecode(token);
    } catch (error) {
      return null;
    }
  }
};

const taskService = {
  getTasks: async () => {
    const response = await apiClient.get('/tasks/');
    return response.data;
  },
  
  getTaskById: async (taskId) => {
    const response = await apiClient.get(`/tasks/${taskId}/`);
    return response.data;
  },
  
  // Generic task submission
  submitTask: async (taskType, parameters = {}) => {
    const response = await apiClient.post(`/tasks/${taskType}/`, parameters);
    return response.data;
  },
  
  // Get available tasks
  getAvailableTasks: async () => {
    const response = await apiClient.get('/tasks/');
    return response.data;
  },
  
  // Convenience method for the random number task
  generateRandomNumber: async (minValue = 1, maxValue = 100) => {
    return taskService.submitTask('generate_random_number', { 
      min_value: minValue,
      max_value: maxValue
    });
  },
  
  // Convenience method for the reverse string task
  reverseString: async (text) => {
    return taskService.submitTask('reverse_string', { text });
  }
};

export { authService, taskService, apiClient };
