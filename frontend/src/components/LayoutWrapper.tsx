'use client';

import React, { useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import Sidebar from './Sidebar';
import { Toaster } from 'react-hot-toast';
import { useAuthStore, apiService } from '../lib/api';

export default function LayoutWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { setSession, isAuthenticated } = useAuthStore();

  const isAuthPage = pathname === '/login' || pathname === '/register' || pathname === '/';

  // Check user session on mount
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      apiService.me()
        .then((user) => {
          setSession(token, user);
          if (pathname === '/' || pathname === '/login' || pathname === '/register') {
            router.push('/dashboard');
          }
        })
        .catch(() => {
          // Token invalid or expired
          localStorage.removeItem('token');
          setSession(null, null);
          if (!isAuthPage) {
            router.push('/login');
          }
        });
    } else {
      if (!isAuthPage) {
        router.push('/login');
      }
    }
  }, [pathname, isAuthPage, setSession, router]);

  if (isAuthPage) {
    return (
      <div className="min-h-screen bg-[#070707] text-gray-100 font-sans">
        <Toaster position="top-right" toastOptions={{
          style: {
            background: '#121212',
            color: '#fff',
            border: '1px solid #1a1a1a',
          }
        }} />
        {children}
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-[#070707] text-gray-100 font-sans">
      <Toaster position="top-right" toastOptions={{
        style: {
          background: '#121212',
          color: '#fff',
          border: '1px solid #1a1a1a',
        }
      }} />
      <Sidebar />
      <main className="flex-1 pl-64 min-h-screen overflow-x-hidden">
        <div className="p-8 max-w-7xl mx-auto w-full">
          {children}
        </div>
      </main>
    </div>
  );
}
