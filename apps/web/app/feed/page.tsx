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
          <h1 className="text-3xl font-pixel text-sunBurst mb-4">
            VOLUNTEER FEED
          </h1>
          <p className="text-white mb-6">
            Discover opportunities that match your interests
          </p>
          <PxButton variant="success" onClick={handleQuickMatch}>
            Quick Match
          </PxButton>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          <PxCard variant="default">
            <h3 className="text-lg font-pixel text-sunBurst mb-2">
              Community Garden Cleanup
            </h3>
            <p className="text-sm text-white mb-3">
              Help maintain the local community garden this weekend.
            </p>
            <div className="flex gap-2">
              <PxButton variant="secondary" size="sm">
                Learn More
              </PxButton>
              <PxButton variant="success" size="sm">
                Apply
              </PxButton>
            </div>
          </PxCard>

          <PxCard variant="glow">
            <h3 className="text-lg font-pixel text-sunBurst mb-2">
              Food Bank Support
            </h3>
            <p className="text-sm text-white mb-3">
              Sort and distribute food donations to families in need.
            </p>
            <div className="flex gap-2">
              <PxButton variant="secondary" size="sm">
                Learn More
              </PxButton>
              <PxButton variant="success" size="sm">
                Apply
              </PxButton>
            </div>
          </PxCard>

          <PxCard variant="default">
            <h3 className="text-lg font-pixel text-sunBurst mb-2">
              Youth Mentoring
            </h3>
            <p className="text-sm text-white mb-3">
              Guide and support young people in their educational journey.
            </p>
            <div className="flex gap-2">
              <PxButton variant="secondary" size="sm">
                Learn More
              </PxButton>
              <PxButton variant="success" size="sm">
                Apply
              </PxButton>
            </div>
          </PxCard>

          <PxCard variant="default">
            <h3 className="text-lg font-pixel text-sunBurst mb-2">
              Senior Care Visits
            </h3>
            <p className="text-sm text-white mb-3">
              Spend time with elderly residents at local care facilities.
            </p>
            <div className="flex gap-2">
              <PxButton variant="secondary" size="sm">
                Learn More
              </PxButton>
              <PxButton variant="success" size="sm">
                Apply
              </PxButton>
            </div>
          </PxCard>
        </div>
      </div>
    </main>
  );
}