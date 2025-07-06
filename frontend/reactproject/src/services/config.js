// Load configuration from global config.json file
// In a real app, this might be fetched from an API or environment variables
const config = {
  frontend: {
    host: 'localhost',
    port: 3000
  },
  backend: {
    host: 'localhost',
    port: 8000
  },
  websocket: {
    path: 'ws/notifications/'
  }
};

export default config;
