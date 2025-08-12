import React from 'react';
import { clsx } from 'clsx';

export interface PxChipProps {
  children: React.ReactNode;
  variant?: 'default' | 'selected';
  size?: 'sm' | 'md';
  onClick?: () => void;
  className?: string;
}

export function PxChip({
  children,
  variant = 'default',
  size = 'md',
  onClick,
  className,
}: PxChipProps) {
  const isClickable = !!onClick;

  return (
    <span
      className={clsx(
        'inline-block clip-px border-px font-body transition-all duration-200',
        {
          'bg-white border-ink text-ink dark:bg-dark-surface dark:border-dark-border dark:text-white': variant === 'default',
          'bg-primary border-ink text-ink dark:bg-neon-cyan dark:border-white dark:text-dark-bg': variant === 'selected',
          'px-2 py-1 text-xs': size === 'sm',
          'px-px py-2 text-sm': size === 'md',
          'cursor-pointer hover:bg-primary hover:text-ink dark:hover:bg-neon-cyan dark:hover:text-dark-bg': isClickable && variant === 'default',
          'cursor-pointer hover:bg-pixel-mint hover:text-ink dark:hover:bg-pixel-mint': isClickable && variant === 'selected',
        },
        className
      )}
      onClick={onClick}
    >
      {children}
    </span>
  );
}