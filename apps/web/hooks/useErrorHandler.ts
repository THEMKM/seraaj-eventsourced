import { useState, useCallback } from 'react';
import { useToast } from '@/contexts/ToastContext';
import { parseApiError, retryWithBackoff, UserFriendlyError } from '@/utils/errorHandler';

interface UseErrorHandlerOptions {
  showToast?: boolean;
  maxRetries?: number;
  retryDelay?: number;
}

interface UseErrorHandlerReturn {
  error: UserFriendlyError | null;
  isRetrying: boolean;
  retryCount: number;
  handleError: (error: any) => void;
  clearError: () => void;
  retryLastAction: () => Promise<void>;
  executeWithRetry: <T>(fn: () => Promise<T>) => Promise<T>;
}

export function useErrorHandler(options: UseErrorHandlerOptions = {}): UseErrorHandlerReturn {
  const {
    showToast = true,
    maxRetries = 3,
    retryDelay = 1000
  } = options;

  const { showError, showSuccess } = useToast();
  const [error, setError] = useState<UserFriendlyError | null>(null);
  const [isRetrying, setIsRetrying] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [lastAction, setLastAction] = useState<(() => Promise<any>) | null>(null);

  const handleError = useCallback((rawError: any) => {
    const parsedError = parseApiError(rawError);
    setError(parsedError);
    setIsRetrying(false);

    if (showToast) {
      showError(parsedError.message);
    }

    console.error('Error handled:', rawError, parsedError);
  }, [showToast, showError]);

  const clearError = useCallback(() => {
    setError(null);
    setRetryCount(0);
    setLastAction(null);
  }, []);

  const retryLastAction = useCallback(async () => {
    if (!lastAction || !error?.retry) {
      return;
    }

    if (retryCount >= maxRetries) {
      if (showToast) {
        showError(`Maximum retries (${maxRetries}) reached. Please try again later.`);
      }
      return;
    }

    setIsRetrying(true);
    setRetryCount(prev => prev + 1);

    try {
      await new Promise(resolve => setTimeout(resolve, retryDelay * retryCount));
      const result = await lastAction();
      clearError();
      
      if (showToast) {
        showSuccess('Action completed successfully!');
      }
      
      return result;
    } catch (retryError) {
      handleError(retryError);
    } finally {
      setIsRetrying(false);
    }
  }, [lastAction, error, retryCount, maxRetries, retryDelay, showToast, showError, showSuccess, handleError, clearError]);

  const executeWithRetry = useCallback(async <T>(fn: () => Promise<T>): Promise<T> => {
    setLastAction(() => fn);
    clearError();

    try {
      return await retryWithBackoff(fn, maxRetries, retryDelay);
    } catch (retryError) {
      handleError(retryError);
      throw retryError;
    }
  }, [handleError, clearError, maxRetries, retryDelay]);

  return {
    error,
    isRetrying,
    retryCount,
    handleError,
    clearError,
    retryLastAction,
    executeWithRetry
  };
}