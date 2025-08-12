'use client';

import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { Header } from '@/components/navigation/Header';
import { PxButton, PxCard } from '@seraaj/ui';

export default function Home() {
  const { isAuthenticated, user } = useAuth();

  return (
    <div className="min-h-screen bg-gradient-to-br from-deepIndigo to-ink">
      <Header />
      
      <main className="max-w-4xl mx-auto p-6">
        <div className="text-center mb-12 pt-12">
          <h1 className="text-4xl font-pixel text-sunBurst mb-4 animate-pxGlow">
            SERAAJ
          </h1>
          <p className="text-lg text-white mb-8">
            Connect volunteers with meaningful opportunities in their communities
          </p>
          
          {isAuthenticated ? (
            <div className="space-y-4">
              <p className="text-sunBurst font-pixel">
                Welcome back, {user?.name}!
              </p>
              <Link href="/dashboard">
                <PxButton size="lg">
                  GO TO DASHBOARD
                </PxButton>
              </Link>
            </div>
          ) : (
            <Link href="/auth?mode=register">
              <PxButton size="lg">
                GET STARTED
              </PxButton>
            </Link>
          )}
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          <PxCard variant="default">
            <h3 className="text-lg font-pixel text-sunBurst mb-2">For Volunteers</h3>
            <p className="text-sm text-white mb-4">
              Find opportunities that match your skills and passions
            </p>
            {isAuthenticated ? (
              <Link href="/dashboard">
                <PxButton variant="secondary" size="sm">
                  VIEW OPPORTUNITIES
                </PxButton>
              </Link>
            ) : (
              <Link href="/auth?mode=register">
                <PxButton variant="secondary" size="sm">
                  JOIN AS VOLUNTEER
                </PxButton>
              </Link>
            )}
          </PxCard>

          <PxCard variant="glow">
            <h3 className="text-lg font-pixel text-sunBurst mb-2">For Organizations</h3>
            <p className="text-sm text-white mb-4">
              Connect with passionate volunteers ready to make a difference
            </p>
            <Link href="/auth?mode=register">
              <PxButton variant="secondary" size="sm">
                JOIN AS ORGANIZATION
              </PxButton>
            </Link>
          </PxCard>

          <PxCard variant="default">
            <h3 className="text-lg font-pixel text-sunBurst mb-2">Quick Match</h3>
            <p className="text-sm text-white mb-4">
              Get matched with opportunities tailored to you
            </p>
            {isAuthenticated ? (
              <Link href="/dashboard">
                <PxButton variant="success" size="sm">
                  FIND MY MATCH
                </PxButton>
              </Link>
            ) : (
              <Link href="/auth?mode=login">
                <PxButton variant="success" size="sm">
                  LOGIN TO MATCH
                </PxButton>
              </Link>
            )}
          </PxCard>
        </div>
      </main>
    </div>
  );
}