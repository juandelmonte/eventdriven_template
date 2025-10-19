import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';
import Login from './components/Login';
import Register from './components/Register';
import Dashboard from './components/Dashboard';
import ProtectedRoute from './components/ProtectedRoute';
import { authService } from './services/api';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/login" element={
            authService.isAuthenticated() ? <Navigate to="/dashboard" /> : <Login />
          } />
          <Route path="/register" element={
            authService.isAuthenticated() ? <Navigate to="/dashboard" /> : <Register />
          } />
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } />
          <Route path="/" element={<Navigate to={authService.isAuthenticated() ? "/dashboard" : "/login"} />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;