# Issue #3: Port V2 Advanced Search Interface with Event-Driven Backend

## 🎯 **OBJECTIVE**
Migrate V2's sophisticated search interface to our event-sourced implementation, providing users with advanced filtering, sorting, and search capabilities while maintaining our event-driven architecture.

## 🏗️ **ARCHITECTURE CONTEXT**
- **Current**: Basic opportunity browsing in `apps/web/app/opportunities/page.tsx`
- **V2 Source**: `C:\Users\Mohamad\Documents\Claude\Seraaj\apps\web\components\search\`
- **Target**: Rich search interface backed by event-sourced data
- **Backend Flow**: Search Queries → BFF → Matching Service → Event Store Projections

## ⚠️ **CRITICAL WARNINGS - MEMORIZE THESE**
1. **DO NOT** modify the Matching service API without understanding the event flow
2. **DO NOT** hardcode search options - make them configurable/dynamic
3. **DO NOT** break existing opportunity browsing until new search is working
4. **DO NOT** copy V2's state management without adapting to our contexts
5. **DO NOT** assume V2's data structure matches our event projections

## 📊 **CURRENT VS V2 SEARCH COMPARISON**

### **Current Search (Basic)**
```typescript
// Location: apps/web/app/opportunities/page.tsx
// Features:
// - Simple opportunity list display
// - Basic matching score visualization  
// - Gaming theme presentation
// - Integrated with OpportunitiesContext

// Limitations:
// - No search/filter options
// - No sorting capabilities
// - No saved searches
// - No advanced criteria selection
```

### **V2 Search (Advanced)**
```typescript
// Location: C:\Users\Mohamad\Documents\Claude\Seraaj\apps\web\components\search\
// Components:
// - AdvancedSearch.tsx (main search interface)
// - SearchResults.tsx (results display)  
// - SavedSearches.tsx (search history)

// Features:
// - Text search with autocomplete
// - Multi-criteria filtering (location, skills, causes, time)
// - Chip-based filter selection
// - Sort options (relevance, date, match score)
// - Date range filtering
// - Remote work toggle
// - Active filter count
// - Clear all filters
// - Collapsible advanced panel
// - Search suggestions
```

## 🗺️ **MIGRATION STRATEGY**

### **Phase 3A: Component Structure Analysis (45 minutes)**
1. Map V2 search components to our architecture
2. Identify current search/filter backend endpoints
3. Plan integration with OpportunitiesContext
4. Document search state management approach

### **Phase 3B: Search Interface Migration (2 hours)**
1. Port AdvancedSearch component with adaptations
2. Create search state management
3. Integrate with existing opportunity display
4. Add search result management

### **Phase 3C: Backend Integration (1 hour)**
1. Connect to Matching service search endpoints
2. Test search performance with event projections
3. Implement search analytics (optional)

### **Phase 3D: Advanced Features (1 hour)**  
1. Add saved searches functionality
2. Implement search suggestions
3. Add search result analytics

## 🔧 **DETAILED IMPLEMENTATION**

### **Step 1: Backend Search API Analysis**

#### **1.1: Current Search Capabilities**
```typescript
// Examine: services/matching/api.py or equivalent
// Document what search endpoints exist:

/* CURRENT SEARCH API MAPPING:
GET /matches/opportunities/:volunteerId
- Parameters: limit, filters?, sort?
- Returns: Array of matched opportunities with scores

POST /search/opportunities  
- Body: search criteria
- Returns: filtered/sorted opportunities

MISSING APIs (may need to implement):
- GET /search/suggestions
- POST /search/save
- GET /search/saved/:userId
*/
```

#### **1.2: Event Projection Analysis**
```typescript
// Check: services/matching/repository.py or similar
// Document what fields are searchable:

/* SEARCHABLE FIELDS FROM EVENT PROJECTIONS:
Opportunity fields:
- title, description
- location, country, remote_allowed
- causes[], skills_required[], skills_preferred[]
- time_commitment, urgency
- volunteers_needed, application_deadline
- organization_name (via join/projection)

Volunteer fields (for reverse matching):
- skills[], interests[], causes[]
- location, availability
- experience_level
*/
```

### **Step 2: Search State Management**

#### **2.1: Search Context Creation**
```typescript
// Create: apps/web/contexts/SearchContext.tsx
// Manage search state and API calls

import React, { createContext, useContext, useState, useCallback } from 'react';

