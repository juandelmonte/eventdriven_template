import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import App from './App';

// Mock the authService and react-router-dom
vi.mock('./services/api', () => ({
  authService: {
    isAuthenticated: () => false
  }
}));

vi.mock('react-router-dom', () => ({
  BrowserRouter: ({ children }) => <div>{children}</div>,
  Routes: ({ children }) => <div>{children}</div>,
  Route: ({ element }) => element,
  Navigate: () => <div>Navigate</div>
}));

describe('App', () => {
  it('renders without crashing', () => {
    render(<App />);
    expect(document.querySelector('.App')).toBeTruthy();
  });
});
