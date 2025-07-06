import React, { useState, useEffect } from 'react';
import { taskService } from '../services/api';
import webSocketService from '../services/websocket';
import { useNavigate } from 'react-router-dom';
import TaskList from './TaskList';
import { authService } from '../services/api';

const Dashboard = () => {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [minValue, setMinValue] = useState(1);
  const [maxValue, setMaxValue] = useState(100);
  const [processing, setProcessing] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      navigate('/login');
      return;
    }
    
    // Connect WebSocket
    webSocketService.connect();
    
    // Set up WebSocket listener for task updates
    const unsubscribe = webSocketService.onTaskUpdate(task => {
      setTasks(prevTasks => {
        // Find and update the task if it exists
        const taskExists = prevTasks.some(t => t.task_id === task.task_id);
        
        if (taskExists) {
          return prevTasks.map(t => 
            t.task_id === task.task_id ? task : t
          );
        } else {
          // Add the new task
          return [task, ...prevTasks];
        }
      });
    });
    
    // Cleanup
    return () => {
      webSocketService.disconnect();
      unsubscribe();
    };
  }, [navigate]);
  
  const handleLogout = () => {
    authService.logout();
    navigate('/login');
  };
  
  const handleGenerateRandomNumber = async () => {
    try {
      setProcessing(true);
      await taskService.generateRandomNumber(parseInt(minValue), parseInt(maxValue));
    } catch (err) {
      setError('Failed to generate random number');
      console.error('Error generating random number:', err);
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1>Dashboard</h1>
        <button className="btn-logout" onClick={handleLogout}>Logout</button>
      </div>
      
      <div className="card">
        <h2>Generate Random Number</h2>
        <div className="form-group">
          <label htmlFor="minValue">Min Value:</label>
          <input 
            type="number" 
            id="minValue"
            value={minValue}
            onChange={e => setMinValue(e.target.value)}
            min="1"
          />
        </div>
        <div className="form-group">
          <label htmlFor="maxValue">Max Value:</label>
          <input 
            type="number" 
            id="maxValue"
            value={maxValue}
            onChange={e => setMaxValue(e.target.value)}
            min={minValue}
          />
        </div>
        <button 
          className="btn-primary" 
          onClick={handleGenerateRandomNumber}
          disabled={processing}
        >
          {processing ? 'Processing...' : 'Generate Random Number'}
        </button>
      </div>
      
      {error && <div className="error-message">{error}</div>}
      
      <div className="tasks-section">
        <h2>Tasks</h2>
        {loading ? (
          <p>Loading tasks...</p>
        ) : (
          <TaskList tasks={tasks} />
        )}
      </div>
    </div>
  );
};

export default Dashboard;
