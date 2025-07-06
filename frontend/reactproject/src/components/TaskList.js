import React from 'react';

const TaskList = ({ tasks }) => {
  if (!tasks || tasks.length === 0) {
    return <p>No tasks found</p>;
  }

  return (
    <div className="task-list">
      {tasks.map((task) => (
        <div key={task.task_id} className={`task-item ${task.status}`}>
          <div className="task-header">
            <h3>{task.task_type}</h3>
            <span className={`status-badge ${task.status}`}>{task.status}</span>
          </div>
          <div className="task-details">
            <p><strong>Task ID:</strong> {task.task_id}</p>
            <p><strong>Received:</strong> {new Date().toLocaleString()}</p>
            {task.result && (
              <div className="task-result">
                <h4>Result:</h4>
                {task.task_type === 'generate_random_number' && (
                  <p className="random-number">{task.result.number}</p>
                )}
                {task.task_type !== 'generate_random_number' && (
                  <pre>{JSON.stringify(task.result, null, 2)}</pre>
                )}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

export default TaskList;
