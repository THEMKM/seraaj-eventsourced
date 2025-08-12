import React, { forwardRef } from 'react';
import { clsx } from 'clsx';

export interface PxInputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  label?: string;
  error?: string;
  variant?: 'default' | 'error';
  size?: 'sm' | 'md' | 'lg';
}

export const PxInput = forwardRef<HTMLInputElement, PxInputProps>(function PxInput({
  label,
  error,
  variant = 'default',
  size = 'md',
  className,
  id,
  ...props
}, ref) {
  const hasError = error || variant === 'error';
  const inputId = id || `px-input-${Math.random().toString(36).substr(2, 9)}`;
  
  return (
    <div className="space-y-1">
      {label && (
        <label htmlFor={inputId} className="block text-sm font-pixel text-ink dark:text-white">
          {label}
        </label>
      )}
      <input
        ref={ref}
        id={inputId}
        className={clsx(
          'w-full clip-px border-px bg-white border-ink font-body',
          'focus:outline-none focus:ring-2 focus:ring-pixel-coral focus:ring-dotted',
          'placeholder:text-gray-500 transition-all duration-200',
          'dark:bg-dark-surface dark:border-dark-border dark:text-white dark:placeholder:text-gray-400',
          {
            // Variants
            'text-ink dark:text-white': variant === 'default' && !hasError,
            'border-pixel-coral dark:border-pixel-coral': hasError,
            
            // Sizes
            'px-2 py-1 text-sm': size === 'sm',
            'px-px-2 py-2 text-sm': size === 'md',
            'px-px-3 py-3 text-base': size === 'lg',
          },
          className
        )}
        {...props}
      />
      {error && (
        <p className="text-sm font-body text-pixel-coral">
          {error}
        </p>
      )}
    </div>
  );
});