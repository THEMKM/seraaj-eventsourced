"use client";

import React from 'react';
import { PxButton, PxChip } from '@seraaj/ui';
import { OnboardingData, UserType } from '../OnboardingFlow';

export const UserTypeStep: React.FC<{
  data: OnboardingData;
  updateData: (u: Partial<OnboardingData>) => void;
  onNext?: () => void;
}> = ({ data, updateData }) => {
  const select = (type: UserType) => updateData({ userType: type });
  return (
    <div className="space-y-6 text-center">
      <p className="text-white text-sm">Are you here to volunteer or represent an organization?</p>
      <div className="flex items-center justify-center gap-4">
        <PxChip variant={data.userType === 'volunteer' ? 'selected' : 'default'} onClick={() => select('volunteer')}>Volunteer</PxChip>
        <PxChip variant={data.userType === 'organization' ? 'selected' : 'default'} onClick={() => select('organization')}>Organization</PxChip>
      </div>
      {data.userType && (
        <div className="text-white/70 text-xs">Selected: {data.userType}</div>
      )}
      <div className="flex items-center justify-center">
        <PxButton variant="secondary" onClick={() => select('volunteer')}>I want to Volunteer</PxButton>
      </div>
    </div>
  );
};

