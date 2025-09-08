# Build Advanced Search Interface with Autocomplete

## 📋 **Task Description**
Create a sophisticated search interface with location autocomplete, skills suggestions, real-time filtering, and complex query building. This replicates V2's advanced search capabilities with gaming aesthetics.

## 🔍 **Current State**
Basic filtering exists from Issue #54. Need to enhance with autocomplete, advanced operators, and real-time suggestions.

## 🎯 **Exact Steps to Follow**

### Step 1: Examine existing FilterPanel
Use Read tool to examine `apps/web/components/search/FilterPanel.tsx` from Issue #54 to understand current filtering structure.

### Step 2: Create SearchAutocomplete component
Create `apps/web/components/search/SearchAutocomplete.tsx`:

```typescript
import React, { useState, useEffect, useRef } from 'react';
import { PxCard } from '@seraaj/ui';

interface SearchSuggestion {
  id: string;
  text: string;
  type: 'skill' | 'location' | 'cause' | 'organization';
  icon: string;
}

interface SearchAutocompleteProps {
  placeholder: string;
  suggestions: SearchSuggestion[];
  onSelect: (suggestion: SearchSuggestion) => void;
  onInputChange: (value: string) => void;
  value: string;
  className?: string;
}

export const SearchAutocomplete: React.FC<SearchAutocompleteProps> = ({
  placeholder,
  suggestions,
  onSelect,
  onInputChange,
  value,
  className = ''
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setIsOpen(suggestions.length > 0 && value.length > 0);
  }, [suggestions, value]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setHighlightedIndex(prev => 
          prev < suggestions.length - 1 ? prev + 1 : 0
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setHighlightedIndex(prev => 
          prev > 0 ? prev - 1 : suggestions.length - 1
        );
        break;
      case 'Enter':
        e.preventDefault();
        if (highlightedIndex >= 0) {
          onSelect(suggestions[highlightedIndex]);
          setIsOpen(false);
        }
        break;
      case 'Escape':
        setIsOpen(false);
        inputRef.current?.blur();
        break;
    }
  };

  const handleSuggestionClick = (suggestion: SearchSuggestion) => {
    onSelect(suggestion);
    setIsOpen(false);
    inputRef.current?.focus();
  };

  return (
    <div className={`relative ${className}`}>
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={(e) => onInputChange(e.target.value)}
        onKeyDown={handleKeyDown}
        onFocus={() => setIsOpen(suggestions.length > 0 && value.length > 0)}
        placeholder={placeholder}
        className="w-full px-4 py-3 border-2 border-electric-teal bg-dark-surface text-white rounded-lg font-pixel focus:outline-none focus:ring-2 focus:ring-electric-teal"
      />

      {isOpen && (
        <PxCard className="absolute top-full left-0 right-0 mt-2 z-50 max-h-64 overflow-y-auto border-2 border-electric-teal">
          <div ref={listRef}>
            {suggestions.map((suggestion, index) => (
              <div
                key={suggestion.id}
                className={`px-4 py-3 cursor-pointer transition-colors flex items-center gap-3 ${
                  index === highlightedIndex
                    ? 'bg-primary/20 text-primary'
                    : 'hover:bg-electric-teal/10 text-white'
                }`}
                onClick={() => handleSuggestionClick(suggestion)}
              >
                <span className="text-lg">{suggestion.icon}</span>
                <div className="flex-1">
                  <span className="font-pixel text-sm">{suggestion.text}</span>
                  <div className="text-xs text-gray-400 capitalize">
                    {suggestion.type}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </PxCard>
      )}
    </div>
  );
};
```

### Step 3: Create AdvancedSearchPanel component
Create `apps/web/components/search/AdvancedSearchPanel.tsx`:

