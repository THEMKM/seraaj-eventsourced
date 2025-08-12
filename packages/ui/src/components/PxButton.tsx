import React from 'react';
import { clsx } from 'clsx';

export interface PxButtonProps extends Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, 'size'> {
  variant?: 'primary' | 'secondary' | 'danger' | 'success' | 'warning' | 'error';
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
  className,
  ...props
}: PxButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      {...props}
      className={clsx(
        'clip-px shadow-px border-px font-pixel transition-all duration-200',
        'hover:translate-x-1 hover:translate-y-1 hover:shadow-none',
        'active:translate-x-1 active:translate-y-1 active:shadow-none',
        'focus:outline-none focus:ring-2 focus:ring-pixel-coral focus:ring-dotted',
        {
          // Variants
          'bg-primary border-ink text-ink dark:bg-neon-cyan dark:border-white dark:text-dark-bg': variant === 'primary',
          'bg-white border-ink text-ink dark:bg-dark-surface dark:border-dark-border dark:text-white': variant === 'secondary', 
          'bg-pixel-coral border-ink text-white dark:bg-neon-pink dark:border-white': variant === 'danger',
          'bg-success border-ink text-white dark:bg-neon-green dark:border-white': variant === 'success',
          'bg-warning border-ink text-white': variant === 'warning',
          'bg-error border-ink text-white': variant === 'error',
          
          // Sizes
          'px-px py-1 text-xs': size === 'sm',
          'px-px-2 py-2 text-sm': size === 'md', 
          'px-px-3 py-3 text-base': size === 'lg',
          
          // Disabled
          'opacity-50 cursor-not-allowed hover:translate-x-0 hover:translate-y-0 hover:shadow-px': disabled,
        },
        className
      )}
    >
      {children}
    </button>
  );
}