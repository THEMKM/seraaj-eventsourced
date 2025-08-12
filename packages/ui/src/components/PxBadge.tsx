import React from 'react';
import { clsx } from 'clsx';

interface PxBadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info' | 'premium';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  animated?: boolean;
}

export const PxBadge: React.FC<PxBadgeProps> = ({
  children,
  variant = 'default',
  size = 'md',
  className,
  animated = false,
}) => {
  return (
    <span
      className={clsx(
        'inline-flex items-center font-pixel border-px clip-px',
        {
          // Variants
          'bg-gray-100 dark:bg-dark-surface border-gray-400 dark:border-dark-border text-gray-700 dark:text-gray-300': variant === 'default',
          'bg-electric-teal border-ink dark:border-white text-ink dark:text-dark-bg': variant === 'success',
          'bg-primary border-ink dark:border-white text-ink dark:text-dark-bg': variant === 'warning',
          'bg-pixel-coral border-ink dark:border-white text-white': variant === 'error',
          'bg-pixel-mint border-ink dark:border-white text-ink dark:text-dark-bg': variant === 'info',
          'bg-gradient-to-r from-pixel-lavender to-pixel-coral border-ink dark:border-white text-white': variant === 'premium',
          
          // Sizes
          'px-1 py-0.5 text-xs': size === 'sm',
          'px-2 py-1 text-xs': size === 'md',
          'px-px py-2 text-sm': size === 'lg',
          
          // Animation
          'animate-px-glow': animated,
        },
        className
      )}
    >
      {children}
    </span>
  );
};

// Achievement Badge Component
interface AchievementBadgeProps {
  title: string;
  icon: string;
  description?: string;
  earned?: boolean;
  className?: string;
}

export const PxAchievementBadge: React.FC<AchievementBadgeProps> = ({
  title,
  icon,
  description,
  earned = false,
  className,
}) => {
  return (
    <div
      className={clsx(
        'clip-px border-px p-4 text-center transition-all duration-300',
        {
          'bg-gradient-to-br from-primary to-electric-teal border-ink dark:border-white shadow-px-glow': earned,
          'bg-gray-100 dark:bg-dark-surface border-gray-400 dark:border-dark-border opacity-50': !earned,
        },
        className
      )}
    >
      <div className="text-2xl mb-2">{icon}</div>
      <h3 className={clsx('font-pixel text-xs mb-1', {
        'text-ink dark:text-dark-bg': earned,
        'text-gray-500 dark:text-gray-400': !earned,
      })}>
        {title}
      </h3>
      {description && (
        <p className={clsx('text-xs font-body', {
          'text-ink dark:text-dark-bg': earned,
          'text-gray-400': !earned,
        })}>
          {description}
        </p>
      )}
      {earned && (
        <PxBadge variant="success" size="sm" className="mt-2">
          EARNED
        </PxBadge>
      )}
    </div>
  );
};

// Skill Level Badge
interface SkillBadgeProps {
  skill: string;
  level: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  className?: string;
}

export const PxSkillBadge: React.FC<SkillBadgeProps> = ({
  skill,
  level,
  className,
}) => {
  const getLevelColor = () => {
    switch (level) {
      case 'beginner':
        return 'bg-gray-200 dark:bg-dark-surface border-gray-400 dark:border-dark-border text-gray-700 dark:text-gray-300';
      case 'intermediate':
        return 'bg-pixel-mint border-ink dark:border-white text-ink dark:text-dark-bg';
      case 'advanced':
        return 'bg-primary border-ink dark:border-white text-ink dark:text-dark-bg';
      case 'expert':
        return 'bg-gradient-to-r from-pixel-coral to-pixel-lavender border-ink dark:border-white text-white';
    }
  };

  const getLevelDots = () => {
    const totalDots = 4;
    const filledDots = level === 'beginner' ? 1 : level === 'intermediate' ? 2 : level === 'advanced' ? 3 : 4;
    
    return Array.from({ length: totalDots }).map((_, index) => (
      <div
        key={index}
        className={clsx('w-1 h-1 clip-px', {
          'bg-current': index < filledDots,
          'bg-gray-400 dark:bg-gray-600': index >= filledDots,
        })}
      />
    ));
  };

  return (
    <div className={clsx('clip-px border-px p-2', getLevelColor(), className)}>
      <div className="flex items-center justify-between gap-2">
        <span className="font-pixel text-xs">{skill}</span>
        <div className="flex gap-0.5">
          {getLevelDots()}
        </div>
      </div>
    </div>
  );
};