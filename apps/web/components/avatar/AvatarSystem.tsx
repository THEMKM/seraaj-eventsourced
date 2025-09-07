'use client';

import React from 'react';

// Avatar system types
export interface AvatarConfig {
  class: AvatarClass;
  level: number;
  pose: AvatarPose;
  accessories: AvatarAccessory[];
  background?: AvatarBackground;
}

export enum AvatarClass {
  HERO = 'hero',
  MENTOR = 'mentor', 
  ORGANIZER = 'organizer',
  LEGEND = 'legend'
}

export enum AvatarPose {
  DEFAULT = 'default',
  CELEBRATING = 'celebrating',
  WORKING = 'working',
  THINKING = 'thinking'
}

export interface AvatarAccessory {
  id: string;
  name: string;
  type: 'hat' | 'badge' | 'tool' | 'effect';
  unlockRequirement: string;
  icon: string;
}

export enum AvatarBackground {
  DEFAULT = 'default',
  OFFICE = 'office',
  COMMUNITY = 'community', 
  NATURE = 'nature'
}

// Pre-defined avatar accessories based on achievements
export const AVATAR_ACCESSORIES: AvatarAccessory[] = [
  {
    id: 'rookie_badge',
    name: 'Rookie Badge',
    type: 'badge',
    unlockRequirement: 'Complete first application',
    icon: '🏅'
  },
  {
    id: 'volunteer_hat',
    name: 'Volunteer Cap',
    type: 'hat',
    unlockRequirement: 'Reach level 3',
    icon: '🧢'
  },
  {
    id: 'helping_hands',
    name: 'Helping Hands',
    type: 'effect',
    unlockRequirement: 'Get 5 applications approved',
    icon: '🤝'
  },
  {
    id: 'community_star',
    name: 'Community Star',
    type: 'badge',
    unlockRequirement: 'Help 3 different organizations',
    icon: '⭐'
  },
  {
    id: 'mentor_crown',
    name: 'Mentor Crown',
    type: 'hat',
    unlockRequirement: 'Reach level 10',
    icon: '👑'
  },
  {
    id: 'organizer_clipboard',
    name: 'Organizer Clipboard',
    type: 'tool',
    unlockRequirement: 'Complete 25 applications',
    icon: '📋'
  },
  {
    id: 'legend_aura',
    name: 'Legend Aura',
    type: 'effect',
    unlockRequirement: 'Reach level 20',
    icon: '✨'
  }
];

interface PixelAvatarProps {
  config: AvatarConfig;
  size?: 'sm' | 'md' | 'lg';
  showLevel?: boolean;
  animated?: boolean;
  className?: string;
}

export function PixelAvatar({ 
  config, 
  size = 'md', 
  showLevel = false, 
  animated = false,
  className = '' 
}: PixelAvatarProps) {
  const sizeClasses = {
    sm: 'w-8 h-8 text-xs',
    md: 'w-12 h-12 text-sm', 
    lg: 'w-24 h-24 text-xl'
  };

  const getClassIcon = (avatarClass: AvatarClass): string => {
    switch (avatarClass) {
      case AvatarClass.HERO: return '🦸';
      case AvatarClass.MENTOR: return '🧙';
      case AvatarClass.ORGANIZER: return '👨‍💼';
      case AvatarClass.LEGEND: return '🏆';
      default: return '🙂';
    }
  };

  const getPoseEffect = (pose: AvatarPose): string => {
    switch (pose) {
      case AvatarPose.CELEBRATING: return 'animate-bounce';
      case AvatarPose.WORKING: return 'animate-pulse';
      case AvatarPose.THINKING: return '';
      default: return '';
    }
  };

  const getClassColor = (avatarClass: AvatarClass): string => {
    switch (avatarClass) {
      case AvatarClass.HERO: return 'from-primary to-electric-teal';
      case AvatarClass.MENTOR: return 'from-sunBurst to-pixel-coral';
      case AvatarClass.ORGANIZER: return 'from-electric-teal to-neon-cyan';
      case AvatarClass.LEGEND: return 'from-pixel-coral to-sunBurst';
      default: return 'from-gray-600 to-gray-800';
    }
  };

  const baseIcon = getClassIcon(config.class);
  const poseEffect = animated ? getPoseEffect(config.pose) : '';
  const gradientColor = getClassColor(config.class);

  return (
    <div className={`relative ${className}`}>
      {/* Main Avatar */}
      <div className={`
        ${sizeClasses[size]}
        ${poseEffect}
        bg-gradient-to-br ${gradientColor}
        border-2 border-electric-teal rounded-lg
        flex items-center justify-center
        clip-px transition-transform hover:scale-105
        ${config.pose === AvatarPose.CELEBRATING ? 'shadow-lg shadow-electric-teal/50' : ''}
      `}>
        <span className="filter drop-shadow-sm">
          {baseIcon}
        </span>
      </div>

      {/* Level Indicator */}
      {showLevel && (
        <div className="absolute -top-1 -right-1 bg-pixel-coral text-white font-pixel text-xs w-5 h-5 rounded-full flex items-center justify-center border border-white">
          {config.level}
        </div>
      )}

      {/* Accessories */}
      {config.accessories.map((accessory, index) => (
        <div
          key={accessory.id}
          className={`absolute ${getAccessoryPosition(accessory.type, index)} text-xs`}
          title={accessory.name}
        >
          {accessory.icon}
        </div>
      ))}

      {/* Special Effects for Legend class */}
      {config.class === AvatarClass.LEGEND && animated && (
        <div className="absolute inset-0 rounded-lg bg-gradient-to-r from-transparent via-white/20 to-transparent animate-pulse pointer-events-none" />
      )}
    </div>
  );
}

