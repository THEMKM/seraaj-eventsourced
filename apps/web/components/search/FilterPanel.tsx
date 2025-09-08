import React, { useState } from 'react';
import { useSearch } from '@/contexts/SearchContext';
import { PxButton, PxChip, PxCard } from '@seraaj/ui';

const CAUSES = [
  'Education', 'Health', 'Environment', 'Poverty', 
  'Human Rights', 'Youth Development', 'Elderly Care', 
  'Community Development', 'Technology for Good'
];

const TIME_COMMITMENTS = [
  '1-2 hours/week', '3-5 hours/week', '6-10 hours/week', 
  '10+ hours/week', 'One-time event', 'Flexible schedule'
];

const LOCATIONS = [
  'Amman, Jordan', 'Beirut, Lebanon', 'Cairo, Egypt',
  'Dubai, UAE', 'Riyadh, Saudi Arabia', 'Remote'
];

export const FilterPanel: React.FC = () => {
  const { filters, updateFilters, clearFilters, activeFilterCount } = useSearch();
  const [isOpen, setIsOpen] = useState(false);

  const toggleCause = (cause: string) => {
    const newCauses = filters.causes.includes(cause)
      ? filters.causes.filter(c => c !== cause)
      : [...filters.causes, cause];
    updateFilters({ causes: newCauses });
  };

  const toggleTimeCommitment = (time: string) => {
    const newTime = filters.timeCommitment.includes(time)
      ? filters.timeCommitment.filter(t => t !== time)
      : [...filters.timeCommitment, time];
    updateFilters({ timeCommitment: newTime });
  };

  return (
    <div className="mb-6">
      {/* Filter Toggle Button */}
      <div className="flex gap-3 items-center mb-4">
        <PxButton
          variant="secondary"
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-2"
        >
          🎯 Filters
          {activeFilterCount > 0 && (
            <span className="bg-primary text-white text-xs px-2 py-1 rounded-full">
              {activeFilterCount}
            </span>
          )}
        </PxButton>
        
        {activeFilterCount > 0 && (
          <PxButton variant="secondary" size="sm" onClick={clearFilters}>
            Clear All
          </PxButton>
        )}
      </div>

      {/* Filter Panel */}
      {isOpen && (
        <PxCard className="p-6 space-y-6 bg-dark-surface">
          {/* Location Filter */}
          <div>
            <label className="block text-sm font-pixel text-electric-teal mb-3">
              📍 Location
            </label>
            <select
              value={filters.location}
              onChange={(e) => updateFilters({ location: e.target.value })}
              className="w-full px-4 py-3 border-2 border-electric-teal bg-dark-surface text-white rounded-lg font-body text-sm"
            >
              <option value="">Any Location</option>
              {LOCATIONS.map(location => (
                <option key={location} value={location}>{location}</option>
              ))}
            </select>
          </div>

          {/* Causes Filter */}
          <div>
            <label className="block text-sm font-pixel text-electric-teal mb-3">
              ❤️ Causes ({filters.causes.length} selected)
            </label>
            <div className="flex flex-wrap gap-2">
              {CAUSES.map(cause => (
                <PxChip
                  key={cause}
                  variant={filters.causes.includes(cause) ? 'selected' : 'default'}
                  onClick={() => toggleCause(cause)}
                  className="cursor-pointer"
                >
                  {cause}
                </PxChip>
              ))}
            </div>
          </div>

          {/* Time Commitment Filter */}
          <div>
            <label className="block text-sm font-pixel text-electric-teal mb-3">
              ⏰ Time Commitment ({filters.timeCommitment.length} selected)
            </label>
            <div className="flex flex-wrap gap-2">
              {TIME_COMMITMENTS.map(time => (
                <PxChip
                  key={time}
                  variant={filters.timeCommitment.includes(time) ? 'selected' : 'default'}
                  onClick={() => toggleTimeCommitment(time)}
                  className="cursor-pointer"
                >
                  {time}
                </PxChip>
              ))}
            </div>
          </div>

          {/* Apply Button */}
          <div className="pt-4 border-t border-electric-teal/30">
            <PxButton 
              variant="primary" 
              onClick={() => setIsOpen(false)}
              className="w-full"
            >
              Apply Filters
            </PxButton>
          </div>
        </PxCard>
      )}
    </div>
  );
};