```typescript
import React, { useState, useEffect } from 'react';
import { SearchAutocomplete } from './SearchAutocomplete';
import { PxButton, PxCard, PxChip, PxBadge } from '@seraaj/ui';

interface AdvancedFilters {
  searchQuery: string;
  locations: string[];
  skills: string[];
  causes: string[];
  organizations: string[];
  timeCommitment: string[];
  experienceLevel: string[];
  remoteOnly: boolean;
  datePosted: string;
  sortBy: string;
}

interface AdvancedSearchPanelProps {
  filters: AdvancedFilters;
  onFiltersChange: (filters: AdvancedFilters) => void;
  onSearch: () => void;
  onClear: () => void;
  totalResults: number;
  isSearching?: boolean;
}

// Mock suggestion data - in real implementation, fetch from API
const MOCK_SUGGESTIONS = [
  { id: '1', text: 'Teaching', type: 'skill' as const, icon: '🎓' },
  { id: '2', text: 'Amman, Jordan', type: 'location' as const, icon: '📍' },
  { id: '3', text: 'Education', type: 'cause' as const, icon: '❤️' },
  { id: '4', text: 'Green Earth Initiative', type: 'organization' as const, icon: '🏰' },
  { id: '5', text: 'Mentoring', type: 'skill' as const, icon: '🎓' },
  { id: '6', text: 'Healthcare', type: 'cause' as const, icon: '❤️' },
];

export const AdvancedSearchPanel: React.FC<AdvancedSearchPanelProps> = ({
  filters,
  onFiltersChange,
  onSearch,
  onClear,
  totalResults,
  isSearching = false
}) => {
  const [searchInput, setSearchInput] = useState('');
  const [suggestions, setSuggestions] = useState(MOCK_SUGGESTIONS);
  const [isExpanded, setIsExpanded] = useState(false);

  // Debounced search suggestions
  useEffect(() => {
    if (searchInput.length < 2) {
      setSuggestions([]);
      return;
    }

    const filtered = MOCK_SUGGESTIONS.filter(s => 
      s.text.toLowerCase().includes(searchInput.toLowerCase())
    );
    setSuggestions(filtered);
  }, [searchInput]);

  const handleSuggestionSelect = (suggestion: any) => {
    const { type, text } = suggestion;
    
    switch (type) {
      case 'skill':
        if (!filters.skills.includes(text)) {
          onFiltersChange({
            ...filters,
            skills: [...filters.skills, text]
          });
        }
        break;
      case 'location':
        if (!filters.locations.includes(text)) {
          onFiltersChange({
            ...filters,
            locations: [...filters.locations, text]
          });
        }
        break;
      case 'cause':
        if (!filters.causes.includes(text)) {
          onFiltersChange({
            ...filters,
            causes: [...filters.causes, text]
          });
        }
        break;
      case 'organization':
        if (!filters.organizations.includes(text)) {
          onFiltersChange({
            ...filters,
            organizations: [...filters.organizations, text]
          });
        }
        break;
    }
    
    setSearchInput('');
  };

  const removeFilter = (type: string, value: string) => {
    const newFilters = { ...filters };
    switch (type) {
      case 'skills':
        newFilters.skills = filters.skills.filter(s => s !== value);
        break;
      case 'locations':
        newFilters.locations = filters.locations.filter(l => l !== value);
        break;
      case 'causes':
        newFilters.causes = filters.causes.filter(c => c !== value);
        break;
      case 'organizations':
        newFilters.organizations = filters.organizations.filter(o => o !== value);
        break;
    }
    onFiltersChange(newFilters);
  };

  const getActiveFilterCount = () => {
    return (
      filters.locations.length +
      filters.skills.length +
      filters.causes.length +
      filters.organizations.length +
      filters.timeCommitment.length +
      filters.experienceLevel.length +
      (filters.remoteOnly ? 1 : 0) +
      (filters.datePosted !== 'any' ? 1 : 0)
    );
  };

  const activeFilterCount = getActiveFilterCount();

  return (
    <PxCard className="p-6 border-2 border-electric-teal mb-6">
      {/* Search Header */}
      <div className="flex items-center gap-4 mb-6">
        <div className="flex-1">
          <SearchAutocomplete
            placeholder="🔍 Search skills, locations, causes, or organizations..."
            suggestions={suggestions}
            onSelect={handleSuggestionSelect}
            onInputChange={setSearchInput}
            value={searchInput}
          />
        </div>
        <PxButton
          variant="primary"
          onClick={onSearch}
          loading={isSearching}
          className="px-6"
        >
          🎯 Search
        </PxButton>
      </div>

      {/* Active Filters Display */}
      {activeFilterCount > 0 && (
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-3">
            <PxBadge variant="info" size="sm">
              {activeFilterCount} Active Filter{activeFilterCount !== 1 ? 's' : ''}
            </PxBadge>
            <PxButton variant="secondary" size="sm" onClick={onClear}>
              Clear All
            </PxButton>
          </div>
          
          <div className="flex flex-wrap gap-2">
            {filters.skills.map(skill => (
              <PxChip
                key={skill}
                variant="selected"
                size="sm"
                className="cursor-pointer"
                onClick={() => removeFilter('skills', skill)}
              >
                🎓 {skill} ×
              </PxChip>
            ))}
            {filters.locations.map(location => (
              <PxChip
                key={location}
                variant="selected"
                size="sm"
                className="cursor-pointer"
                onClick={() => removeFilter('locations', location)}
              >
                📍 {location} ×
              </PxChip>
            ))}
            {filters.causes.map(cause => (
              <PxChip
                key={cause}
                variant="selected"
                size="sm"
                className="cursor-pointer"
                onClick={() => removeFilter('causes', cause)}
              >
                ❤️ {cause} ×
              </PxChip>
            ))}
            {filters.organizations.map(org => (
              <PxChip
                key={org}
                variant="selected"
                size="sm"
                className="cursor-pointer"
                onClick={() => removeFilter('organizations', org)}
              >
                🏰 {org} ×
              </PxChip>
            ))}
          </div>
        </div>
      )}

      {/* Advanced Filters Toggle */}
      <div className="border-t border-electric-teal/30 pt-4">
        <PxButton
          variant="secondary"
          size="sm"
          onClick={() => setIsExpanded(!isExpanded)}
          className="mb-4"
        >
          {isExpanded ? '▼' : '▶'} Advanced Filters
        </PxButton>

        {isExpanded && (
          <div className="grid md:grid-cols-2 gap-6">
            {/* Time Commitment */}
            <div>
              <label className="block text-sm font-pixel text-electric-teal mb-3">
                ⏰ Time Commitment
              </label>
              <div className="space-y-2">
                {['1-2 hours/week', '3-5 hours/week', '6-10 hours/week', '10+ hours/week', 'One-time event'].map(time => (
                  <label key={time} className="flex items-center gap-2 text-sm text-white cursor-pointer">
                    <input
                      type="checkbox"
                      checked={filters.timeCommitment.includes(time)}
                      onChange={(e) => {
                        const newTime = e.target.checked
                          ? [...filters.timeCommitment, time]
                          : filters.timeCommitment.filter(t => t !== time);
                        onFiltersChange({ ...filters, timeCommitment: newTime });
                      }}
                      className="rounded border-electric-teal"
                    />
                    {time}
                  </label>
                ))}
              </div>
            </div>

            {/* Experience Level */}
            <div>
              <label className="block text-sm font-pixel text-electric-teal mb-3">
                🎖️ Experience Level
              </label>
              <div className="space-y-2">
                {['Beginner friendly', 'Some experience preferred', 'Advanced skills required'].map(level => (
                  <label key={level} className="flex items-center gap-2 text-sm text-white cursor-pointer">
                    <input
                      type="checkbox"
                      checked={filters.experienceLevel.includes(level)}
                      onChange={(e) => {
                        const newLevel = e.target.checked
                          ? [...filters.experienceLevel, level]
                          : filters.experienceLevel.filter(l => l !== level);
                        onFiltersChange({ ...filters, experienceLevel: newLevel });
                      }}
                      className="rounded border-electric-teal"
                    />
                    {level}
                  </label>
                ))}
              </div>
            </div>

            {/* Date Posted */}
            <div>
              <label className="block text-sm font-pixel text-electric-teal mb-3">
                📅 Date Posted
              </label>
              <select
                value={filters.datePosted}
                onChange={(e) => onFiltersChange({ ...filters, datePosted: e.target.value })}
                className="w-full px-3 py-2 border border-electric-teal bg-dark-surface text-white rounded"
              >
                <option value="any">Any time</option>
                <option value="today">Today</option>
                <option value="week">This week</option>
                <option value="month">This month</option>
              </select>
            </div>

            {/* Sort By */}
            <div>
              <label className="block text-sm font-pixel text-electric-teal mb-3">
                📊 Sort By
              </label>
              <select
                value={filters.sortBy}
                onChange={(e) => onFiltersChange({ ...filters, sortBy: e.target.value })}
                className="w-full px-3 py-2 border border-electric-teal bg-dark-surface text-white rounded"
              >
                <option value="relevance">Best Match</option>
                <option value="date">Most Recent</option>
                <option value="location">Nearest First</option>
                <option value="organization">Organization A-Z</option>
              </select>
            </div>

            {/* Remote Only */}
            <div className="md:col-span-2">
              <label className="flex items-center gap-3 text-white cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.remoteOnly}
                  onChange={(e) => onFiltersChange({ ...filters, remoteOnly: e.target.checked })}
                  className="rounded border-electric-teal"
                />
                <span className="font-pixel">🌐 Remote opportunities only</span>
              </label>
            </div>
          </div>
        )}
      </div>

      {/* Results Count */}
      <div className="border-t border-electric-teal/30 pt-4 mt-4 text-center">
        <PxBadge variant="info" size="md">
          🎯 {totalResults} Quest{totalResults !== 1 ? 's' : ''} Found
        </PxBadge>
      </div>
    </PxCard>
  );
};
```

