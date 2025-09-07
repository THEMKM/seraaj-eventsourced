'use client';

import React from 'react';

export interface Achievement {
  id: string;
  name: string;
  description: string;
  icon: string;
  earnedAt: Date | null;
  progress?: number; // 0-100 for progress-based achievements
  requirement?: number; // Total needed for achievement
}

interface AchievementBadgeProps {
  achievement: Achievement;
  size?: 'sm' | 'md' | 'lg';
}

export function AchievementBadge({ achievement, size = 'md' }: AchievementBadgeProps) {
  const isEarned = achievement.earnedAt !== null;
  const hasProgress = achievement.progress !== undefined;

  const sizeClasses = {
    sm: 'w-12 h-12 text-lg',
    md: 'w-16 h-16 text-xl',
    lg: 'w-20 h-20 text-2xl'
  };

  const badgeClass = isEarned 
    ? 'bg-gradient-to-br from-sunBurst to-pixel-coral border-sunBurst shadow-lg' 
    : 'bg-dark-surface/40 border-gray-600';

  return (
    <div className="relative group">
      <div className={`
        ${sizeClasses[size]} 
        ${badgeClass}
        border-2 rounded-lg flex items-center justify-center
        transition-all duration-300 hover:scale-105 cursor-pointer
        ${isEarned ? 'animate-pulse' : 'opacity-60'}
      `}>
        <span className={isEarned ? 'text-white' : 'text-gray-400'}>
          {achievement.icon}
        </span>
      </div>

      {hasProgress && !isEarned && (
        <div className="absolute -bottom-1 left-1/2 transform -translate-x-1/2 w-full">
          <div className="h-1 bg-dark-surface/60 rounded-full">
            <div
              className="h-1 bg-electric-teal rounded-full transition-all duration-500"
              style={{ width: `${achievement.progress}%` }}
            />
          </div>
        </div>
      )}

      {isEarned && (
        <div className="absolute -top-1 -right-1 w-4 h-4 bg-neon-cyan rounded-full border border-white animate-ping" />
      )}

      {/* Tooltip */}
      <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-ink text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-10 min-w-max">
        <div className="font-pixel text-electric-teal">{achievement.name}</div>
        <div className="text-gray-300">{achievement.description}</div>
        {hasProgress && !isEarned && (
          <div className="text-pixel-coral">
            {achievement.progress}% ({Math.floor((achievement.progress! / 100) * (achievement.requirement || 100))}/{achievement.requirement || 100})
          </div>
        )}
        {isEarned && achievement.earnedAt && (
          <div className="text-neon-cyan text-xs">
            Earned: {achievement.earnedAt.toLocaleDateString()}
          </div>
        )}
        <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-ink" />
      </div>
    </div>
  );
}