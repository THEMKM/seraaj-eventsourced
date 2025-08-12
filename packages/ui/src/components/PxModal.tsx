'use client';

import React, { useEffect } from 'react';
import { clsx } from 'clsx';
import { PxButton } from './PxButton';

export interface PxModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}

export function PxModal({
  isOpen,
  onClose,
  title,
  children,
  size = 'md',
  className
}: PxModalProps) {
  // Handle escape key
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-ink/80 backdrop-blur-sm animate-pxFadeIn"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div 
        className={clsx(
          'relative clip-px border-px border-electric-teal bg-deep-indigo p-6 animate-pxFadeIn',
          'shadow-px-glow max-h-[90vh] overflow-y-auto',
          {
            'w-full max-w-sm': size === 'sm',
            'w-full max-w-md': size === 'md', 
            'w-full max-w-2xl': size === 'lg',
            'w-full max-w-4xl': size === 'xl',
          },
          className
        )}
      >
        {/* Header */}
        {title && (
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-pixel text-primary">{title}</h2>
            <PxButton
              variant="secondary"
              size="sm"
              onClick={onClose}
            >
              ✕
            </PxButton>
          </div>
        )}
        
        {/* Content */}
        <div className="text-white">
          {children}
        </div>
      </div>
    </div>
  );
}