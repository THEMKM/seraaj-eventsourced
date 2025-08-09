'use client';

import { PxButton, PxCard } from '@seraaj/ui';

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-deepIndigo to-ink p-4">
      <div className="max-w-4xl mx-auto py-12">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-pixel text-sunBurst mb-4 animate-pxGlow">
            SERAAJ
          </h1>
          <p className="text-lg text-white mb-8">
            Connect volunteers with meaningful opportunities in their communities
          </p>
          <PxButton size="lg" onClick={() => console.log('Get Started clicked')}>
            Get Started
          </PxButton>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          <PxCard variant="default">
            <h3 className="text-lg font-pixel text-sunBurst mb-2">For Volunteers</h3>
            <p className="text-sm text-white mb-4">
              Find opportunities that match your skills and passions
            </p>
            <PxButton variant="secondary" size="sm">
              Browse Opportunities
            </PxButton>
          </PxCard>

          <PxCard variant="glow">
            <h3 className="text-lg font-pixel text-sunBurst mb-2">For Organizations</h3>
            <p className="text-sm text-white mb-4">
              Connect with passionate volunteers ready to make a difference
            </p>
            <PxButton variant="secondary" size="sm">
              Post Opportunity
            </PxButton>
          </PxCard>

          <PxCard variant="default">
            <h3 className="text-lg font-pixel text-sunBurst mb-2">Quick Match</h3>
            <p className="text-sm text-white mb-4">
              Get matched with opportunities tailored to you
            </p>
            <PxButton variant="success" size="sm">
              Find My Match
            </PxButton>
          </PxCard>
        </div>
      </div>
    </main>
  );
}