'use client';

import { useState } from 'react';
import { PxButton, PxCard, PxLoading, PxBadge, PxChip } from '@seraaj/ui';
import { Header } from '@/components/navigation/Header';
import { useToast } from '@/contexts/ToastContext';

// Define match response type based on actual API
interface MatchResponse {
  id: string;
  volunteerId: string;
  opportunityId: string;
  organizationId: string;
  score: number;
  scoreComponents: {
    distance: number;
    skills: number;
    availability: number;
  };
  explanation: string[];
  generatedAt: string;
  status: string;
}

export default function DemoPage() {
  const [matches, setMatches] = useState<MatchResponse[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const { showSuccess, showError, showInfo } = useToast();

  const loadMatches = async () => {
    try {
      setIsLoading(true);
      showInfo('Scanning for perfect quests... 🔍');
      
      const response = await fetch('http://localhost:8000/api/volunteer/quick-match', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          volunteerId: 'demo-hero-' + Date.now(),
          limit: 10
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data: MatchResponse[] = await response.json();
      setMatches(data);
      showSuccess(`Found ${data.length} epic quests for you! 🎆`);
    } catch (error) {
      console.error('Failed to load matches:', error);
      showError('Failed to load quests. The realm might be offline.');
    } finally {
      setIsLoading(false);
    }
  };

  const testApplication = async (opportunityId: string) => {
    try {
      showInfo('Submitting heroic application... 📨');
      
      const response = await fetch('http://localhost:8000/api/volunteer/apply', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          volunteerId: 'demo-hero-' + Date.now(),
          opportunityId,
          coverLetter: 'I am excited to join this heroic quest and make a positive impact!'
        })
      });
      
      if (response.ok) {
        showSuccess('Application submitted successfully! 🎆 Your heroic credentials have been sent!');
        // Remove applied opportunity from list
        setMatches(prev => prev.filter(m => m.opportunityId !== opportunityId));
      } else {
        const error = await response.json().catch(() => ({ detail: 'Application failed' }));
        showError(`Application failed: ${error.detail}`);
      }
    } catch (error) {
      console.error('Failed to apply:', error);
      showError('Failed to submit application. The quest masters might be busy.');
    }
  };

  const getMatchBadgeVariant = (score: number) => {
    const percentage = Math.round(score * 100);
    if (percentage >= 85) return 'premium';
    if (percentage >= 70) return 'success';
    if (percentage >= 50) return 'warning';
    return 'default';
  };

  const getMatchEmoji = (score: number) => {
    const percentage = Math.round(score * 100);
    if (percentage >= 85) return '🎆';
    if (percentage >= 70) return '✨';
    if (percentage >= 50) return '🔥';
    return '💫';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-deepIndigo to-ink">
      <Header />
      
      <main className="max-w-6xl mx-auto p-6">
        <div className="mb-8">
          <h1 className="text-3xl font-pixel text-primary dark:text-neon-cyan mb-2">
            🎮 LIVE API DEMO 🎮
          </h1>
          <p className="text-white text-lg mb-4">
            Real-time integration with backend services! Watch the magic happen.
          </p>
          
          <div className="space-x-4">
            <PxButton 
              variant="primary" 
              onClick={loadMatches}
              disabled={isLoading}
            >
              {isLoading ? '⏳ SCANNING...' : '🔄 FIND QUEST MATCHES'}
            </PxButton>
            
            <PxButton 
              variant="secondary" 
              onClick={() => setMatches([])}
            >
              🗑️ CLEAR RESULTS
            </PxButton>
          </div>
        </div>

        {isLoading && (
          <div className="flex justify-center py-12">
            <PxLoading size="lg" variant="bright" text="Connecting to backend services..." />
          </div>
        )}

        {matches.length > 0 && (
          <>
            <div className="mb-6">
              <PxBadge variant="info" size="md">
                🎯 {matches.length} live matches from backend API
              </PxBadge>
            </div>
            
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {matches.map((match) => {
                const matchScore = Math.round(match.score * 100);
                return (
                  <PxCard key={match.id} variant="default" className="h-full">
                    <div className="space-y-4">
                      {/* Header */}
                      <div className="space-y-2">
                        <div className="flex items-start justify-between">
                          <h3 className="text-ink dark:text-white font-pixel text-sm leading-tight">
                            🏆 QUEST {match.opportunityId.toUpperCase()}
                          </h3>
                          <PxBadge 
                            variant={getMatchBadgeVariant(match.score)} 
                            size="sm"
                            animated={matchScore >= 85}
                          >
                            {getMatchEmoji(match.score)} {matchScore}%
                          </PxBadge>
                        </div>
                        
                        <p className="text-ink dark:text-white text-xs">
                          🏰 {match.organizationId.toUpperCase()}
                        </p>
                        
                        <p className="text-electric-teal text-xs font-pixel">
                          📍 MENA REGION • ID: {match.id.slice(0, 8)}...
                        </p>
                      </div>

                      {/* Match Breakdown */}
                      <div className="clip-px border-px border-electric-teal/30 bg-primary/5 p-2">
                        <p className="text-xs font-pixel text-electric-teal mb-1">
                          ✨ LIVE MATCH DATA:
                        </p>
                        <div className="space-y-1 text-xs text-ink dark:text-white">
                          <div className="flex justify-between">
                            <span>📍 Distance:</span>
                            <span className="text-success">{Math.round(match.scoreComponents.distance * 100)}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span>🎆 Skills:</span>
                            <span className="text-warning">{Math.round(match.scoreComponents.skills * 100)}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span>⏰ Availability:</span>
                            <span className="text-info">{Math.round(match.scoreComponents.availability * 100)}%</span>
                          </div>
                        </div>
                      </div>

                      {/* AI Explanation */}
                      <div className="space-y-2">
                        <p className="text-electric-teal text-xs font-pixel">
                          🤖 AI REASONING:
                        </p>
                        <div className="space-y-1">
                          {match.explanation.map((reason, index) => (
                            <div key={index} className="flex items-start space-x-2">
                              <span className="text-primary text-xs">•</span>
                              <span className="text-ink dark:text-white text-xs">{reason}</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Status & Timestamp */}
                      <div className="space-y-1">
                        <div className="flex items-center justify-between">
                          <PxChip variant={match.status === 'pending' ? 'default' : 'selected'} size="sm">
                            {match.status === 'pending' ? '⏳' : '✅'} {match.status.toUpperCase()}
                          </PxChip>
                          <span className="text-xs text-gray-400">
                            {new Date(match.generatedAt).toLocaleTimeString()}
                          </span>
                        </div>
                      </div>

                      {/* Action */}
                      <div className="pt-2">
                        <PxButton
                          variant={matchScore >= 70 ? "success" : "primary"}
                          size="sm"
                          className="w-full"
                          onClick={() => testApplication(match.opportunityId)}
                        >
                          🚀 TEST APPLICATION
                        </PxButton>
                      </div>
                    </div>
                  </PxCard>
                );
              })}
            </div>
          </>
        )}

        {/* API Info */}
        <div className="mt-12">
          <PxCard variant="default">
            <div className="space-y-4">
              <h3 className="text-lg font-pixel text-primary">
                🔧 BACKEND INTEGRATION STATUS
              </h3>
              
              <div className="grid md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <h4 className="font-pixel text-sm text-electric-teal">WORKING ENDPOINTS:</h4>
                  <div className="space-y-1 text-xs text-ink dark:text-white">
                    <div className="flex items-center space-x-2">
                      <span className="text-success">✅</span>
                      <span>GET /api/health - Service health check</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-success">✅</span>
                      <span>POST /api/volunteer/quick-match - AI matching</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-warning">⚠</span>
                      <span>POST /api/volunteer/apply - Application (partial)</span>
                    </div>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <h4 className="font-pixel text-sm text-electric-teal">AUTH SERVICES:</h4>
                  <div className="space-y-1 text-xs text-ink dark:text-white">
                    <div className="flex items-center space-x-2">
                      <span className="text-error">❌</span>
                      <span>POST /api/auth/register - User registration</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-error">❌</span>
                      <span>POST /api/auth/login - User authentication</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-warning">⚠</span>
                      <span>Using test user IDs for demo</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </PxCard>
        </div>
      </main>
    </div>
  );
}