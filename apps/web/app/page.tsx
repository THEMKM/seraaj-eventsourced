'use client';

import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { Header } from '@/components/navigation/Header';
import { HeroSearch } from '@/components/landing/HeroSearch';
import { PxButton, PxCard } from '@seraaj/ui';

export default function Home() {
  const { isAuthenticated, user } = useAuth();

  return (
    <div className="min-h-screen bg-gradient-to-br from-deepIndigo to-ink">
      <Header />
      
      <main className="max-w-4xl mx-auto p-6">
        {/* Hero Section */}
        <div className="text-center mb-12 pt-12">
          <h1 className="text-6xl font-pixel text-primary dark:text-neon-cyan mb-2 animate-px-glow">
            SERAAJ
          </h1>
          <div className="text-2xl font-pixel text-pixel-coral dark:text-neon-pink mb-4">
            🎆 8-BIT VOLUNTEERING 🎆
          </div>
          <p className="text-lg text-white mb-8 max-w-2xl mx-auto">
            Connect volunteers with meaningful opportunities across the MENA region. 
            Level up your community impact!
          </p>
          
          {isAuthenticated ? (
            <div className="space-y-4">
              <p className="text-primary font-pixel animate-px-fade-in">
                🎉 WELCOME BACK, {user?.name?.toUpperCase()}! 🎉
              </p>
              <Link href="/dashboard">
                <PxButton size="lg" className="hover:shadow-px-glow">
                  🏆 DASHBOARD
                </PxButton>
              </Link>
            </div>
          ) : (
            <Link href="/auth?mode=register">
              <PxButton size="lg" className="hover:shadow-px-glow">
                ✨ START QUEST
              </PxButton>
            </Link>
          )}
        </div>

        {/* Enhanced Hero Search */}
        <div className="mb-12">
          <HeroSearch />
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-3 gap-6">
          <PxCard variant="default" className="transform hover:scale-105 transition-transform duration-300">
            <div className="text-2xl mb-2">🎆</div>
            <h3 className="text-lg font-pixel text-primary mb-2">FOR VOLUNTEERS</h3>
            <p className="text-sm text-ink dark:text-gray-300 mb-4">
              Level up by finding quests that match your superpowers!
            </p>
            {isAuthenticated ? (
              <Link href="/dashboard">
                <PxButton variant="secondary" size="sm">
                  📊 VIEW QUESTS
                </PxButton>
              </Link>
            ) : (
              <Link href="/auth?mode=register">
                <PxButton variant="secondary" size="sm">
                  🎆 JOIN GUILD
                </PxButton>
              </Link>
            )}
          </PxCard>

          <PxCard variant="glow" className="transform hover:scale-105 transition-transform duration-300">
            <div className="text-2xl mb-2">🏰</div>
            <h3 className="text-lg font-pixel text-sunBurst mb-2">FOR GUILDS</h3>
            <p className="text-sm text-white mb-4">
              Recruit heroes ready to tackle your most epic challenges!
            </p>
            <Link href="/auth?mode=register">
              <PxButton variant="secondary" size="sm">
                🏰 CREATE GUILD
              </PxButton>
            </Link>
          </PxCard>

          <PxCard variant="default" className="transform hover:scale-105 transition-transform duration-300">
            <div className="text-2xl mb-2">✨</div>
            <h3 className="text-lg font-pixel text-primary mb-2">QUICK MATCH</h3>
            <p className="text-sm text-ink dark:text-gray-300 mb-4">
              Let our AI find the perfect quest for your skill tree!
            </p>
            {isAuthenticated ? (
              <Link href="/dashboard">
                <PxButton variant="success" size="sm">
                  ✨ FIND QUEST
                </PxButton>
              </Link>
            ) : (
              <Link href="/auth?mode=login">
                <PxButton variant="success" size="sm">
                  🔑 LOGIN FIRST
                </PxButton>
              </Link>
            )}
          </PxCard>
        </div>
      </main>
    </div>
  );
}