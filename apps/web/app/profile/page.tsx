'use client';

import { PxButton, PxCard } from '@seraaj/ui';

export default function ProfilePage() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-deepIndigo to-ink p-4">
      <div className="max-w-4xl mx-auto py-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-pixel text-sunBurst mb-4">
            PROFILE
          </h1>
          <p className="text-white mb-6">
            Manage your volunteer profile and preferences
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          <PxCard variant="minimal" className="col-span-full md:col-span-1">
            <h2 className="text-xl font-pixel text-ink mb-4">
              Personal Info
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-ink mb-1">
                  Full Name
                </label>
                <input 
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-sunBurst"
                  placeholder="John Doe"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-ink mb-1">
                  Email
                </label>
                <input 
                  type="email"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-sunBurst"
                  placeholder="john@example.com"
                />
              </div>
              <PxButton variant="primary">
                Update Profile
              </PxButton>
            </div>
          </PxCard>

          <PxCard variant="glow" className="col-span-full md:col-span-1">
            <h2 className="text-xl font-pixel text-sunBurst mb-4">
              Volunteer Stats
            </h2>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-white">Total Hours:</span>
                <span className="text-sunBurst font-pixel">127</span>
              </div>
              <div className="flex justify-between">
                <span className="text-white">Projects Completed:</span>
                <span className="text-sunBurst font-pixel">8</span>
              </div>
              <div className="flex justify-between">
                <span className="text-white">Organizations Helped:</span>
                <span className="text-sunBurst font-pixel">5</span>
              </div>
              <div className="flex justify-between">
                <span className="text-white">Community Impact:</span>
                <span className="text-pixelCoral font-pixel">HIGH</span>
              </div>
            </div>
          </PxCard>

          <PxCard variant="default" className="col-span-full">
            <h2 className="text-xl font-pixel text-sunBurst mb-4">
              Recent Activity
            </h2>
            <div className="space-y-3">
              <div className="border-l-4 border-success pl-4">
                <p className="text-white text-sm">
                  <strong>Completed:</strong> Community Garden Cleanup
                </p>
                <p className="text-gray-300 text-xs">2 days ago</p>
              </div>
              <div className="border-l-4 border-warning pl-4">
                <p className="text-white text-sm">
                  <strong>Applied:</strong> Food Bank Support
                </p>
                <p className="text-gray-300 text-xs">5 days ago</p>
              </div>
              <div className="border-l-4 border-info pl-4">
                <p className="text-white text-sm">
                  <strong>Matched:</strong> Youth Mentoring Program
                </p>
                <p className="text-gray-300 text-xs">1 week ago</p>
              </div>
            </div>
          </PxCard>
        </div>
      </div>
    </main>
  );
}