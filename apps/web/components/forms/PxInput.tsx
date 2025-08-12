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
  ...props
}, ref) {
  const hasError = error || variant === 'error';
  
  return (
    <div className="space-y-1">
      {label && (
        <label className="block text-xs font-pixel text-sunBurst">
          {label}
        </label>
      )}
      <input
        ref={ref}
        className={clsx(
          'w-full border-2 bg-deepIndigo text-white font-pixel text-xs',
          'focus:outline-none focus:ring-2 focus:ring-offset-2',
          'transition-all duration-200',
          {
            // Variants
            'border-electricTeal focus:ring-electricTeal': variant === 'default' && !hasError,
            'border-error focus:ring-error': hasError,
            
            // Sizes
            'px-2 py-1 text-xs': size === 'sm',
            'px-3 py-2 text-sm': size === 'md',
            'px-4 py-3 text-base': size === 'lg',
          },
          className
        )}
        {...props}
      />
      {error && (
        <p className="text-xs text-error font-pixel">
          {error}
        </p>
      )}
    </div>
  );
});