### Step 4: Update opportunities page to use advanced search
Modify `apps/web/app/opportunities/page.tsx` to integrate advanced search:

```typescript
'use client';

import { useEffect, useMemo, useState } from 'react';
import { SearchProvider, useSearch } from '@/contexts/SearchContext';
import { AdvancedSearchPanel } from '@/components/search/AdvancedSearchPanel';
import { useOpportunities } from '@/contexts/OpportunitiesContext';
// ... other imports

// Update the search context to include advanced filters
interface AdvancedFilters {
  searchQuery: string;
  locations: string[];
  skills: string[];
  causes: string[];
  organizations: string[];
  timeCommitment: string[];
  experienceLevel: string[];
  remoteOnly: boolean;
  datePosted: string;
  sortBy: string;
}

const OpportunitiesContent = () => {
  const { opportunities, isLoading, loadQuickMatches } = useOpportunities();
  const [advancedFilters, setAdvancedFilters] = useState<AdvancedFilters>({
    searchQuery: '',
    locations: [],
    skills: [],
    causes: [],
    organizations: [],
    timeCommitment: [],
    experienceLevel: [],
    remoteOnly: false,
    datePosted: 'any',
    sortBy: 'relevance'
  });
  const [isSearching, setIsSearching] = useState(false);

  // Advanced filtering logic
  const filteredAndSortedOpportunities = useMemo(() => {
    let filtered = opportunities.filter(opportunity => {
      // Location filter
      if (advancedFilters.locations.length > 0) {
        const hasLocation = advancedFilters.locations.some(location =>
          opportunity.organizationName?.toLowerCase().includes(location.toLowerCase()) ||
          opportunity.opportunityTitle?.toLowerCase().includes(location.toLowerCase())
        );
        if (!hasLocation && !advancedFilters.remoteOnly) return false;
      }

      // Skills filter
      if (advancedFilters.skills.length > 0) {
        const hasSkill = advancedFilters.skills.some(skill =>
          opportunity.opportunityTitle?.toLowerCase().includes(skill.toLowerCase())
        );
        if (!hasSkill) return false;
      }

      // Causes filter
      if (advancedFilters.causes.length > 0) {
        const hasCause = advancedFilters.causes.some(cause =>
          opportunity.opportunityTitle?.toLowerCase().includes(cause.toLowerCase()) ||
          opportunity.organizationName?.toLowerCase().includes(cause.toLowerCase())
        );
        if (!hasCause) return false;
      }

      // Organizations filter
      if (advancedFilters.organizations.length > 0) {
        const hasOrg = advancedFilters.organizations.some(org =>
          opportunity.organizationName?.toLowerCase().includes(org.toLowerCase())
        );
        if (!hasOrg) return false;
      }

      // Remote only filter
      if (advancedFilters.remoteOnly) {
        const isRemote = opportunity.opportunityTitle?.toLowerCase().includes('remote') ||
                         opportunity.organizationName?.toLowerCase().includes('remote');
        if (!isRemote) return false;
      }

      return true;
    });

    // Sorting
    switch (advancedFilters.sortBy) {
      case 'date':
        // Mock sorting by date - in real implementation, sort by actual dates
        filtered.sort((a, b) => b.id.localeCompare(a.id));
        break;
      case 'location':
        filtered.sort((a, b) => (a.organizationName || '').localeCompare(b.organizationName || ''));
        break;
      case 'organization':
        filtered.sort((a, b) => (a.organizationName || '').localeCompare(b.organizationName || ''));
        break;
      case 'relevance':
      default:
        // Keep current order (should be by match score in real implementation)
        break;
    }

    return filtered;
  }, [opportunities, advancedFilters]);

  useEffect(() => {
    if (opportunities.length === 0) {
      loadQuickMatches(50); // Load more for advanced filtering
    }
  }, [opportunities.length, loadQuickMatches]);

  const handleSearch = async () => {
    setIsSearching(true);
    // In real implementation, make API call with advanced filters
    await new Promise(resolve => setTimeout(resolve, 1000)); // Mock delay
    setIsSearching(false);
  };

  const handleClearFilters = () => {
    setAdvancedFilters({
      searchQuery: '',
      locations: [],
      skills: [],
      causes: [],
      organizations: [],
      timeCommitment: [],
      experienceLevel: [],
      remoteOnly: false,
      datePosted: 'any',
      sortBy: 'relevance'
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-deepIndigo to-ink">
      <Header />
      
      <main className="max-w-7xl mx-auto p-6">
        {/* Page Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-pixel text-primary mb-4">
            🔍 ADVANCED QUEST SEARCH 🔍
          </h1>
          <p className="text-white text-lg">
            Use the power of advanced search to find your perfect heroic mission!
          </p>
        </div>

        {/* Advanced Search Panel */}
        <AdvancedSearchPanel
          filters={advancedFilters}
          onFiltersChange={setAdvancedFilters}
          onSearch={handleSearch}
          onClear={handleClearFilters}
          totalResults={filteredAndSortedOpportunities.length}
          isSearching={isSearching}
        />

        {/* Results */}
        {isLoading ? (
          <div className="flex justify-center py-12">
            <PxLoading size="lg" variant="bright" text="Loading epic quests..." />
          </div>
        ) : (
          <>
            {filteredAndSortedOpportunities.length === 0 ? (
              <PxCard variant="default" className="text-center py-12">
                <div className="text-6xl mb-4">🤷‍♂️</div>
                <h3 className="text-lg font-pixel text-primary mb-2">
                  NO QUESTS MATCH YOUR SEARCH
                </h3>
                <p className="text-white text-sm mb-4">
                  Try adjusting your search criteria or clearing filters to see more opportunities.
                </p>
                <PxButton variant="primary" onClick={handleClearFilters}>
                  Clear All Filters
                </PxButton>
              </PxCard>
            ) : (
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {filteredAndSortedOpportunities.map((opportunity) => (
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

### Step 5: Add keyboard shortcuts for power users
Create `apps/web/hooks/useSearchShortcuts.tsx`:

```typescript
import { useEffect } from 'react';

