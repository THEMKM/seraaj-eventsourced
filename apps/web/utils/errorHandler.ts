/**
 * Centralized error handling utilities for better user experience
 */

export interface ApiError {
  status?: number;
  message: string;
  code?: string;
  details?: any;
}

export interface UserFriendlyError {
  title: string;
  message: string;
  action?: string;
  retry?: boolean;
  type: 'network' | 'service' | 'validation' | 'auth' | 'unknown';
}

/**
 * Convert API errors to user-friendly messages
 */
export function parseApiError(error: any): UserFriendlyError {
  // Handle network/connection issues first
  if (!navigator.onLine) {
    return {
      title: 'No Internet Connection',
      message: 'Please check your internet connection and try again.',
      action: 'Check your connection',
      retry: true,
      type: 'network'
    };
  }

  if (error?.message?.includes('fetch') || error?.code === 'NETWORK_ERROR') {
    return {
      title: 'Connection Problem',
      message: 'Unable to connect to our servers. Please try again in a moment.',
      action: 'Try again',
      retry: true,
      type: 'network'
    };
  }

  // Handle specific HTTP status codes
  const status = error?.status;
  const errorMessage = error?.message || 'Request failed';

  switch (status) {
    case 400:
      return {
        title: 'Invalid Input',
        message: 'Please check your information and try again.',
        action: 'Check your input',
        retry: false,
        type: 'validation'
      };

    case 401:
      return {
        title: 'Authentication Required',
        message: 'Please log in to continue.',
        action: 'Log in',
        retry: false,
        type: 'auth'
      };

    case 403:
      return {
        title: 'Access Denied',
        message: 'You don\'t have permission to perform this action.',
        action: 'Contact support',
        retry: false,
        type: 'auth'
      };

    case 404:
      return {
        title: 'Not Found',
        message: 'The requested resource was not found.',
        action: 'Go back',
        retry: false,
        type: 'service'
      };

    case 409:
      return {
        title: 'Conflict',
        message: 'This action conflicts with existing data. Please try a different approach.',
        action: 'Try different input',
        retry: false,
        type: 'validation'
      };

    case 422:
      return {
        title: 'Validation Error',
        message: errorMessage.includes('validation') 
          ? errorMessage 
          : 'Please check your input and try again.',
        action: 'Fix validation errors',
        retry: false,
        type: 'validation'
      };

    case 429:
      return {
        title: 'Too Many Requests',
        message: 'You\'re doing that too often. Please wait a moment and try again.',
        action: 'Wait and retry',
        retry: true,
        type: 'service'
      };

    case 503:
      return {
        title: 'Service Unavailable',
        message: 'Our services are temporarily unavailable. We\'re working to fix this.',
        action: 'Try again later',
        retry: true,
        type: 'service'
      };

    case 500:
    case 502:
    case 504:
      return {
        title: 'Server Error',
        message: 'Something went wrong on our end. Please try again in a moment.',
        action: 'Try again',
        retry: true,
        type: 'service'
      };

    default:
      // Check for specific error types in message
      if (errorMessage.includes('timeout') || errorMessage.includes('timed out')) {
        return {
          title: 'Request Timeout',
          message: 'The request took too long to complete. Please try again.',
          action: 'Try again',
          retry: true,
          type: 'network'
        };
      }

      if (errorMessage.includes('service') || errorMessage.includes('degraded')) {
        return {
          title: 'Service Issue',
          message: 'Some of our services are experiencing issues. Please try again.',
          action: 'Try again',
          retry: true,
          type: 'service'
        };
      }

      return {
        title: 'Something Went Wrong',
        message: errorMessage || 'An unexpected error occurred. Please try again.',
        action: 'Try again',
        retry: true,
        type: 'unknown'
      };
  }
}

/**
 * Retry logic with exponential backoff
 */
export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  baseDelay: number = 1000
): Promise<T> {
  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;
      
      // Don't retry on certain error types
      const parsedError = parseApiError(error);
      if (!parsedError.retry || parsedError.type === 'auth' || parsedError.type === 'validation') {
        throw error;
      }

      // Don't wait on the last attempt
      if (attempt < maxRetries) {
        const delay = baseDelay * Math.pow(2, attempt); // Exponential backoff
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }

  throw lastError || new Error('Retry failed with unknown error');
}

/**
 * Circuit breaker pattern implementation
 */
export class CircuitBreaker {
  private failures = 0;
  private lastFailureTime = 0;
  private state: 'closed' | 'open' | 'half-open' = 'closed';

  constructor(
    private readonly threshold = 5,
    private readonly timeout = 60000 // 1 minute
  ) {}

  async call<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === 'open') {
      if (Date.now() - this.lastFailureTime > this.timeout) {
        this.state = 'half-open';
      } else {
        throw new Error('Circuit breaker is open');
      }
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private onSuccess() {
    this.failures = 0;
    this.state = 'closed';
  }

  private onFailure() {
    this.failures++;
    this.lastFailureTime = Date.now();

    if (this.failures >= this.threshold) {
      this.state = 'open';
    }
  }

  getState() {
    return this.state;
  }
}

// Global circuit breakers for different services
export const serviceCircuitBreakers = {
  auth: new CircuitBreaker(3, 30000),
  applications: new CircuitBreaker(3, 30000),
  matching: new CircuitBreaker(3, 30000),
  bff: new CircuitBreaker(5, 60000)
};