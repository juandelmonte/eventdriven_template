// This file is used by vitest for test configuration
// It adds custom matchers for asserting on DOM nodes
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom/vitest';
import { beforeAll, afterEach, afterAll } from 'vitest';
import { cleanup } from '@testing-library/react';
