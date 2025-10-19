import config from './config';

class WebSocketService {
  constructor() {
    this.socket = null;
    this.connected = false;
    this.callbacks = {
      taskUpdate: [],
    };
  }

  connect() {
    if (this.socket) {
      this.disconnect();
    }

    const token = localStorage.getItem('accessToken');
    if (!token) {
      console.error('No token available for WebSocket connection');
      return;
    }

    const wsUrl = `ws://${config.backend.host}:${config.backend.port}/${config.websocket.path}`;
    this.socket = new WebSocket(`${wsUrl}?token=${token}`);

    this.socket.onopen = () => {
      console.log('WebSocket connection established');
      this.connected = true;
    };

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('WebSocket received message:', data);
        
        // Handle task_result type coming from the backend
        if (data.type === 'task_result') {
          this.callbacks.taskUpdate.forEach(callback => {
            callback(data.data);
          });
        }
        // Keep the original task_update type for compatibility
        else if (data.type === 'task_update') {
          this.callbacks.taskUpdate.forEach(callback => {
            callback(data.task);
          });
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    this.socket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.socket.onclose = (event) => {
      console.log('WebSocket connection closed:', event.code, event.reason);
      this.connected = false;
      
      // Try to reconnect after 5 seconds
      setTimeout(() => {
        this.connect();
      }, 5000);
    };
  }

  disconnect() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
      this.connected = false;
    }
  }

  onTaskUpdate(callback) {
    this.callbacks.taskUpdate.push(callback);
    return () => {
      this.callbacks.taskUpdate = this.callbacks.taskUpdate.filter(cb => cb !== callback);
    };
  }
}

const webSocketService = new WebSocketService();
export default webSocketService;
