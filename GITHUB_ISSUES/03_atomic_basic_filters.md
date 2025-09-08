# Add Basic Filters to Opportunity Search

## 📋 **Task Description**
Add basic filtering functionality to the existing opportunities page. Users should be able to filter opportunities by location, causes, and time commitment.

## 🎯 **Exact Steps to Follow**

### Step 1: Create a search context
Create `apps/web/contexts/SearchContext.tsx`:

```typescript
import React, { createContext, useContext, useState } from 'react';

interface SearchFilters {
  location: string;
  causes: string[];
  timeCommitment: string[];
}

interface SearchContextType {
  filters: SearchFilters;
  updateFilters: (newFilters: Partial<SearchFilters>) => void;
  clearFilters: () => void;
  activeFilterCount: number;
}

const SearchContext = createContext<SearchContextType | undefined>(undefined);

export const SearchProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [filters, setFilters] = useState<SearchFilters>({
    location: '',
    causes: [],
    timeCommitment: []
  });

  const updateFilters = (newFilters: Partial<SearchFilters>) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
  };

  const clearFilters = () => {
    setFilters({
      location: '',
      causes: [],
      timeCommitment: []
    });
  };

  const activeFilterCount = 
    (filters.location ? 1 : 0) + 
    filters.causes.length + 
    filters.timeCommitment.length;

  return (
    <SearchContext.Provider value={{
      filters,
      updateFilters,
      clearFilters,
      activeFilterCount
    }}>
      {children}
    </SearchContext.Provider>
  );
};

export const useSearch = () => {
  const context = useContext(SearchContext);
  if (!context) {
    throw new Error('useSearch must be used within SearchProvider');
  }
  return context;
};
```

### Step 2: Create a FilterPanel component
Create `apps/web/components/search/FilterPanel.tsx`:

```typescript
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
              className="w-full px-4 py-3 border-2 border-electric-teal bg-dark-surface text-white rounded-lg"
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
                  size="sm"
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
                  size="sm"
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
```

### Step 3: Update the opportunities page to use filters
Modify `apps/web/app/opportunities/page.tsx`:

