'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { PxButton, PxChip } from '@seraaj/ui';
import { PxInput } from '@/components/forms/PxInput';

export function HeroSearch() {
  const router = useRouter();
  const { isAuthenticated } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCause, setSelectedCause] = useState<string | null>(null);

  const popularCauses = [
    'Education', 'Health', 'Environment', 'Refugees', 'Youth Development'
  ];

  const handleSearch = () => {
    if (isAuthenticated) {
      const params = new URLSearchParams();
      if (searchQuery.trim()) {
        params.set('q', searchQuery.trim());
      }
      if (selectedCause) {
        params.set('cause', selectedCause);
      }
      router.push(`/search?${params.toString()}`);
    } else {
      router.push('/auth?mode=register');
    }
  };

  const handleCauseClick = (cause: string) => {
    setSelectedCause(selectedCause === cause ? null : cause);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className="bg-white dark:bg-dark-surface clip-px border-px shadow-px dark:shadow-px-dark p-6 max-w-3xl mx-auto">
      <div className="text-center mb-6">
        <h3 className="text-xl font-pixel text-ink dark:text-white mb-2">
          FIND YOUR PERFECT MATCH
        </h3>
        <p className="text-ink dark:text-gray-300 text-sm">
          Search thousands of volunteer opportunities in the MENA region
        </p>
      </div>

      {/* Search Input */}
      <div className="flex gap-3 mb-4">
        <div className="flex-1">
          <PxInput
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Search by role, organization, or skill..."
            className="text-base"
          />
        </div>
        <PxButton
          variant="primary"
          onClick={handleSearch}
          className="hover:shadow-px-glow px-8"
        >
          🔍 SEARCH
        </PxButton>
      </div>

      {/* Popular Causes */}
      <div className="space-y-3">
        <p className="text-sm font-pixel text-ink dark:text-gray-400">
          POPULAR CAUSES:
        </p>
        <div className="flex flex-wrap gap-2">
          {popularCauses.map((cause) => (
            <PxChip
              key={cause}
              variant={selectedCause === cause ? 'selected' : 'default'}
              onClick={() => handleCauseClick(cause)}
              className="cursor-pointer hover:shadow-px transition-all duration-300"
              size="sm"
            >
              {cause}
            </PxChip>
          ))}
        </div>
      </div>

      {/* Quick Stats */}
      <div className="flex items-center justify-center gap-8 mt-6 pt-4 border-t border-ink/20 dark:border-dark-border text-sm text-ink dark:text-gray-400">
        <div className="text-center">
          <div className="font-pixel text-primary dark:text-neon-cyan">500+</div>
          <div>Opportunities</div>
        </div>
        <div className="text-center">
          <div className="font-pixel text-primary dark:text-neon-cyan">150+</div>
          <div>Organizations</div>
        </div>
        <div className="text-center">
          <div className="font-pixel text-primary dark:text-neon-cyan">12</div>
          <div>Countries</div>
        </div>
      </div>
    </div>
  );
}