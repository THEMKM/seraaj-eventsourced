/* eslint-env jest */
import '@testing-library/jest-dom';

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
    prefetch: jest.fn(),
  }),
  useSearchParams: () => ({
    get: jest.fn(),
  }),
  usePathname: () => '/',
}));

// Mock environment variables
process.env.NEXT_PUBLIC_BFF_URL = 'http://localhost:8000/api';

// Mock auth context
jest.mock('./contexts/AuthContext', () => ({
  useAuth: () => ({
    login: jest.fn().mockResolvedValue({}),
    isLoading: false,
  }),
}));