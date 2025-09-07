"use client";

import React from 'react';
import { PxInput } from '@/components/forms/PxInput';
import { OnboardingData } from '../OnboardingFlow';

export const ProfileStep: React.FC<{
  data: OnboardingData;
  updateData: (u: Partial<OnboardingData>) => void;
  onNext?: () => void;
}> = ({ data, updateData }) => {
  return (
    <div className="space-y-6">
      <div className="text-center">
        <p className="text-white text-sm">
          {data.userType === 'organization' ? 'Tell us about your organization.' : 'Tell us a bit about yourself.'}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {data.userType !== 'organization' && (
          <>
            <PxInput label="Your Name" value={data.name} onChange={(e) => updateData({ name: e.target.value })} required />
            <PxInput label="Email" type="email" value={data.email} onChange={(e) => updateData({ email: e.target.value })} required />
          </>
        )}

        {data.userType === 'organization' && (
          <>
            <PxInput label="Organization Name" value={data.organizationName || ''} onChange={(e) => updateData({ organizationName: e.target.value })} required />
            <PxInput label="Organization Type" value={data.organizationType || ''} onChange={(e) => updateData({ organizationType: e.target.value })} />
          </>
        )}

        <PxInput label="Location" value={data.location} onChange={(e) => updateData({ location: e.target.value })} placeholder="e.g., Cairo, Egypt" required />
      </div>

      <div>
        <label className="block text-sm font-pixel text-white mb-2">Bio (optional)</label>
        <textarea
          value={data.bio}
          onChange={(e) => updateData({ bio: e.target.value })}
          className="w-full clip-px border-px border-electric-teal bg-dark-surface/20 text-white font-body text-sm p-3"
          rows={4}
          placeholder={data.userType === 'organization' ? 'What is your mission?' : 'What motivates you to volunteer?'}
        />
      </div>
    </div>
  );
};

