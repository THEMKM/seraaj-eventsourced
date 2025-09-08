import React from 'react';
import { clsx } from 'clsx';

export interface PxCardProps {
  children: React.ReactNode;
  variant?: 'default' | 'highlighted' | 'glow' | 'minimal';
  className?: string;
}

export function PxCard({ children, variant = 'default', className }: PxCardProps) {
  return (
    <div
      className={clsx(
        'clip-px shadow-px border-px p-4 transition-all duration-200',
        {
          'bg-white border-ink text-ink dark:bg-dark-surface dark:border-dark-border dark:text-white': variant === 'default',
          'bg-primary border-ink text-ink dark:bg-neon-cyan dark:border-white dark:text-dark-bg': variant === 'highlighted',
          'bg-deepIndigo border-sunBurst text-white animate-pxGlow': variant === 'glow',
          'bg-white border-gray-200 text-ink shadow-sm': variant === 'minimal',
        },
        className
      )}
    >
      {children}
    </div>
  );
}