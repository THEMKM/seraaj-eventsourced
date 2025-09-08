'use client';

import React, { useState } from 'react';
import { PxButton, PxCard, PxModal } from '@seraaj/ui';
import { 
  PixelAvatar, 
  AvatarConfig, 
  AvatarClass, 
  AvatarPose, 
  AvatarAccessory,
  AVATAR_ACCESSORIES,
  calculateAvatarClass,
  getUnlockedAccessories
} from './AvatarSystem';

interface AvatarSelectorProps {
  currentConfig: AvatarConfig;
  userLevel: number;
  achievements: any[];
  onConfigChange: (config: AvatarConfig) => void;
  onSave: (config: AvatarConfig) => void;
  isOpen: boolean;
  onClose: () => void;
}

export function AvatarSelector({
  currentConfig,
  userLevel,
  achievements,
  onConfigChange,
  onSave,
  isOpen,
  onClose
}: AvatarSelectorProps) {
  const [previewConfig, setPreviewConfig] = useState<AvatarConfig>(currentConfig);
  const unlockedAccessories = getUnlockedAccessories(achievements, userLevel);
  const currentClass = calculateAvatarClass(userLevel, achievements);

  const poses = [
    { value: AvatarPose.DEFAULT, name: 'Default', icon: '🙂' },
    { value: AvatarPose.CELEBRATING, name: 'Celebrating', icon: '🎉' },
    { value: AvatarPose.WORKING, name: 'Working', icon: '💪' },
    { value: AvatarPose.THINKING, name: 'Thinking', icon: '🤔' }
  ];

  const handlePoseChange = (pose: AvatarPose) => {
    const newConfig = { ...previewConfig, pose };
    setPreviewConfig(newConfig);
    onConfigChange(newConfig);
  };

  const handleAccessoryToggle = (accessory: AvatarAccessory) => {
    const currentAccessories = previewConfig.accessories;
    const isSelected = currentAccessories.some(acc => acc.id === accessory.id);
    
    let newAccessories;
    if (isSelected) {
      newAccessories = currentAccessories.filter(acc => acc.id !== accessory.id);
    } else {
      newAccessories = [...currentAccessories, accessory];
    }

    const newConfig = { ...previewConfig, accessories: newAccessories };
    setPreviewConfig(newConfig);
    onConfigChange(newConfig);
  };

  const handleSave = () => {
    onSave(previewConfig);
    onClose();
  };

  const handleReset = () => {
    const resetConfig: AvatarConfig = {
      class: currentClass,
      level: userLevel,
      pose: AvatarPose.DEFAULT,
      accessories: []
    };
    setPreviewConfig(resetConfig);
    onConfigChange(resetConfig);
  };

  return (
    <PxModal
      isOpen={isOpen}
      onClose={onClose}
      title="🎭 CUSTOMIZE AVATAR"
      size="lg"
    >
      <div className="space-y-6">
        {/* Avatar Preview */}
        <div className="text-center">
          <div className="inline-block p-6 bg-gradient-to-br from-dark-surface/20 to-primary/10 rounded-lg">
            <PixelAvatar
              config={previewConfig}
              size="lg"
              showLevel={true}
              animated={true}
            />
          </div>
          <div className="mt-3">
            <h3 className="font-pixel text-electric-teal">
              {currentClass.toUpperCase()} - LEVEL {userLevel}
            </h3>
          </div>
        </div>

        {/* Pose Selection */}
        <PxCard variant="default">
          <h4 className="font-pixel text-primary mb-4">⚡ POSE SELECTION</h4>
          <div className="grid grid-cols-2 gap-3">
            {poses.map((pose) => (
              <button
                key={pose.value}
                onClick={() => handlePoseChange(pose.value)}
                className={`
                  p-3 rounded-lg border-2 transition-all duration-200
                  ${previewConfig.pose === pose.value 
                    ? 'border-electric-teal bg-electric-teal/20' 
                    : 'border-gray-600 hover:border-electric-teal/50'
                  }
                `}
              >
                <div className="text-center">
                  <div className="text-2xl mb-1">{pose.icon}</div>
                  <div className="font-pixel text-sm text-white">{pose.name}</div>
                </div>
              </button>
            ))}
          </div>
        </PxCard>

        {/* Accessories */}
        <PxCard variant="default">
          <h4 className="font-pixel text-primary mb-4">🏆 ACCESSORIES</h4>
          {unlockedAccessories.length === 0 ? (
            <div className="text-center py-8">
              <div className="text-4xl mb-2">🔒</div>
              <p className="text-white text-sm">
                Unlock accessories by completing achievements and leveling up!
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-3 gap-3">
              {AVATAR_ACCESSORIES.map((accessory) => {
                const isUnlocked = unlockedAccessories.some(acc => acc.id === accessory.id);
                const isSelected = previewConfig.accessories.some(acc => acc.id === accessory.id);
                
                return (
                  <button
                    key={accessory.id}
                    onClick={() => isUnlocked && handleAccessoryToggle(accessory)}
                    disabled={!isUnlocked}
                    className={`
                      p-3 rounded-lg border-2 transition-all duration-200 relative
                      ${!isUnlocked 
                        ? 'border-gray-700 opacity-50 cursor-not-allowed' 
                        : isSelected
                          ? 'border-pixel-coral bg-pixel-coral/20' 
                          : 'border-gray-600 hover:border-pixel-coral/50'
                      }
                    `}
                    title={isUnlocked ? accessory.name : `Locked: ${accessory.unlockRequirement}`}
                  >
                    <div className="text-center">
                      <div className="text-lg mb-1">{accessory.icon}</div>
                      <div className="font-pixel text-xs text-white">{accessory.name}</div>
                      {!isUnlocked && (
                        <div className="absolute inset-0 flex items-center justify-center">
                          <div className="bg-dark-surface/80 rounded-full p-1">
                            <span className="text-xs">🔒</span>
                          </div>
                        </div>
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          )}
          
          {unlockedAccessories.length > 0 && (
            <div className="mt-4 p-3 bg-dark-surface/20 rounded-lg">
              <p className="text-electric-teal font-pixel text-sm mb-2">
                ✨ UNLOCKED: {unlockedAccessories.length} / {AVATAR_ACCESSORIES.length}
              </p>
              <p className="text-white text-xs">
                Keep volunteering to unlock more customization options!
              </p>
            </div>
          )}
        </PxCard>

        {/* Action Buttons */}
        <div className="flex space-x-3 justify-end">
          <PxButton
            variant="secondary"
            onClick={handleReset}
          >
            🔄 RESET
          </PxButton>
          <PxButton
            variant="secondary"
            onClick={onClose}
          >
            CANCEL
          </PxButton>
          <PxButton
            variant="primary"
            onClick={handleSave}
          >
            💾 SAVE AVATAR
          </PxButton>
        </div>
      </div>
    </PxModal>
  );
}

// Simple avatar display component for throughout the interface
interface AvatarDisplayProps {
  config: AvatarConfig;
  size?: 'sm' | 'md' | 'lg';
  showLevel?: boolean;
  clickable?: boolean;
  onClick?: () => void;
  className?: string;
}

export function AvatarDisplay({
  config,
  size = 'md',
  showLevel = false,
  clickable = false,
  onClick,
  className = ''
}: AvatarDisplayProps) {
  return (
    <div 
      className={`
        ${clickable ? 'cursor-pointer hover:scale-110 transition-transform' : ''}
        ${className}
      `}
      onClick={clickable ? onClick : undefined}
      title={clickable ? 'Click to customize avatar' : undefined}
    >
      <PixelAvatar
        config={config}
        size={size}
        showLevel={showLevel}
        animated={clickable}
      />
    </div>
  );
}