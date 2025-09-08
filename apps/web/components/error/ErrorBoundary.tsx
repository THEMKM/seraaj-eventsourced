'use client';

import React, { Component, ReactNode } from 'react';
import { PxButton, PxCard } from '@seraaj/ui';

interface ErrorInfo {
  componentStack: string;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  retryCount: number;
}

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  maxRetries?: number;
  resetOnPropsChange?: boolean;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  private resetTimeoutId: number | null = null;

  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: 0
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    this.setState({
      error,
      errorInfo
    });

    // Call optional error handler
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  componentDidUpdate(prevProps: ErrorBoundaryProps) {
    const { resetOnPropsChange } = this.props;
    const { hasError } = this.state;
    
    // Reset error state when props change (e.g., route changes)
    if (prevProps.children !== this.props.children && hasError && resetOnPropsChange) {
      this.handleReset();
    }
  }

  componentWillUnmount() {
    if (this.resetTimeoutId) {
      clearTimeout(this.resetTimeoutId);
    }
  }

  handleRetry = () => {
    const { maxRetries = 3 } = this.props;
    const { retryCount } = this.state;

    if (retryCount < maxRetries) {
      this.setState(prevState => ({
        hasError: false,
        error: null,
        errorInfo: null,
        retryCount: prevState.retryCount + 1
      }));
    }
  };

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: 0
    });
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    const { hasError, error, retryCount } = this.state;
    const { children, fallback, maxRetries = 3 } = this.props;

    if (hasError && error) {
      // Use custom fallback if provided
      if (fallback) {
        return fallback;
      }

      // Determine error type for user-friendly messaging
      const isNetworkError = error.message.includes('fetch') || error.message.includes('network');
      const isServiceError = error.message.includes('service') || error.message.includes('503');
      const isValidationError = error.message.includes('validation') || error.message.includes('400');

      let userMessage = 'Something went wrong';
      let suggestion = 'Please try again';
      let icon = '⚠️';

      if (isNetworkError) {
        userMessage = 'Connection Problem';
        suggestion = 'Check your internet connection and try again';
        icon = '📡';
      } else if (isServiceError) {
        userMessage = 'Service Temporarily Unavailable';
        suggestion = 'Our services are experiencing issues. Please try again in a moment.';
        icon = '🔧';
      } else if (isValidationError) {
        userMessage = 'Invalid Data';
        suggestion = 'Please check your input and try again';
        icon = '📝';
      }

      return (
        <div className="min-h-screen bg-gradient-to-br from-deepIndigo to-ink flex items-center justify-center p-6">
          <PxCard variant="default" className="max-w-lg w-full text-center">
            <div className="space-y-6">
              <div className="text-6xl">{icon}</div>
              
              <div>
                <h1 className="text-xl font-pixel text-primary mb-2">
                  SYSTEM ERROR
                </h1>
                <h2 className="text-lg font-pixel text-pixel-coral mb-4">
                  {userMessage}
                </h2>
                <p className="text-white text-sm mb-4">
                  {suggestion}
                </p>
              </div>

              {/* Error details (dev mode) */}
              {process.env.NODE_ENV === 'development' && (
                <details className="text-left">
                  <summary className="text-electric-teal font-pixel cursor-pointer">
                    Technical Details
                  </summary>
                  <div className="mt-2 p-3 bg-dark-surface/20 rounded text-xs text-gray-300">
                    <p><strong>Error:</strong> {error.message}</p>
                    <p><strong>Retries:</strong> {retryCount}/{maxRetries}</p>
                  </div>
                </details>
              )}

              <div className="flex gap-3 justify-center">
                {retryCount < maxRetries && (
                  <PxButton 
                    variant="primary" 
                    onClick={this.handleRetry}
                  >
                    🔄 TRY AGAIN ({maxRetries - retryCount} left)
                  </PxButton>
                )}
                
                <PxButton 
                  variant="secondary" 
                  onClick={this.handleReload}
                >
                  🔃 RELOAD PAGE
                </PxButton>
              </div>

              {retryCount >= maxRetries && (
                <div className="text-pixel-coral text-sm">
                  <p>Maximum retries reached.</p>
                  <p>If the problem persists, please reload the page or contact support.</p>
                </div>
              )}
            </div>
          </PxCard>
        </div>
      );
    }

    return children;
  }
}

// Hook version for functional components
export function useErrorHandler() {
  const [error, setError] = React.useState<Error | null>(null);

  const resetError = () => setError(null);

  const handleError = React.useCallback((error: Error) => {
    setError(error);
  }, []);

  // Throw error to trigger error boundary
  if (error) {
    throw error;
  }

  return { handleError, resetError };
}