// Configuration using Vite environment variables with fallbacks
const config = {
  frontend: {
    host: import.meta.env.VITE_APP_FRONTEND_HOST || 'localhost',
    port: parseInt(import.meta.env.VITE_APP_FRONTEND_PORT || '3000')
  },
  backend: {
    host: import.meta.env.VITE_APP_BACKEND_HOST || 'localhost',
    port: parseInt(import.meta.env.VITE_APP_BACKEND_PORT || '8000')
  },
  websocket: {
    path: import.meta.env.VITE_APP_WS_PATH || 'ws/notifications/'
  }
};

export default config;