interface SearchFilters {
  query: string;
  location: string;
  causes: string[];
  skills: string[];
  timeCommitment: string[];
  type: string[];
  remote: boolean;
  sortBy: 'relevance' | 'date' | 'match-score' | 'time-commitment';
  datePosted: 'any' | 'today' | 'week' | 'month';
  minMatchScore?: number;
}

interface SearchContextType {
  // Search state
  filters: SearchFilters;
  searchResults: Array<any>;
  isSearching: boolean;
  hasSearched: boolean;
  searchError: string | null;
  
  // Search actions  
  updateFilters: (newFilters: Partial<SearchFilters>) => void;
  performSearch: () => Promise<void>;
  clearSearch: () => void;
  resetFilters: () => void;
  
  // Saved searches (if implemented)
  savedSearches: Array<any>;
  saveCurrentSearch: (name: string) => Promise<void>;
  loadSavedSearch: (searchId: string) => Promise<void>;
  deleteSavedSearch: (searchId: string) => Promise<void>;
}

const SearchContext = createContext<SearchContextType | undefined>(undefined);

export const SearchProvider: React.FC<{ children: React.ReactNode }> = ({ 
  children 
}) => {
  // Default filter state
  const [filters, setFilters] = useState<SearchFilters>({
    query: '',
    location: '',
    causes: [],
    skills: [],
    timeCommitment: [],
    type: [],
    remote: false,
    sortBy: 'relevance',
    datePosted: 'any',
  });
  
  const [searchResults, setSearchResults] = useState<Array<any>>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [savedSearches, setSavedSearches] = useState<Array<any>>([]);
  
  const updateFilters = useCallback((newFilters: Partial<SearchFilters>) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
  }, []);
  
  const performSearch = useCallback(async () => {
    setIsSearching(true);
    setSearchError(null);
    
    try {
      // Call our BFF search endpoint
      const searchParams = {
        query: filters.query,
        filters: {
          location: filters.location,
          causes: filters.causes,
          skills: filters.skills,
          timeCommitment: filters.timeCommitment,
          type: filters.type,
          remote: filters.remote,
          datePosted: filters.datePosted,
        },
        sort: filters.sortBy,
        minMatchScore: filters.minMatchScore || 0.3,
      };
      
      // Use existing BFF SDK or create new search endpoint
      const response = await bffSdk.opportunities.search(searchParams);
      
      setSearchResults(response.opportunities || []);
      setHasSearched(true);
      
      // Optional: Track search analytics
      // await bffSdk.analytics.trackSearch(searchParams);
      
    } catch (error) {
      console.error('Search failed:', error);
      setSearchError('Search failed. Please try again.');
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  }, [filters]);
  
  const clearSearch = useCallback(() => {
    setSearchResults([]);
    setHasSearched(false);
    setSearchError(null);
  }, []);
  
  const resetFilters = useCallback(() => {
    setFilters({
      query: '',
      location: '',
      causes: [],
      skills: [],
      timeCommitment: [],
      type: [],
      remote: false,
      sortBy: 'relevance',
      datePosted: 'any',
    });
    clearSearch();
  }, [clearSearch]);
  
  // Saved searches implementation
  const saveCurrentSearch = useCallback(async (name: string) => {
    try {
      const searchToSave = {
        name,
        filters,
        createdAt: new Date().toISOString(),
      };
      
      // Save via BFF
      const savedSearch = await bffSdk.users.saveSearch(searchToSave);
      setSavedSearches(prev => [...prev, savedSearch]);
      
    } catch (error) {
      console.error('Failed to save search:', error);
      throw error;
    }
  }, [filters]);
  
  const value: SearchContextType = {
    filters,
    searchResults,
    isSearching,
    hasSearched,  
    searchError,
    updateFilters,
    performSearch,
    clearSearch,
    resetFilters,
    savedSearches,
    saveCurrentSearch,
    loadSavedSearch: async () => {}, // Implement if needed
    deleteSavedSearch: async () => {}, // Implement if needed
  };
  
  return (
    <SearchContext.Provider value={value}>
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

### **Step 3: Advanced Search Component Migration**

#### **3.1: Main Search Interface**
```typescript
// Create: apps/web/components/search/AdvancedSearch.tsx
// Adapted from V2 but integrated with our SearchContext

import React, { useState } from 'react';
import { useSearch } from '@/contexts/SearchContext';
import { PxButton, PxInput, PxChip, PxCard } from '@seraaj/ui';

export const AdvancedSearch: React.FC = () => {
  const {
    filters,
    updateFilters,
    performSearch,
    resetFilters,
    isSearching,
  } = useSearch();
  
  const [showAdvanced, setShowAdvanced] = useState(false);
  
  // Copy V2's predefined options but make them configurable
  const causes = [
    'Education', 'Health', 'Environment', 'Poverty', 'Human Rights',
    'Refugees', 'Women Empowerment', 'Youth Development', 'Elderly Care',
    'Disability Support', 'Mental Health', 'Community Development',
    'Food Security', 'Water & Sanitation', 'Technology for Good'
  ];

  const skills = [
    'Teaching', 'Mentoring', 'Social Media', 'Graphic Design', 'Writing',
    'Photography', 'Video Editing', 'Web Development', 'Marketing',
    'Project Management', 'Event Planning', 'Fundraising', 'Public Speaking',
    'Translation', 'Data Analysis', 'Research', 'Healthcare', 'Counseling'
  ];

  const timeCommitments = [
    '1-2 hours/week', '3-5 hours/week', '6-10 hours/week', '10+ hours/week',
    'One-time event', 'Flexible schedule', 'Weekends only', 'Evenings only'
  ];

  const opportunityTypes = [
    'Direct Service', 'Advocacy', 'Research', 'Capacity Building',
    'Emergency Response', 'Policy Work', 'Creative Projects',
    'Technology Solutions', 'Community Outreach', 'Training & Workshops'
  ];

  // Note: In production, these should come from API/config
  const locations = [
    'Amman, Jordan', 'Beirut, Lebanon', 'Cairo, Egypt', 'Dubai, UAE',
    'Riyadh, Saudi Arabia', 'Baghdad, Iraq', 'Kuwait City, Kuwait',
    'Doha, Qatar', 'Manama, Bahrain', 'Muscat, Oman'
  ];
  
  const toggleArrayFilter = (key: keyof SearchFilters, value: string) => {
    const current = filters[key] as string[];
    const updated = current.includes(value)
      ? current.filter(item => item !== value)
      : [...current, value];
    updateFilters({ [key]: updated });
  };
  
  const activeFiltersCount = 
    (filters.location ? 1 : 0) +
    filters.causes.length +
    filters.skills.length +
    filters.timeCommitment.length +
    filters.type.length +
    (filters.remote ? 1 : 0) +
    (filters.sortBy !== 'relevance' ? 1 : 0) +
    (filters.datePosted !== 'any' ? 1 : 0);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    performSearch();
  };

  return (
    <div className="space-y-4">
      {/* Main Search Bar */}
      <form onSubmit={handleSearchSubmit} className="flex gap-3">
        <div className="flex-1">
          <PxInput
            value={filters.query}
            onChange={(e) => updateFilters({ query: e.target.value })}
            placeholder="🔍 Search for quests by title, cause, or organization..."
            className="text-lg"
          />
        </div>
        
        <PxButton
          variant="secondary"
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center gap-2"
        >
          🎯 Filters
          {activeFiltersCount > 0 && (
            <span className="bg-primary dark:bg-neon-cyan text-ink dark:text-dark-bg text-xs font-pixel px-2 py-1 rounded">
              {activeFiltersCount}
            </span>
          )}
        </PxButton>
        
        <PxButton
          variant="primary"
          type="submit"
          disabled={isSearching}
          className="hover:shadow-px-glow"
        >
          {isSearching ? '⏳ SEARCHING...' : '🚀 SEARCH QUESTS'}
        </PxButton>
      </form>

      {/* Advanced Filters Panel */}
      {showAdvanced && (
        <PxCard className="p-6 space-y-6 bg-white dark:bg-dark-surface animate-px-fade-in">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-pixel text-ink dark:text-white">
              ⚙️ ADVANCED QUEST FILTERS
            </h3>
            {activeFiltersCount > 0 && (
              <PxButton variant="secondary" size="sm" onClick={resetFilters}>
                🗑️ Clear All
              </PxButton>
            )}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left Column - Basic Filters */}
            <div className="space-y-4">
              {/* Location Filter */}
              <div>
                <label className="block text-sm font-pixel text-ink dark:text-white mb-2">
                  📍 Location
                </label>
                <select
                  value={filters.location}
                  onChange={(e) => updateFilters({ location: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-ink dark:border-dark-border rounded-lg bg-white dark:bg-dark-surface text-ink dark:text-white font-body focus:ring-2 focus:ring-primary dark:focus:ring-neon-cyan focus:border-transparent transition-all duration-300"
                >
                  <option value="">🌍 Any Location</option>
                  {locations.map(location => (
                    <option key={location} value={location}>{location}</option>
                  ))}
                </select>
              </div>

              {/* Remote Work Toggle */}
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="remote"
                  checked={filters.remote}
                  onChange={(e) => updateFilters({ remote: e.target.checked })}
                  className="w-4 h-4 text-primary bg-white border-2 border-ink rounded focus:ring-primary dark:focus:ring-neon-cyan dark:bg-dark-surface dark:border-dark-border"
                />
                <label htmlFor="remote" className="ml-2 text-sm font-pixel text-ink dark:text-white">
                  💻 Remote Work Available
                </label>
              </div>

              {/* Sort Options */}
              <div>
                <label className="block text-sm font-pixel text-ink dark:text-white mb-2">
                  📊 Sort By
                </label>
                <select
                  value={filters.sortBy}
                  onChange={(e) => updateFilters({ sortBy: e.target.value as any })}
                  className="w-full px-4 py-3 border-2 border-ink dark:border-dark-border rounded-lg bg-white dark:bg-dark-surface text-ink dark:text-white font-body focus:ring-2 focus:ring-primary dark:focus:ring-neon-cyan focus:border-transparent transition-all duration-300"
                >
                  <option value="relevance">🎯 Best Match</option>
                  <option value="date">📅 Most Recent</option>
                  <option value="match-score">⭐ Highest Match Score</option>
                  <option value="time-commitment">⏰ Time Commitment</option>
                </select>
              </div>

              {/* Date Posted Filter */}
              <div>
                <label className="block text-sm font-pixel text-ink dark:text-white mb-2">
                  📅 Posted Within
                </label>
                <select
                  value={filters.datePosted}
                  onChange={(e) => updateFilters({ datePosted: e.target.value as any })}
                  className="w-full px-4 py-3 border-2 border-ink dark:border-dark-border rounded-lg bg-white dark:bg-dark-surface text-ink dark:text-white font-body focus:ring-2 focus:ring-primary dark:focus:ring-neon-cyan focus:border-transparent transition-all duration-300"
                >
                  <option value="any">🕐 Any Time</option>
                  <option value="today">🌅 Today</option>
                  <option value="week">📆 This Week</option>
                  <option value="month">🗓️ This Month</option>
                </select>
              </div>
            </div>

            {/* Right Column - Chip Filters */}
            <div className="space-y-4">
              {/* Causes Filter */}
              <div>
                <label className="block text-sm font-pixel text-ink dark:text-white mb-3">
                  ❤️ Causes ({filters.causes.length} selected)
                </label>
                <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto border border-ink/20 dark:border-dark-border rounded p-2">
                  {causes.map(cause => (
                    <PxChip
                      key={cause}
                      variant={filters.causes.includes(cause) ? 'selected' : 'default'}
                      onClick={() => toggleArrayFilter('causes', cause)}
                      className="cursor-pointer"
                      size="sm"
                    >
                      {cause}
                    </PxChip>
                  ))}
                </div>
              </div>

              {/* Skills Filter */}
              <div>
                <label className="block text-sm font-pixel text-ink dark:text-white mb-3">
                  🛠️ Skills Needed ({filters.skills.length} selected)
                </label>
                <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto border border-ink/20 dark:border-dark-border rounded p-2">
                  {skills.map(skill => (
                    <PxChip
                      key={skill}
                      variant={filters.skills.includes(skill) ? 'selected' : 'default'}
                      onClick={() => toggleArrayFilter('skills', skill)}
                      className="cursor-pointer"
                      size="sm"
                    >
                      {skill}
                    </PxChip>
                  ))}
                </div>
              </div>

              {/* Time Commitment Filter */}
              <div>
                <label className="block text-sm font-pixel text-ink dark:text-white mb-3">
                  ⏰ Time Commitment ({filters.timeCommitment.length} selected)
                </label>
                <div className="flex flex-wrap gap-2">
                  {timeCommitments.map(time => (
                    <PxChip
                      key={time}
                      variant={filters.timeCommitment.includes(time) ? 'selected' : 'default'}
                      onClick={() => toggleArrayFilter('timeCommitment', time)}
                      className="cursor-pointer"
                      size="sm"
                    >
                      {time}
                    </PxChip>
                  ))}
                </div>
              </div>

              {/* Opportunity Type Filter */}
              <div>
                <label className="block text-sm font-pixel text-ink dark:text-white mb-3">
                  🎭 Quest Type ({filters.type.length} selected)
                </label>
                <div className="flex flex-wrap gap-2">
                  {opportunityTypes.map(type => (
                    <PxChip
                      key={type}
                      variant={filters.type.includes(type) ? 'selected' : 'default'}
                      onClick={() => toggleArrayFilter('type', type)}
                      className="cursor-pointer"
                      size="sm"
                    >
                      {type}
                    </PxChip>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-between pt-4 border-t border-ink/20 dark:border-dark-border">
            <div className="text-sm text-ink dark:text-gray-400">
              {activeFiltersCount === 0 
                ? '🔍 No active filters - showing all quests'
                : `🎯 ${activeFiltersCount} filter${activeFiltersCount === 1 ? '' : 's'} active`
              }
            </div>
            <div className="flex gap-3">
              <PxButton 
                variant="secondary" 
                onClick={() => setShowAdvanced(false)}
              >
                ❌ Close Filters
              </PxButton>
              <PxButton 
                variant="primary" 
                onClick={() => { performSearch(); setShowAdvanced(false); }}
                disabled={isSearching}
                className="hover:shadow-px-glow"
              >
                {isSearching ? '⏳ SEARCHING...' : '🚀 Apply Filters'}
              </PxButton>
            </div>
          </div>
        </PxCard>
      )}
    </div>
  );
};
```

### **Step 4: Search Results Integration**

#### **4.1: Update Opportunities Page**
```typescript
// Modify: apps/web/app/opportunities/page.tsx
// Add search functionality to existing page

'use client';

import { useEffect } from 'react';
import { AdvancedSearch } from '@/components/search/AdvancedSearch';
import { SearchProvider, useSearch } from '@/contexts/SearchContext';
import { useOpportunities } from '@/contexts/OpportunitiesContext';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Header } from '@/components/navigation/Header';
import { PxButton, PxCard, PxLoading, PxBadge } from '@seraaj/ui';

// Separate component to use search context
const OpportunitiesContent = () => {
  const { 
    searchResults, 
    hasSearched, 
    isSearching, 
    searchError 
  } = useSearch();
  
  const { 
    opportunities, 
    isLoading, 
    loadQuickMatches 
  } = useOpportunities();

  // Use search results if available, otherwise show matched opportunities
  const displayOpportunities = hasSearched ? searchResults : opportunities;

  useEffect(() => {
    // Load quick matches on initial load if no search performed
    if (!hasSearched && opportunities.length === 0) {
      loadQuickMatches(10);
    }
  }, [hasSearched, opportunities.length, loadQuickMatches]);

  const showLoading = isSearching || (isLoading && !hasSearched);
  const showEmptyState = !showLoading && displayOpportunities.length === 0;

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
            {hasSearched 
              ? "Search results for your quest criteria"
              : "Discover opportunities perfectly matched to your heroic abilities!"
            }
          </p>
          
          {/* Quick Actions */}
          {!hasSearched && (
            <div className="flex space-x-4 mb-6">
              <PxButton 
                variant="primary" 
                onClick={() => loadQuickMatches(10)}
                disabled={isLoading}
              >
                {isLoading ? '⏳ SCANNING...' : '🔄 REFRESH MATCHES'}
              </PxButton>
              
              <PxButton 
                variant="secondary" 
                onClick={() => loadQuickMatches(20)}
                disabled={isLoading}
              >
                🌌 SHOW MORE
              </PxButton>
            </div>
          )}
        </div>

        {/* Advanced Search Component */}
        <div className="mb-8">
          <AdvancedSearch />
        </div>

        {/* Search Error */}
        {searchError && (
          <PxCard variant="error" className="mb-6">
            <div className="text-center py-4">
              <div className="text-4xl mb-2">⚠️</div>
              <p className="text-red-500 font-pixel">Search Error: {searchError}</p>
            </div>
          </PxCard>
        )}

        {/* Loading State */}
        {showLoading ? (
          <div className="flex justify-center py-12">
            <PxLoading 
              size="lg" 
              variant="bright" 
              text={isSearching ? "Searching for perfect quests..." : "Finding matches for you..."} 
            />
          </div>
        ) : (
          <>
            {/* Empty State */}
            {showEmptyState ? (
              <PxCard variant="default" className="text-center py-12">
                <div className="text-6xl mb-4">
                  {hasSearched ? '🤷‍♂️' : '🔍'}
                </div>
                <h3 className="text-lg font-pixel text-primary mb-2">
                  {hasSearched ? 'NO QUESTS MATCH YOUR SEARCH' : 'NO QUESTS FOUND'}
                </h3>
                <p className="text-white text-sm mb-4">
                  {hasSearched 
                    ? 'Try adjusting your search filters or expanding your criteria.'
                    : 'Try refreshing or adjusting your profile to find new opportunities!'
                  }
                </p>
                <div className="flex gap-3 justify-center">
                  {hasSearched && (
                    <PxButton variant="secondary" onClick={() => window.location.reload()}>
                      🗑️ Clear Search
                    </PxButton>
                  )}
                  <PxButton variant="primary" onClick={() => loadQuickMatches(10)}>
                    🔍 {hasSearched ? 'Show All Matches' : 'Search for Quests'}
                  </PxButton>
                </div>
              </PxCard>
            ) : (
              <>
                {/* Results Header */}
                <div className="mb-4 flex items-center justify-between">
                  <PxBadge variant="info" size="md">
                    🎯 Found {displayOpportunities.length} {hasSearched ? 'search results' : 'matching quests'}
                  </PxBadge>
                  
                  {hasSearched && (
                    <PxButton 
                      variant="secondary" 
                      size="sm"
                      onClick={() => window.location.reload()}
                    >
                      🔄 Show All Matches
                    </PxButton>
                  )}
                </div>
                
                {/* Results Grid */}
                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                  {displayOpportunities.map((opportunity) => {
                    // Adapt to different data structures (search results vs matches)
                    const matchScore = hasSearched 
                      ? Math.round((opportunity.relevanceScore || 0.5) * 100)
                      : Math.round((opportunity.score || 0.5) * 100);
                      
                    return (
                      <OpportunityCard 
                        key={opportunity.id || opportunity.opportunityId}
                        opportunity={opportunity}
                        matchScore={matchScore}
                        isSearchResult={hasSearched}
                      />
                    );
                  })}
                </div>
              </>
            )}
          </>
        )}
      </main>
    </div>
  );
};

// Main page component with search provider
export default function OpportunitiesPage() {
  return (
    <ProtectedRoute>
      <SearchProvider>
        <OpportunitiesContent />
      </SearchProvider>
    </ProtectedRoute>
  );
}

// Opportunity card component (extract from existing code)
const OpportunityCard = ({ opportunity, matchScore, isSearchResult }) => {
  // Implementation similar to current card but handle both data structures
  return (
    <PxCard variant="default" className="h-full">
      {/* Card content adapted for both search results and matches */}
    </PxCard>
  );
};
```

### **Step 5: Backend Integration**

#### **5.1: Add Search Endpoint to BFF SDK**
```typescript
// Add to: packages/bff-sdk/src/opportunities.ts or equivalent

interface SearchOpportunitiesParams {
  query?: string;
  filters?: {
    location?: string;
    causes?: string[];
    skills?: string[];
    timeCommitment?: string[];
    type?: string[];
    remote?: boolean;
    datePosted?: string;
  };
  sort?: string;
  minMatchScore?: number;
  limit?: number;
  offset?: number;
}

interface SearchOpportunitiesResponse {
  opportunities: Array<any>;
  total: number;
  hasMore: boolean;
  searchId?: string; // For analytics
}

export class OpportunitiesAPI {
  // ... existing methods
  
  async search(params: SearchOpportunitiesParams): Promise<SearchOpportunitiesResponse> {
    try {
      const response = await this.client.post('/opportunities/search', params);
      return response.data;
    } catch (error) {
      console.error('Search failed:', error);
      throw error;
    }
  }
  
  async getSuggestions(query: string): Promise<string[]> {
    try {
      const response = await this.client.get(`/opportunities/search/suggestions?q=${encodeURIComponent(query)}`);
      return response.data.suggestions || [];
    } catch (error) {
      console.error('Failed to get suggestions:', error);
      return [];
    }
  }
}
```

#### **5.2: Update BFF to Handle Search Requests**
```python
# Add to: bff/main.py or equivalent
# New search endpoint that calls Matching service

@app.post("/api/opportunities/search")
async def search_opportunities(search_params: dict, current_user: User = Depends(get_current_user)):
    try:
        # Transform search params for Matching service
        matching_params = {
            "volunteer_id": current_user.volunteer_id,
            "query": search_params.get("query"),
            "filters": search_params.get("filters", {}),
            "sort": search_params.get("sort", "relevance"),
            "min_score": search_params.get("minMatchScore", 0.3),
            "limit": search_params.get("limit", 20),
        }
        
        # Call Matching service
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{MATCHING_SERVICE_URL}/search/opportunities",
                json=matching_params
            )
            response.raise_for_status()
            
        search_results = response.json()
        
        # Optional: Log search for analytics
        # await log_search_event(current_user.id, search_params, len(search_results.get("opportunities", [])))
        
        return search_results
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@app.get("/api/opportunities/search/suggestions")
async def get_search_suggestions(q: str, current_user: User = Depends(get_current_user)):
    try:
        # Get suggestions from Matching service or cache
        # This could be implemented as:
        # 1. Recent search terms
        # 2. Popular causes/skills
        # 3. Organization names
        # 4. Location suggestions
        
        suggestions = []
        
        # Example implementation:
        if len(q) >= 2:
            # Get from Matching service
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{MATCHING_SERVICE_URL}/search/suggestions?query={q}"
                )
                if response.status_code == 200:
                    suggestions = response.json().get("suggestions", [])
        
        return {"suggestions": suggestions}
        
    except Exception as e:
        logger.error(f"Failed to get suggestions: {e}")
        return {"suggestions": []}
```

## 🧪 **TESTING STRATEGY**

### **Unit Tests**
```typescript
// Create: apps/web/components/search/__tests__/
// Test search components and context

describe('SearchContext', () => {
  it('should update filters correctly', () => {
    // Test filter updates
  });
  
  it('should perform search with correct parameters', async () => {
    // Mock BFF SDK calls
    // Test search execution
  });
  
  it('should handle search errors gracefully', async () => {
    // Test error handling
  });
});

describe('AdvancedSearch', () => {
  it('should render all filter options', () => {
    // Test component rendering
  });
  
  it('should toggle filters correctly', () => {
    // Test chip selection
  });
});
```

### **Integration Tests**
```typescript
// Test complete search flow:
// 1. User enters search criteria
// 2. Filters are applied correctly
// 3. Search request is sent to backend
// 4. Results are displayed properly
// 5. Error states work correctly
```

### **Performance Tests**
- Search response time < 2 seconds
- Filter updates are responsive
- Large result sets don't cause UI lag
- Search suggestions load quickly

## 📝 **ACCEPTANCE CRITERIA**

### **Must Have**
- [ ] Advanced search interface matches V2 functionality
- [ ] All filter types work (text, location, chips, toggles)
- [ ] Search integrates with existing opportunity display
- [ ] Results show proper match scores and explanations
- [ ] Loading and error states handled properly
- [ ] Search performance is acceptable (<2s response time)

### **Should Have**
- [ ] Search suggestions as user types
- [ ] Filter counts show number of selected items
- [ ] Clear all filters functionality
- [ ] Search results sorting options work
- [ ] Back/forward navigation preserves search state

### **Could Have**
- [ ] Saved searches functionality
- [ ] Search analytics tracking
- [ ] Search result export
- [ ] Advanced sorting algorithms
- [ ] Search history

## 🚨 **ROLLBACK PLAN**
```bash
# If search breaks opportunity browsing:
git stash  # Save work
git checkout -- apps/web/app/opportunities/page.tsx
git checkout -- apps/web/contexts/

# Verify existing opportunity browsing works
# Fix issues before re-applying changes
```

## ⏱️ **ESTIMATED TIME**
- **Component Analysis**: 45 minutes
- **Search Interface Migration**: 2 hours
- **Backend Integration**: 1 hour
- **Advanced Features**: 1 hour
- **Testing**: 45 minutes
- **Total**: 5.5 hours

## 👥 **DEPENDENCIES**
- Issue #1 (Px Components) must be completed first
- Matching service must support search endpoints
- BFF SDK must be updated for search functionality

## 🏁 **DEFINITION OF DONE**
- Advanced search interface fully functional
- All filter types work correctly
- Search integrates with opportunity display
- Backend search endpoints implemented
- Performance meets requirements
- No regressions in existing functionality
- Code reviewed and tested