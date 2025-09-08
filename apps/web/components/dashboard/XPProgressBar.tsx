'use client';

import React from 'react';

interface XPProgressBarProps {
  currentXP: number;
  level: number;
  nextLevelXP: number;
}

export function XPProgressBar({ currentXP, level, nextLevelXP }: XPProgressBarProps) {
  // Linear level scheme: each level requires +100 XP (points)
  const prevLevelThreshold = Math.max(0, nextLevelXP - 100);
  const xpInCurrentLevel = Math.max(0, currentXP - prevLevelThreshold);
  const levelSpan = nextLevelXP - prevLevelThreshold || 100;
  const progressPercent = Math.min(100, (xpInCurrentLevel / levelSpan) * 100);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-electric-teal font-pixel text-sm">⭐ LEVEL {level}</span>
        <span className="text-pixel-coral font-pixel text-sm">
          {xpInCurrentLevel}/{levelSpan} XP
        </span>
      </div>
      <div className="relative h-4 clip-px border-px border-electric-teal bg-dark-surface/20 overflow-hidden">
        <div
          className="absolute inset-0 bg-gradient-to-r from-electric-teal to-pixel-coral transition-all duration-1000 ease-out"
          style={{
            width: `${progressPercent}%`,
            boxShadow: progressPercent > 0 ? '0 0 10px rgba(0, 255, 255, 0.3)' : 'none'
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent opacity-30 animate-pulse" />
      </div>
      <div className="text-center">
        <span className="text-white font-pixel text-xs">
          {Math.max(0, levelSpan - xpInCurrentLevel)} XP to Level {level + 1}
        </span>
      </div>
    </div>
  );
}
