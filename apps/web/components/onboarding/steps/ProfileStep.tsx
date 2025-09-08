"use client";

import React from 'react';
import { PxInput } from '@/components/forms/PxInput';
import { OnboardingData } from '../OnboardingFlow';

const ORGANIZATION_TYPES = [
  { value: 'nonprofit', label: 'Non-profit' },
  { value: 'charity', label: 'Charity' },
  { value: 'ngo', label: 'NGO' },
  { value: 'social-enterprise', label: 'Social Enterprise' },
  { value: 'community-group', label: 'Community Group' },
];

const ORGANIZATION_SIZES = [
  { value: '1-5', label: '1-5 people' },
  { value: '6-20', label: '6-20 people' },
  { value: '21-50', label: '21-50 people' },
  { value: '50+', label: '50+ people' },
];

const LOCATIONS = [
  'Amman, Jordan',
  'Beirut, Lebanon', 
  'Cairo, Egypt',
  'Dubai, UAE',
  'Riyadh, Saudi Arabia',
  'Baghdad, Iraq',
  'Kuwait City, Kuwait',
  'Doha, Qatar',
  'Manama, Bahrain',
  'Muscat, Oman',
  'Other'
];

export const ProfileStep: React.FC<{
  data: OnboardingData;
  updateData: (u: Partial<OnboardingData>) => void;
  onNext?: () => void;
}> = ({ data, updateData }) => {
  return (
    <div className="space-y-6">
      <div className="text-center">
        <p className="text-white text-sm">
          {data.userType === 'organization' 
            ? 'Tell us about your quest-giving organization.' 
            : 'Tell us about yourself, brave hero.'}
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
            <div>
              <label className="block text-sm font-pixel text-white mb-2">Organization Type</label>
              <select
                value={data.organizationType || ''}
                onChange={(e) => updateData({ organizationType: e.target.value })}
                className="w-full clip-px border-px border-electric-teal bg-dark-surface/20 text-white font-body text-sm p-3"
              >
                <option value="">Select type...</option>
                {ORGANIZATION_TYPES.map(type => (
                  <option key={type.value} value={type.value}>{type.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-pixel text-white mb-2">Organization Size</label>
              <select
                value={data.organizationSize || ''}
                onChange={(e) => updateData({ organizationSize: e.target.value })}
                className="w-full clip-px border-px border-electric-teal bg-dark-surface/20 text-white font-body text-sm p-3"
              >
                <option value="">Select size...</option>
                {ORGANIZATION_SIZES.map(size => (
                  <option key={size.value} value={size.value}>{size.label}</option>
                ))}
              </select>
            </div>
          </>
        )}

        <div>
          <label className="block text-sm font-pixel text-white mb-2">Location *</label>
          <select
            value={data.location}
            onChange={(e) => updateData({ location: e.target.value })}
            className="w-full clip-px border-px border-electric-teal bg-dark-surface/20 text-white font-body text-sm p-3"
            required
          >
            <option value="">Select location...</option>
            {LOCATIONS.map(location => (
              <option key={location} value={location}>{location}</option>
            ))}
          </select>
        </div>
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

