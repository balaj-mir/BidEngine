'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { 
  LayoutDashboard, 
  BookOpen, 
  BarChart3, 
  LogOut, 
  FileCheck2, 
  Database,
  User as UserIcon,
  ChevronRight
} from 'lucide-react';
import { useAuthStore } from '../lib/api';

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  const navItems = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Capability Library', href: '/capability-library', icon: BookOpen },
    { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  ];

  // If on login/register pages, do not render sidebar
  if (pathname === '/login' || pathname === '/register' || pathname === '/') {
    return null;
  }

  return (
    <aside className="w-64 bg-[#0a0a0a] border-r border-[#1a1a1a] flex flex-col h-screen fixed left-0 top-0 text-white z-20">
      {/* Brand Logo */}
      <div className="p-6 border-b border-[#1a1a1a] flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-violet-600 to-indigo-600 flex items-center justify-center font-bold text-white shadow-md shadow-violet-500/20">
          BE
        </div>
        <div>
          <h1 className="font-bold text-lg leading-none bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
            BidEngine AI
          </h1>
          <span className="text-[10px] text-gray-500 font-medium uppercase tracking-wider">
            Enterprise v1.0
          </span>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-4 py-6 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname.startsWith(item.href);
          const Icon = item.icon;

          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center justify-between px-4 py-3 rounded-xl transition-all duration-300 group ${
                isActive
                  ? 'bg-gradient-to-r from-violet-600/10 to-indigo-600/5 border border-violet-500/20 text-white font-medium shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)]'
                  : 'text-gray-400 hover:text-white hover:bg-white/5 border border-transparent'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon className={`w-5 h-5 transition-transform duration-300 group-hover:scale-110 ${
                  isActive ? 'text-violet-400' : 'text-gray-400 group-hover:text-white'
                }`} />
                <span>{item.name}</span>
              </div>
              {isActive && <div className="w-1.5 h-1.5 rounded-full bg-violet-400 shadow-[0_0_8px_#8b5cf6]" />}
            </Link>
          );
        })}
      </nav>

      {/* User Profile & Logout */}
      <div className="p-4 border-t border-[#1a1a1a] bg-black/40">
        <div className="flex items-center gap-3 px-2 py-3 mb-2">
          <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-indigo-500 to-violet-500 flex items-center justify-center font-bold text-white shadow-inner">
            {user?.name ? user.name[0].toUpperCase() : 'U'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-white truncate leading-none">
              {user?.name || 'Demo User'}
            </p>
            <p className="text-xs text-gray-500 truncate mt-1">
              {user?.email || 'demo@bidengine.ai'}
            </p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-xl transition-all duration-300 border border-transparent hover:border-red-500/10"
        >
          <LogOut className="w-4.5 h-4.5" />
          <span>Log Out</span>
        </button>
      </div>
    </aside>
  );
}
