'use client';

import { PxButton, PxCard } from '@seraaj/ui';

export default function LoginPage() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-deepIndigo to-ink p-4 flex items-center justify-center">
      <PxCard variant="minimal" className="w-full max-w-md">
        <div className="text-center mb-6">
          <h1 className="text-2xl font-pixel text-ink mb-2">
            LOGIN
          </h1>
          <p className="text-sm text-gray-600">
            Access your volunteer dashboard
          </p>
        </div>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-ink mb-1">
              Email
            </label>
            <input 
              type="email"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-sunBurst"
              placeholder="your@email.com"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-ink mb-1">
              Password
            </label>
            <input 
              type="password"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-sunBurst"
              placeholder="••••••••"
            />
          </div>
          
          <PxButton variant="primary" className="w-full">
            Sign In
          </PxButton>
        </div>
      </PxCard>
    </main>
  );
}