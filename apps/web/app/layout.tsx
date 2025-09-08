import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { AuthProvider } from '@/contexts/AuthContext';
import { ToastProvider } from '@/contexts/ToastContext';
import { OpportunitiesProvider } from '@/contexts/OpportunitiesContext';
import { ErrorBoundary } from '@/components/error/ErrorBoundary';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });

export const metadata: Metadata = {
  title: 'Seraaj - Volunteer Management Platform',
  description: 'Connect volunteers with meaningful opportunities in their communities',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" dir="ltr">
      <body className={`${inter.variable} font-body`}>
        <ErrorBoundary resetOnPropsChange={true} maxRetries={3}>
          <AuthProvider>
            <ToastProvider>
              <OpportunitiesProvider>
                {children}
              </OpportunitiesProvider>
            </ToastProvider>
          </AuthProvider>
        </ErrorBoundary>
      </body>
    </html>
  );
}