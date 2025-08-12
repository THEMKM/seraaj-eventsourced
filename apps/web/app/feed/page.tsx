'use client';

import { PxButton, PxCard } from '@seraaj/ui';
import { VolunteerApi } from '@seraaj/sdk-bff';

export default function FeedPage() {
  const handleQuickMatch = async () => {
    try {
      // Example of using the SDK - this proves types are wired without making network assumptions
      const volunteerApi = new VolunteerApi();
      console.log('VolunteerApi instance created:', volunteerApi);
      // Note: Not actually calling the API here to avoid network dependencies
    } catch (error) {
      console.error('Error with volunteer API:', error);
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-deepIndigo to-ink p-4">
      <div className="max-w-4xl mx-auto py-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-pixel text-primary dark:text-neon-cyan mb-2">
            🎆 QUEST BOARD 🎆
          </h1>
          <div className="text-xl font-pixel text-pixel-coral dark:text-neon-pink mb-4">
            AVAILABLE ADVENTURES
          </div>
          <p className="text-white mb-6">
            🚀 Choose your next epic volunteer quest!
          </p>
          <PxButton variant="success" onClick={handleQuickMatch}>
            ✨ QUEST MATCH
          </PxButton>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          <PxCard variant="default" className="hover:scale-105 transition-transform duration-300">
            <div className="flex items-center mb-2">
              <span className="text-2xl mr-2">🌱</span>
              <h3 className="text-lg font-pixel text-primary mb-0">
                GARDEN QUEST
              </h3>
            </div>
            <p className="text-sm text-ink dark:text-white mb-3">
              🌿 Battle the weeds and restore nature's harmony this weekend!
            </p>
            <div className="flex gap-2">
              <PxButton variant="secondary" size="sm">
                🔍 DETAILS
              </PxButton>
              <PxButton variant="success" size="sm">
                🚀 JOIN QUEST
              </PxButton>
            </div>
          </PxCard>

          <PxCard variant="glow" className="hover:scale-105 transition-transform duration-300">
            <div className="flex items-center mb-2">
              <span className="text-2xl mr-2">🍞</span>
              <h3 className="text-lg font-pixel text-sunBurst mb-0">
                HUNGER FIGHTER
              </h3>
            </div>
            <p className="text-sm text-white mb-3">
              ⚔️ Defeat hunger by distributing magical food supplies to families!
            </p>
            <div className="flex gap-2">
              <PxButton variant="secondary" size="sm">
                🔍 DETAILS
              </PxButton>
              <PxButton variant="success" size="sm">
                🚀 JOIN QUEST
              </PxButton>
            </div>
          </PxCard>

          <PxCard variant="default" className="hover:scale-105 transition-transform duration-300">
            <div className="flex items-center mb-2">
              <span className="text-2xl mr-2">🎓</span>
              <h3 className="text-lg font-pixel text-primary mb-0">
                WISDOM KEEPER
              </h3>
            </div>
            <p className="text-sm text-ink dark:text-white mb-3">
              🧙 Share your knowledge magic with young adventurers!
            </p>
            <div className="flex gap-2">
              <PxButton variant="secondary" size="sm">
                🔍 DETAILS
              </PxButton>
              <PxButton variant="success" size="sm">
                🚀 JOIN QUEST
              </PxButton>
            </div>
          </PxCard>

          <PxCard variant="default" className="hover:scale-105 transition-transform duration-300">
            <div className="flex items-center mb-2">
              <span className="text-2xl mr-2">👩‍💼</span>
              <h3 className="text-lg font-pixel text-primary mb-0">
                ELDER GUARDIAN
              </h3>
            </div>
            <p className="text-sm text-ink dark:text-white mb-3">
              💖 Share stories and companionship with wise elders!
            </p>
            <div className="flex gap-2">
              <PxButton variant="secondary" size="sm">
                🔍 DETAILS
              </PxButton>
              <PxButton variant="success" size="sm">
                🚀 JOIN QUEST
              </PxButton>
            </div>
          </PxCard>
        </div>
      </div>
    </main>
  );
}