export const useSearchShortcuts = (onFocusSearch: () => void, onClearSearch: () => void) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl/Cmd + K to focus search
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        onFocusSearch();
      }
      
      // Escape to clear search
      if (e.key === 'Escape') {
        onClearSearch();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onFocusSearch, onClearSearch]);
};
```

Use this hook in the AdvancedSearchPanel to add keyboard shortcuts.

## ✅ **Definition of Done**
- [ ] SearchAutocomplete component provides real-time suggestions
- [ ] Keyboard navigation works in autocomplete (arrows, enter, escape)
- [ ] AdvancedSearchPanel shows active filters with removal capability
- [ ] Advanced filters panel toggles open/closed
- [ ] All filter types work (skills, locations, causes, organizations)
- [ ] Sorting functionality works correctly
- [ ] Search suggestions are contextual and useful
- [ ] Real-time filter count updates
- [ ] Results update immediately when filters change
- [ ] Keyboard shortcuts work (Ctrl+K, Escape)
- [ ] Gaming theme consistent throughout interface

## 🧪 **How to Test**
1. Navigate to `/opportunities`
2. Type in search box and verify autocomplete appears
3. Test keyboard navigation in autocomplete
4. Select suggestions and verify they become active filters
5. Toggle advanced filters panel open/closed
6. Test all filter checkboxes and dropdowns
7. Verify active filter chips show and can be removed
8. Test "Clear All" functionality
9. Check that results update based on filters
10. Test keyboard shortcuts (Ctrl+K, Escape)
11. Verify sorting options work correctly

**This should take 5-6 hours to implement and test thoroughly.**