import React from 'react';
import { clsx } from 'clsx';

export interface PxButtonProps {
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'error';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  className?: string;
}

export function PxButton({
  variant = 'primary',
  size = 'md',
  children,
  onClick,
  disabled = false,
  className
}: PxButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={clsx(
        'px-4 py-2 font-pixel text-xs border-2 transition-all duration-200',
        'focus:outline-none focus:ring-2 focus:ring-offset-2',
        'active:transform active:scale-95',
        {
          // Variants
          'bg-sunBurst text-ink border-sunBurst hover:animate-pxGlow focus:ring-sunBurst': variant === 'primary',
          'bg-transparent text-sunBurst border-sunBurst hover:bg-sunBurst hover:text-ink focus:ring-sunBurst': variant === 'secondary',
          'bg-success text-white border-success hover:bg-green-600 focus:ring-success': variant === 'success',
          'bg-warning text-white border-warning hover:bg-yellow-600 focus:ring-warning': variant === 'warning',
          'bg-error text-white border-error hover:bg-red-600 focus:ring-error': variant === 'error',
          
          // Sizes
          'px-2 py-1 text-xs': size === 'sm',
          'px-4 py-2 text-sm': size === 'md',
          'px-6 py-3 text-base': size === 'lg',
          
          // Disabled
          'opacity-50 cursor-not-allowed hover:animate-none': disabled,
        },
        className
      )}
    >
      {children}
    </button>
  );
}