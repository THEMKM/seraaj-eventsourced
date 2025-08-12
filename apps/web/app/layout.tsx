import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { AuthProvider } from '@/contexts/AuthContext';
import { ToastProvider } from '@/contexts/ToastContext';
import { OpportunitiesProvider } from '@/contexts/OpportunitiesContext';

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
        <AuthProvider>
          <ToastProvider>
            <OpportunitiesProvider>
              {children}
            </OpportunitiesProvider>
          </ToastProvider>
        </AuthProvider>
      </body>
    </html>
  );
}