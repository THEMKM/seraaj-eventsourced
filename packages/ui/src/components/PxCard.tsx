import React from 'react';
import { clsx } from 'clsx';

export interface PxCardProps {
  children: React.ReactNode;
  variant?: 'default' | 'glow' | 'minimal';
  className?: string;
}

export function PxCard({ children, variant = 'default', className }: PxCardProps) {
  return (
    <div
      className={clsx(
        'border-2 rounded-lg p-4 transition-all duration-200',
        {
          'bg-deepIndigo border-electricTeal text-white': variant === 'default',
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