'use client';

import { useAuth } from '@/contexts/AuthContext';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Header } from '@/components/navigation/Header';
import { PxButton, PxCard, PxChip } from '@seraaj/ui';
import { PxInput } from '@/components/forms/PxInput';
import { UserRole } from '@seraaj/sdk-bff';

export default function ProfilePage() {
  const { user } = useAuth();

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gradient-to-br from-deepIndigo to-ink">
        <Header />
      <main className="max-w-4xl mx-auto p-6">
        <div className="mb-8">
          <h1 className="text-4xl font-pixel text-primary dark:text-neon-cyan mb-2">
            👤 HERO PROFILE 👤
          </h1>
          <p className="text-white text-lg">
            Manage your hero stats and quest preferences
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          <PxCard variant="default" className="col-span-full md:col-span-1">
            <div className="flex items-center mb-4">
              <span className="text-3xl mr-3">🎆</span>
              <h2 className="text-xl font-pixel text-primary mb-0">HERO DATA</h2>
            </div>
            <div className="space-y-4">
              <PxInput
                label="📛 HERO NAME"
                type="text"
                value={user?.name || ''}
                placeholder="Enter your hero name"
                readOnly
              />
              <PxInput
                label="✉️ EMAIL CONTACT"
                type="email"
                value={user?.email || ''}
                placeholder="hero@example.com"
                readOnly
              />
              <div>
                <p className="text-sm font-pixel text-ink dark:text-white mb-2">🎖️ CLASS:</p>
                <PxChip variant="selected" size="sm">
                  {user?.role === UserRole.VOLUNTEER ? '🎆 HERO' : '🏰 GUILD MASTER'}
                </PxChip>
              </div>
              <PxButton variant="primary">
                ✏️ EDIT PROFILE
              </PxButton>
            </div>
          </PxCard>

          <PxCard variant="glow" className="col-span-full md:col-span-1">
            <div className="flex items-center mb-4">
              <span className="text-3xl mr-3">📈</span>
              <h2 className="text-xl font-pixel text-sunBurst mb-0">HERO STATS</h2>
            </div>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center clip-px border-px border-electric-teal p-3">
                  <div className="text-2xl font-pixel text-primary mb-1">127</div>
                  <div className="text-xs text-white">⏱️ HOURS</div>
                </div>
                <div className="text-center clip-px border-px border-electric-teal p-3">
                  <div className="text-2xl font-pixel text-primary mb-1">8</div>
                  <div className="text-xs text-white">🎯 QUESTS</div>
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-white">🏰 Guilds Helped:</span>
                  <PxChip variant="selected" size="sm">5</PxChip>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-white">🌟 Impact Level:</span>
                  <PxChip variant="selected" size="sm" className="bg-pixel-coral">🔥 LEGENDARY</PxChip>
                </div>
              </div>
              
              <div>
                <p className="text-sm font-pixel text-white mb-2">🏅 ACHIEVEMENT BADGES:</p>
                <div className="flex flex-wrap gap-2">
                  <PxChip variant="selected" size="sm">
                    🎆 NEWCOMER
                  </PxChip>
                  <PxChip variant="selected" size="sm">
                    🔥 QUEST MASTER
                  </PxChip>
                  <PxChip variant="default" size="sm" className="opacity-50">
                    ✨ LEGEND
                  </PxChip>
                </div>
              </div>
            </div>
          </PxCard>

          <PxCard variant="default" className="col-span-full">
            <div className="flex items-center mb-4">
              <span className="text-2xl mr-2">📅</span>
              <h2 className="text-xl font-pixel text-primary mb-0">
                QUEST JOURNAL
              </h2>
            </div>
            <div className="space-y-4">
              <div className="clip-px border-px border-success p-3 bg-success/10">
                <div className="flex items-center mb-1">
                  <span className="text-lg mr-2">✅</span>
                  <p className="text-ink dark:text-white text-sm font-pixel">
                    GARDEN QUEST COMPLETED!
                  </p>
                </div>
                <p className="text-xs text-ink dark:text-gray-300 ml-6">🕰️ 2 days ago • +15 Impact Points</p>
              </div>
              <div className="clip-px border-px border-warning p-3 bg-warning/10">
                <div className="flex items-center mb-1">
                  <span className="text-lg mr-2">⏳</span>
                  <p className="text-ink dark:text-white text-sm font-pixel">
                    FOOD BANK MISSION PENDING
                  </p>
                </div>
                <p className="text-xs text-ink dark:text-gray-300 ml-6">🕰️ 5 days ago • Awaiting guild approval</p>
              </div>
              <div className="clip-px border-px border-info p-3 bg-info/10">
                <div className="flex items-center mb-1">
                  <span className="text-lg mr-2">✨</span>
                  <p className="text-ink dark:text-white text-sm font-pixel">
                    NEW MENTOR QUEST MATCHED!
                  </p>
                </div>
                <p className="text-xs text-ink dark:text-gray-300 ml-6">🕰️ 1 week ago • 87% match rate</p>
              </div>
            </div>
            
            <div className="mt-6 pt-4 border-t border-ink/20 dark:border-dark-border">
              <div className="grid md:grid-cols-3 gap-3">
                <PxButton variant="primary" size="sm" className="w-full">
                  🎯 DASHBOARD
                </PxButton>
                <PxButton variant="secondary" size="sm" className="w-full">
                  🔍 NEW QUESTS
                </PxButton>
                <PxButton variant="success" size="sm" className="w-full">
                  ✨ QUICK MATCH
                </PxButton>
              </div>
            </div>
          </PxCard>
        </div>
      </main>
      </div>
    </ProtectedRoute>
  );
}