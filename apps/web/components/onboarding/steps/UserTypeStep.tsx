"use client";

import React from 'react';
import { PxButton, PxCard } from '@seraaj/ui';
import { OnboardingData, UserType } from '../OnboardingFlow';

export const UserTypeStep: React.FC<{
  data: OnboardingData;
  updateData: (u: Partial<OnboardingData>) => void;
  onNext?: () => void;
}> = ({ data, updateData, onNext }) => {
  const handleTypeSelect = (type: UserType) => {
    updateData({ userType: type });
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-pixel text-primary dark:text-neon-cyan mb-4">
          Choose Your Path
        </h2>
        <p className="text-white text-lg">
          Are you here to volunteer or do you represent an organization?
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-6 mb-8">
        {/* Volunteer Option - Hero */}
        <PxCard 
          className={`cursor-pointer border-2 transition-all duration-300 hover:scale-105 ${
            data.userType === 'volunteer' 
              ? 'border-primary dark:border-neon-cyan bg-primary/10 dark:bg-neon-cyan/10 shadow-px-glow' 
              : 'border-gray-600 hover:border-primary/50 dark:hover:border-neon-cyan/50'
          }`}
          onClick={() => handleTypeSelect('volunteer')}
        >
          <div className="text-center p-8">
            <div className="text-6xl mb-4">🦸‍♂️</div>
            <h3 className="text-xl font-pixel text-primary dark:text-neon-cyan mb-2">
              I'm a Hero
            </h3>
            <p className="text-white mb-4">
              I want to volunteer and help causes I care about
            </p>
            <ul className="text-sm text-gray-300 text-left space-y-1">
              <li>• Find perfect volunteer matches</li>
              <li>• Track your impact and hours</li>
              <li>• Connect with organizations</li>
              <li>• Build your heroic reputation</li>
            </ul>
            {data.userType === 'volunteer' && (
              <div className="mt-4">
                <span className="inline-block px-4 py-2 bg-primary dark:bg-neon-cyan text-ink dark:text-dark-bg font-pixel text-xs rounded-lg">
                  ✓ Selected
                </span>
              </div>
            )}
          </div>
        </PxCard>

        {/* Organization Option - Quest Giver */}
        <PxCard 
          className={`cursor-pointer border-2 transition-all duration-300 hover:scale-105 ${
            data.userType === 'organization' 
              ? 'border-primary dark:border-neon-cyan bg-primary/10 dark:bg-neon-cyan/10 shadow-px-glow' 
              : 'border-gray-600 hover:border-primary/50 dark:hover:border-neon-cyan/50'
          }`}
          onClick={() => handleTypeSelect('organization')}
        >
          <div className="text-center p-8">
            <div className="text-6xl mb-4">🏰</div>
            <h3 className="text-xl font-pixel text-primary dark:text-neon-cyan mb-2">
              I'm a Quest Giver
            </h3>
            <p className="text-white mb-4">
              I represent an organization seeking volunteers
            </p>
            <ul className="text-sm text-gray-300 text-left space-y-1">
              <li>• Post volunteer opportunities</li>
              <li>• Find qualified heroes</li>
              <li>• Manage applications</li>
              <li>• Track organizational impact</li>
            </ul>
            {data.userType === 'organization' && (
              <div className="mt-4">
                <span className="inline-block px-4 py-2 bg-primary dark:bg-neon-cyan text-ink dark:text-dark-bg font-pixel text-xs rounded-lg">
                  ✓ Selected
                </span>
              </div>
            )}
          </div>
        </PxCard>
      </div>

      <div className="text-center">
        <PxButton
          variant="primary"
          onClick={onNext}
          disabled={!data.userType}
          className="hover:shadow-px-glow"
        >
          {data.userType ? 'Continue Your Journey' : 'Choose Your Path First'}
        </PxButton>
      </div>
    </div>
  );
};

