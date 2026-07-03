'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Mail, Lock, Loader2, Sparkles, Award, TrendingUp, CheckCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import { api, apiService, useAuthStore } from '../../../lib/api';

export default function LoginPage() {
  const router = useRouter();
  const login = useAuthStore((state) => state.login);
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      toast.error('Please fill in all fields');
      return;
    }

    setLoading(true);
    try {
      await axiosLogin();
    } catch (err: any) {
      if (email === 'demo@bidengine.ai' && password === 'Demo@1234') {
        toast.success('Connected in offline Demo Mode!');
        login('demo_token', { id: 'demo_user_id', email: 'demo@bidengine.ai', name: 'Demo User' });
        router.push('/dashboard');
      } else {
        toast.error(err.response?.data?.detail || 'Authentication failed. Use demo credentials to test.');
      }
    } finally {
      setLoading(false);
    }
  };

  const axiosLogin = async () => {
    // Re-call standard axios
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const axios = require('axios');
    const res = await axios.post(`${API_URL}/api/auth/login`, { email, password });
    
    if (res.data && res.data.access_token) {
      toast.success(`Welcome back, ${res.data.user.name}!`);
      login(res.data.access_token, res.data.user);
      router.push('/dashboard');
    }
  };

  const useDemoCredentials = () => {
    setEmail('demo@bidengine.ai');
    setPassword('Demo@1234');
    toast.success('Loaded demo credentials!');
  };

  return (
    <div className="flex min-h-screen bg-[#070707]">
      {/* Left Marketing Panel */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-[#0c0c14] via-[#09090f] to-[#070707] border-r border-[#1a1a1a] flex-col justify-between p-12 relative overflow-hidden">
        {/* Glow Effects */}
        <div className="absolute top-[-20%] left-[-20%] w-[80%] h-[80%] rounded-full bg-violet-600/10 blur-[120px] pointer-events-none" />
        <div className="absolute bottom-[-20%] right-[-20%] w-[80%] h-[80%] rounded-full bg-indigo-600/10 blur-[120px] pointer-events-none" />

        {/* Top Header */}
        <div className="flex items-center gap-3 relative z-10">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-violet-600 to-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-violet-500/20">
            BE
          </div>
          <div>
            <h2 className="font-bold text-xl leading-none text-white">BidEngine AI</h2>
            <span className="text-xs text-violet-400 font-medium">Enterprise Proposals</span>
          </div>
        </div>

        {/* Center Feature Showcases */}
        <div className="max-w-md my-auto space-y-8 relative z-10">
          <div className="space-y-4">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-violet-500/10 text-violet-400 border border-violet-500/20">
              <Sparkles className="w-3.5 h-3.5" /> Next-Gen AI RAG Pipeline
            </span>
            <h1 className="text-4xl font-extrabold tracking-tight text-white leading-tight">
              Win More Bids with AI-Powered Proposals
            </h1>
            <p className="text-gray-400 text-base leading-relaxed">
              Ingest RFPs, audit compliance requirements, query past bid libraries, and write premium structured drafts automatically.
            </p>
          </div>

          <div className="space-y-4 pt-6 border-t border-[#1a1a1a]">
            <div className="flex items-start gap-4">
              <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 mt-0.5">
                <Award className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-semibold text-white">Compliance Matrices</h3>
                <p className="text-sm text-gray-400">Automated gap-analysis identifying missing capabilities instantly.</p>
              </div>
            </div>

            <div className="flex items-start gap-4">
              <div className="p-2 rounded-lg bg-violet-500/10 text-violet-400 border border-violet-500/20 mt-0.5">
                <TrendingUp className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-semibold text-white">Random Forest Win Scorer</h3>
                <p className="text-sm text-gray-400">ML models trained to calculate probability of winning before bidding.</p>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Credits */}
        <div className="flex justify-between items-center text-xs text-gray-500 relative z-10">
          <p>© 2026 BidEngine AI. All rights reserved.</p>
          <div className="flex gap-4">
            <span className="hover:text-white cursor-pointer transition-colors">Privacy</span>
            <span className="hover:text-white cursor-pointer transition-colors">Terms</span>
          </div>
        </div>
      </div>

      {/* Right Login Form Panel */}
      <div className="w-full lg:w-1/2 flex flex-col justify-center px-6 sm:px-12 lg:px-24 py-12 bg-[#070707]">
        <div className="mx-auto w-full max-w-md space-y-8">
          {/* Header */}
          <div className="space-y-2 text-center lg:text-left">
            <h2 className="text-3xl font-bold tracking-tight text-white">Sign In</h2>
            <p className="text-sm text-gray-400">
              Access your BidEngine workspaces and drafts.
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-300 block">Email Address</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-gray-500">
                  <Mail className="w-5 h-5" />
                </div>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@company.com"
                  className="w-full pl-11 pr-4 py-3 bg-black/40 border border-[#1a1a1a] hover:border-zinc-800 focus:border-violet-500 rounded-xl text-white placeholder-gray-500 focus:outline-none transition-all duration-300 shadow-inner"
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <label className="text-sm font-medium text-gray-300 block">Password</label>
                <span className="text-xs text-violet-400 hover:text-violet-300 cursor-pointer hover:underline">Forgot password?</span>
              </div>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-gray-500">
                  <Lock className="w-5 h-5" />
                </div>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-11 pr-4 py-3 bg-black/40 border border-[#1a1a1a] hover:border-zinc-800 focus:border-violet-500 rounded-xl text-white placeholder-gray-500 focus:outline-none transition-all duration-300 shadow-inner"
                />
              </div>
            </div>

            {/* Remember & Demo Credentials */}
            <div className="flex justify-between items-center text-sm">
              <label className="flex items-center gap-2 text-gray-400 cursor-pointer">
                <input type="checkbox" className="rounded border-zinc-800 bg-black text-violet-600 focus:ring-0 focus:ring-offset-0" />
                <span>Remember me</span>
              </label>
              <button
                type="button"
                onClick={useDemoCredentials}
                className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition-colors uppercase tracking-wider flex items-center gap-1.5 hover:underline"
              >
                <CheckCircle className="w-3.5 h-3.5" /> Use Demo credentials
              </button>
            </div>

            {/* Actions */}
            <div className="space-y-4">
              <button
                type="submit"
                disabled={loading}
                className="w-full flex items-center justify-center gap-2 py-3 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 disabled:from-violet-800 disabled:to-indigo-800 text-white font-semibold rounded-xl shadow-lg shadow-violet-500/20 active:scale-[0.98] transition-all duration-300"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span>Signing In...</span>
                  </>
                ) : (
                  <span>Sign In</span>
                )}
              </button>

              <p className="text-center text-sm text-gray-400">
                Don't have an account?{' '}
                <Link href="/register" className="font-semibold text-violet-400 hover:text-violet-300 hover:underline">
                  Sign up for free
                </Link>
              </p>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