function getAccessoryPosition(type: string, index: number): string {
  switch (type) {
    case 'hat': return '-top-1 left-1/2 transform -translate-x-1/2';
    case 'badge': return '-bottom-1 -right-1';
    case 'tool': return '-bottom-1 -left-1';
    case 'effect': return 'top-1/2 -right-2 transform -translate-y-1/2';
    default: return `${index % 2 === 0 ? '-top-1' : '-bottom-1'} ${index % 4 < 2 ? '-left-1' : '-right-1'}`;
  }
}

// Helper function to determine avatar class based on level and achievements
export function calculateAvatarClass(level: number, achievements: any[]): AvatarClass {
  if (level >= 20) return AvatarClass.LEGEND;
  if (level >= 10) return AvatarClass.MENTOR;
  if (level >= 5) return AvatarClass.ORGANIZER;
  return AvatarClass.HERO;
}

// Helper function to unlock accessories based on achievements
export function getUnlockedAccessories(achievements: any[], level: number): AvatarAccessory[] {
  const unlocked: AvatarAccessory[] = [];
  
  achievements.forEach(achievement => {
    if (achievement.earnedAt) {
      // Map specific achievements to accessories
      const accessoryMap: Record<string, string> = {
        'first_application': 'rookie_badge',
        'quest_seeker': 'rookie_badge',
        'first_approval': 'helping_hands',
        'first_success': 'helping_hands',
        'trusted_volunteer': 'community_star',
        'applicant_gold': 'organizer_clipboard'
      };
      
      const accessoryId = accessoryMap[achievement.id];
      if (accessoryId) {
        const accessory = AVATAR_ACCESSORIES.find(acc => acc.id === accessoryId);
        if (accessory && !unlocked.find(u => u.id === accessory.id)) {
          unlocked.push(accessory);
        }
      }
    }
  });

  // Level-based accessories (ensure they're not already unlocked)
  if (level >= 3) {
    const hat = AVATAR_ACCESSORIES.find(acc => acc.id === 'volunteer_hat')!;
    if (!unlocked.find(u => u.id === hat.id)) {
      unlocked.push(hat);
    }
  }
  if (level >= 10) {
    const crown = AVATAR_ACCESSORIES.find(acc => acc.id === 'mentor_crown')!;
    if (!unlocked.find(u => u.id === crown.id)) {
      unlocked.push(crown);
    }
  }
  if (level >= 20) {
    const aura = AVATAR_ACCESSORIES.find(acc => acc.id === 'legend_aura')!;
    if (!unlocked.find(u => u.id === aura.id)) {
      unlocked.push(aura);
    }
  }

  return unlocked.filter(Boolean);
}