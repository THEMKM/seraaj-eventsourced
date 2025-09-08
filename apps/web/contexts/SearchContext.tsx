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