```typescript
'use client';

import { useEffect, useMemo } from 'react';
import { SearchProvider, useSearch } from '@/contexts/SearchContext';
import { FilterPanel } from '@/components/search/FilterPanel';
import { useOpportunities } from '@/contexts/OpportunitiesContext';
// ... other imports

// Create a content component that uses the search context
const OpportunitiesContent = () => {
  const { filters } = useSearch();
  const { opportunities, isLoading, loadQuickMatches } = useOpportunities();

  // Filter opportunities based on selected filters
  const filteredOpportunities = useMemo(() => {
    return opportunities.filter(opportunity => {
      // Location filter
      if (filters.location && filters.location !== 'Remote') {
        // Simple string match - in real implementation, this would be more sophisticated
        const hasLocation = opportunity.organizationName?.includes(filters.location) ||
                           opportunity.opportunityTitle?.toLowerCase().includes(filters.location.toLowerCase());
        if (!hasLocation) return false;
      }

      // Causes filter (simplified - assumes opportunity has causes data)
      if (filters.causes.length > 0) {
        // For now, we'll do a simple text search in title/description
        // In a real implementation, opportunities would have structured cause data
        const opportunityText = `${opportunity.opportunityTitle} ${opportunity.organizationName}`.toLowerCase();
        const hasCause = filters.causes.some(cause => 
          opportunityText.includes(cause.toLowerCase())
        );
        if (!hasCause) return false;
      }

      // Time commitment filter (simplified)
      if (filters.timeCommitment.length > 0) {
        // Simple text search for now
        const opportunityText = `${opportunity.opportunityTitle}`.toLowerCase();
        const hasTimeMatch = filters.timeCommitment.some(time => {
          if (time.includes('1-2') && opportunityText.includes('part')) return true;
          if (time.includes('flexible') && opportunityText.includes('flexible')) return true;
          return false;
        });
        if (!hasTimeMatch) return false;
      }

      return true;
    });
  }, [opportunities, filters]);

  useEffect(() => {
    if (opportunities.length === 0) {
      loadQuickMatches(20); // Load more for filtering
    }
  }, [opportunities.length, loadQuickMatches]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-deepIndigo to-ink">
      <Header />
      
      <main className="max-w-6xl mx-auto p-6">
        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-pixel text-primary dark:text-neon-cyan mb-2">
            🎯 QUEST BROWSER 🎯
          </h1>
          <p className="text-white text-lg mb-4">
            Discover opportunities perfectly matched to your heroic abilities!
          </p>
        </div>

        {/* Filter Panel */}
        <FilterPanel />

        {/* Results */}
        {isLoading ? (
          <div className="flex justify-center py-12">
            <PxLoading size="lg" variant="bright" text="Finding perfect quests..." />
          </div>
        ) : (
          <>
            {/* Results Count */}
            <div className="mb-4">
              <PxBadge variant="info" size="md">
                🎯 Found {filteredOpportunities.length} matching quests
              </PxBadge>
            </div>
            
            {filteredOpportunities.length === 0 ? (
              <PxCard variant="default" className="text-center py-12">
                <div className="text-6xl mb-4">🤷‍♂️</div>
                <h3 className="text-lg font-pixel text-primary mb-2">
                  NO QUESTS MATCH YOUR FILTERS
                </h3>
                <p className="text-white text-sm mb-4">
                  Try adjusting your filters or clearing them to see more opportunities.
                </p>
              </PxCard>
            ) : (
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {filteredOpportunities.map((opportunity) => (
                  // Your existing opportunity card component
                  <OpportunityCard key={opportunity.id} opportunity={opportunity} />
                ))}
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
};

// Main component with search provider
export default function OpportunitiesPage() {
  return (
    <ProtectedRoute>
      <SearchProvider>
        <OpportunitiesContent />
      </SearchProvider>
    </ProtectedRoute>
  );
}
```

### Step 4: Update PxChip component (if needed)
If PxChip doesn't exist yet, create a simple version in `packages/ui/src/components/Chip/`:

```typescript
// packages/ui/src/components/Chip/Chip.tsx
import React from 'react';
import { clsx } from 'clsx';

export interface ChipProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'selected';
  size?: 'sm' | 'md';
  children: React.ReactNode;
}

export const Chip: React.FC<ChipProps> = ({
  variant = 'default',
  size = 'md',
  className,
  children,
  ...props
}) => {
  return (
    <div
      className={clsx(
        'inline-flex items-center px-3 py-1 rounded-full text-sm font-pixel cursor-pointer transition-all',
        {
          'bg-gray-700 text-white border border-gray-600 hover:border-electric-teal': variant === 'default',
          'bg-primary text-white border border-primary': variant === 'selected',
          'text-xs px-2': size === 'sm',
          'text-sm px-3 py-1': size === 'md',
        },
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};
```

## ✅ **Definition of Done**
- [ ] Filter panel toggles open/closed correctly
- [ ] Location dropdown shows all predefined locations
- [ ] Cause chips can be selected/deselected with visual feedback
- [ ] Time commitment chips work correctly
- [ ] Active filter count shows in filter button
- [ ] Clear all filters button works
- [ ] Filtering actually reduces the displayed opportunities
- [ ] Results count updates based on applied filters
- [ ] Empty state shows when no matches found

## 🧪 **How to Test**
1. Navigate to `/opportunities`
2. Click "Filters" button to open panel
3. Select a location from dropdown
4. Click on some cause chips to select them
5. Select time commitment options
6. Verify filter count shows in button
7. See that opportunity list is filtered
8. Clear filters and verify all opportunities return
9. Test empty state by selecting very specific filters

**This should take 3-4 hours to implement and test thoroughly.**