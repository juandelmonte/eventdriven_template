import React, { useState } from 'react';
import { taskService } from '../services/api';

const ReverseStringTask = () => {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [taskId, setTaskId] = useState(null);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      const response = await taskService.reverseString(text);
      setTaskId(response.task_id);
    } catch (err) {
      setError('Error submitting task: ' + (err.response?.data?.error || err.message));
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="card mb-4">
      <div className="card-header">
        <h3>Reverse String Task</h3>
      </div>
      <div className="card-body">
        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label htmlFor="text" className="form-label">Text to reverse:</label>
            <input
              type="text"
              className="form-control"
              id="text"
              value={text}
              onChange={(e) => setText(e.target.value)}
              required
            />
          </div>
          <button 
            type="submit" 
            className="btn btn-primary"
            disabled={loading || !text}
          >
            {loading ? 'Submitting...' : 'Reverse String'}
          </button>
        </form>
        
        {error && (
          <div className="alert alert-danger mt-3">
            {error}
          </div>
        )}
        
        {taskId && (
          <div className="alert alert-success mt-3">
            Task submitted! ID: {taskId}
          </div>
        )}
      </div>
    </div>
  );
};

export default ReverseStringTask;
