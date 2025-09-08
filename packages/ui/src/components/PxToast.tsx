'use client';

import React, { useEffect, useState } from 'react';
import { clsx } from 'clsx';

export interface PxToastProps {
  message: string;
  type?: 'success' | 'error' | 'warning' | 'info';
  duration?: number;
  onClose: () => void;
  className?: string;
}

export function PxToast({
  message,
  type = 'info',
  duration = 5000,
  onClose,
  className
}: PxToastProps) {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        setIsVisible(false);
        setTimeout(onClose, 300); // Wait for fade out animation
      }, duration);

      return () => clearTimeout(timer);
    }
  }, [duration, onClose]);

  const getIcon = () => {
    switch (type) {
      case 'success': return '✓';
      case 'error': return '✕';
      case 'warning': return '⚠';
      case 'info': return 'ℹ';
      default: return 'ℹ';
    }
  };

  const getColors = () => {
    switch (type) {
      case 'success': return 'bg-success border-success text-white';
      case 'error': return 'bg-error border-error text-white';
      case 'warning': return 'bg-warning border-warning text-ink';
      case 'info': return 'bg-info border-info text-white';
      default: return 'bg-info border-info text-white';
    }
  };

  return (
    <div 
      className={clsx(
        'clip-px border-px px-4 py-3 shadow-px font-pixel text-xs',
        'transition-all duration-300 transform',
        getColors(),
        {
          'translate-y-0 opacity-100': isVisible,
          'translate-y-2 opacity-0': !isVisible,
        },
        className
      )}
    >
      <div className="flex items-center space-x-2">
        <span className="text-sm">{getIcon()}</span>
        <span>{message}</span>
        <button 
          onClick={() => {
            setIsVisible(false);
            setTimeout(onClose, 300);
          }}
          className="ml-auto hover:opacity-80 transition-opacity"
        >
          ✕
        </button>
      </div>
    </div>
  );
}

// Toast Container for managing multiple toasts
export interface ToastItem {
  id: string;
  message: string;
  type?: 'success' | 'error' | 'warning' | 'info';
  duration?: number;
}

export interface PxToastContainerProps {
  toasts: ToastItem[];
  onRemoveToast: (id: string) => void;
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
  className?: string;
}

export function PxToastContainer({
  toasts,
  onRemoveToast,
  position = 'top-right',
  className
}: PxToastContainerProps) {
  const getPositionClasses = () => {
    switch (position) {
      case 'top-right': return 'top-4 right-4';
      case 'top-left': return 'top-4 left-4';
      case 'bottom-right': return 'bottom-4 right-4';
      case 'bottom-left': return 'bottom-4 left-4';
      default: return 'top-4 right-4';
    }
  };

  return (
    <div 
      className={clsx(
        'fixed z-50 flex flex-col space-y-2 max-w-sm',
        getPositionClasses(),
        className
      )}
    >
      {toasts.map((toast) => (
        <PxToast
          key={toast.id}
          message={toast.message}
          type={toast.type}
          duration={toast.duration}
          onClose={() => onRemoveToast(toast.id)}
        />
      ))}
    </div>
  );
}