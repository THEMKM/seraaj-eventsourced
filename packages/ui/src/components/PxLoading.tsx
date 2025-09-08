import React from 'react';
import { clsx } from 'clsx';

export interface PxLoadingProps {
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'bright';
  className?: string;
  text?: string;
}

export function PxLoading({
  size = 'md',
  variant = 'default',
  className,
  text
}: PxLoadingProps) {
  return (
    <div className={clsx('flex items-center justify-center', className)}>
      <div className="flex flex-col items-center space-y-2">
        <div
          className={clsx(
            'border-2 border-t-transparent rounded-full animate-spin',
            {
              'w-4 h-4': size === 'sm',
              'w-8 h-8': size === 'md',
              'w-12 h-12': size === 'lg',
              
              'border-primary': variant === 'default',
              'border-neon-cyan': variant === 'bright',
            }
          )}
        />
        {text && (
          <p className={clsx(
            'font-pixel text-xs',
            {
              'text-ink dark:text-white': variant === 'default',
              'text-neon-cyan': variant === 'bright',
            }
          )}>
            {text}
          </p>
        )}
      </div>
    </div>
  );
}

// Pixel art style loading component
export interface PxPixelLoadingProps {
  className?: string;
  text?: string;
}

export function PxPixelLoading({ className, text }: PxPixelLoadingProps) {
  return (
    <div className={clsx('flex items-center justify-center', className)}>
      <div className="flex flex-col items-center space-y-4">
        <div className="grid grid-cols-3 gap-1">
          {Array.from({ length: 9 }).map((_, i) => (
            <div
              key={i}
              className="w-2 h-2 bg-primary animate-pulse"
              style={{
                animationDelay: `${i * 100}ms`,
                animationDuration: '1s'
              }}
            />
          ))}
        </div>
        {text && (
          <p className="font-pixel text-xs text-primary animate-pulse">
            {text}
          </p>
        )}
      </div>
    </div>
  );
}