"use client";

import React from 'react';

export const WelcomeStep: React.FC<{ onNext?: () => void } & any> = () => {
  return (
    <div className="space-y-4 text-center">
      <div className="text-5xl">dYZ+</div>
      <p className="text-white text-sm">Welcome to Seraaj! Let’s set up your profile for great matches.</p>
      <p className="text-white/70 text-xs">You can change these settings later in your profile.</p>
    </div>
  );
};

