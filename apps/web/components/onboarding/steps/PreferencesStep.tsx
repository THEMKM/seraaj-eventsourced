"use client";

import React from 'react';
import { PxChip } from '@seraaj/ui';
import { OnboardingData } from '../OnboardingFlow';

const CAUSES = [
  'Education', 'Health', 'Environment', 'Poverty', 'Human Rights',
  'Refugees', 'Women Empowerment', 'Youth Development', 'Elderly Care',
  'Disability Support', 'Mental Health', 'Community Development',
  'Food Security', 'Water & Sanitation', 'Technology for Good'
];

const SKILLS = [
  'Teaching', 'Mentoring', 'Social Media', 'Graphic Design', 'Writing',
  'Photography', 'Video Editing', 'Web Development', 'Marketing',
  'Project Management', 'Event Planning', 'Fundraising', 'Public Speaking',
  'Translation', 'Data Analysis', 'Research', 'Healthcare', 'Counseling'
];

const INTERESTS = [
  'Direct Service', 'Advocacy', 'Research', 'Capacity Building',
  'Emergency Response', 'Policy Work', 'Creative Projects',
  'Technology Solutions', 'Community Outreach', 'Training & Workshops'
];

const AVAILABILITY_OPTIONS = [
  { value: '1-2', label: '1-2 hours/week (Minimal)' },
  { value: '3-5', label: '3-5 hours/week (Moderate)' },
  { value: '6-10', label: '6-10 hours/week (Significant)' },
  { value: '10+', label: '10+ hours/week (Extensive)' },
];

export const PreferencesStep: React.FC<{
  data: OnboardingData;
  updateData: (u: Partial<OnboardingData>) => void;
  onNext?: () => void;
}> = ({ data, updateData }) => {
  const toggle = (arr: string[], v: string) => arr.includes(v) ? arr.filter(i => i !== v) : [...arr, v];

  return (
    <div className="space-y-6">
      <div className="text-center">
        <p className="text-white text-sm">
          {data.userType === 'organization' ? 'What causes do you focus on?' : 'Choose your causes, skills and availability.'}
        </p>
      </div>

      {/* Causes */}
      <div>
        <h3 className="text-white font-pixel text-sm mb-2">Causes *</h3>
        <div className="flex flex-wrap gap-2">
          {CAUSES.map(c => (
            <PxChip key={c} variant={data.causes.includes(c) ? 'selected' : 'default'} onClick={() => updateData({ causes: toggle(data.causes, c) })}>
              {c}
            </PxChip>
          ))}
        </div>
      </div>

      {/* Volunteer-only preferences */}
      {data.userType !== 'organization' && (
        <>
          <div>
            <h3 className="text-white font-pixel text-sm mb-2">Skills</h3>
            <div className="flex flex-wrap gap-2">
              {SKILLS.map(s => (
                <PxChip key={s} variant={data.skills.includes(s) ? 'selected' : 'default'} onClick={() => updateData({ skills: toggle(data.skills, s) })}>
                  {s}
                </PxChip>
              ))}
            </div>
          </div>

          <div>
            <h3 className="text-white font-pixel text-sm mb-2">Interests</h3>
            <div className="flex flex-wrap gap-2">
              {INTERESTS.map(i => (
                <PxChip key={i} variant={data.interests.includes(i) ? 'selected' : 'default'} onClick={() => updateData({ interests: toggle(data.interests, i) })}>
                  {i}
                </PxChip>
              ))}
            </div>
          </div>

          <div>
            <h3 className="text-white font-pixel text-sm mb-2">Time Commitment *</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {AVAILABILITY_OPTIONS.map(option => (
                <div
                  key={option.value}
                  className={`clip-px border-px p-3 cursor-pointer ${data.availability === option.value ? 'border-success bg-success/10' : 'border-electric-teal bg-dark-surface/20'}`}
                  onClick={() => updateData({ availability: option.value })}
                >
                  <p className="text-white text-xs font-pixel">{option.label}</p>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

