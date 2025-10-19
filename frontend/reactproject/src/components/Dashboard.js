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
  const [inputText, setInputText] = useState('');
  const [processing, setProcessing] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      navigate('/login');
      return;
    }
    
    console.log('Dashboard: Connecting WebSocket...');
    // Connect WebSocket
    webSocketService.connect();
    
    // Set up WebSocket listener for task updates
    const unsubscribe = webSocketService.onTaskUpdate(task => {
      console.log('Dashboard: Received task update:', task);
      setTasks(prevTasks => {
        // Find and update the task if it exists
        const taskExists = prevTasks.some(t => t.task_id === task.task_id);
        
        if (taskExists) {
          console.log('Dashboard: Updating existing task:', task.task_id);
          return prevTasks.map(t => 
            t.task_id === task.task_id ? task : t
          );
        } else {
          // Add the new task
          console.log('Dashboard: Adding new task:', task.task_id);
          return [task, ...prevTasks];
        }
      });
    });
    
    // Cleanup
    return () => {
      console.log('Dashboard: Disconnecting WebSocket...');
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
      setError('');
      await taskService.generateRandomNumber(parseInt(minValue), parseInt(maxValue));
    } catch (err) {
      setError('Failed to generate random number');
      console.error('Error generating random number:', err);
    } finally {
      setProcessing(false);
    }
  };
  
  const handleReverseString = async () => {
    try {
      if (!inputText.trim()) {
        setError('Please enter some text to reverse');
        return;
      }
      
      setProcessing(true);
      setError('');
      await taskService.reverseString(inputText);
      console.log('Reverse string task submitted');
    } catch (err) {
      setError('Failed to reverse string');
      console.error('Error reversing string:', err);
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
      
      <div className="card">
        <h2>Reverse String</h2>
        <div className="form-group">
          <label htmlFor="inputText">Text to Reverse:</label>
          <input 
            type="text" 
            id="inputText"
            value={inputText}
            onChange={e => setInputText(e.target.value)}
            placeholder="Enter text to reverse"
          />
        </div>
        <button 
          className="btn-primary" 
          onClick={handleReverseString}
          disabled={processing}
        >
          {processing ? 'Processing...' : 'Reverse String'}
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
