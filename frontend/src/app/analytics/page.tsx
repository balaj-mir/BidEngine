'use client';

import React from 'react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  LineChart, 
  Line,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { 
  BarChart3, 
  TrendingUp, 
  Award, 
  Clock, 
  Target,
  ArrowUpRight,
  Sparkles,
  Cpu,
  DollarSign,
  Users,
  ShieldAlert
} from 'lucide-react';

const sectorPerformanceData = [
  { name: 'Public Sector / Tax', bids: 24, wins: 18, rate: 75 },
  { name: 'Cybersecurity / IT', bids: 32, wins: 22, rate: 68 },
  { name: 'Infrastructure', bids: 15, wins: 9, rate: 60 },
  { name: 'Health Tech', bids: 18, wins: 12, rate: 66 },
  { name: 'Education', bids: 11, wins: 8, rate: 72 },
];

const timelinePerformanceData = [
  { month: 'Jan', winRate: 58, avgScore: 68 },
  { month: 'Feb', winRate: 62, avgScore: 71 },
  { month: 'Mar', winRate: 60, avgScore: 69 },
  { month: 'Apr', winRate: 65, avgScore: 73 },
  { month: 'May', winRate: 69, avgScore: 76 },
  { month: 'Jun', winRate: 74, avgScore: 79 },
];

const winLossData = [
  { name: 'Won Bids', value: 69 },
  { name: 'Lost Bids', value: 31 },
];

const COLORS = ['#8b5cf6', '#ef4444'];

const competitorData = [
  { id: 1, name: 'Acme Corp', winRate: 42, pricing: 'LOW', strength: 'Aggressive pricing, quick delivery', weakness: 'Poor post-sales support' },
  { id: 2, name: 'TechSolutions Inc', winRate: 65, pricing: 'HIGH', strength: 'Premium brand, high security', weakness: 'Slow implementation' },
  { id: 3, name: 'GlobalSys Defense', winRate: 55, pricing: 'MEDIUM', strength: 'Strong government ties', weakness: 'Legacy technology stack' },
];

export default function AnalyticsPage() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white tracking-tight">Analytics</h1>
        <p className="text-gray-400 text-sm mt-1">Track proposal performance trends, win rates, and sector highlights.</p>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {/* Metric 1 */}
        <div className="bg-[#0c0c12] border border-[#1a1a24] p-6 rounded-2xl relative overflow-hidden">
          <div className="flex justify-between items-start">
            <span className="text-gray-500 text-xs font-semibold uppercase tracking-wider">Historical Win Rate</span>
            <span className="text-xs text-emerald-400 font-bold bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded flex items-center gap-0.5">
              <ArrowUpRight className="w-3 h-3" /> +5%
            </span>
          </div>
          <h3 className="text-3xl font-bold text-white mt-2">69.0%</h3>
          <p className="text-xs text-gray-500 mt-2">Based on 120 submitted bids</p>
        </div>

        {/* Metric 2 */}
        <div className="bg-[#0c0c12] border border-[#1a1a24] p-6 rounded-2xl relative overflow-hidden">
          <div className="flex justify-between items-start">
            <span className="text-gray-500 text-xs font-semibold uppercase tracking-wider">Avg Response Cycle</span>
            <span className="text-xs text-emerald-400 font-bold bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded flex items-center gap-0.5">
              <Clock className="w-3 h-3" /> -12d
            </span>
          </div>
          <h3 className="text-3xl font-bold text-white mt-2">3.2 Days</h3>
          <p className="text-xs text-gray-500 mt-2">Industry average: 14.5 Days</p>
        </div>

        {/* Metric 3 */}
        <div className="bg-[#0c0c12] border border-[#1a1a24] p-6 rounded-2xl relative overflow-hidden">
          <div className="flex justify-between items-start">
            <span className="text-gray-500 text-xs font-semibold uppercase tracking-wider">RFP Parsing Accuracy</span>
            <span className="text-xs text-violet-400 font-bold bg-violet-500/10 border border-violet-500/20 px-2 py-0.5 rounded">
              LLM + RAG
            </span>
          </div>
          <h3 className="text-3xl font-bold text-white mt-2">99.4%</h3>
          <p className="text-xs text-gray-500 mt-2">Accuracy verified on 4.2k clauses</p>
        </div>

        {/* Metric 4 */}
        <div className="bg-[#0c0c12] border border-[#1a1a24] p-6 rounded-2xl relative overflow-hidden">
          <div className="flex justify-between items-start">
            <span className="text-gray-500 text-xs font-semibold uppercase tracking-wider">Total Contract Ingested</span>
            <span className="text-xs text-white/50 bg-white/5 border border-white/10 px-2 py-0.5 rounded">
              USD
            </span>
          </div>
          <h3 className="text-3xl font-bold text-white mt-2">$24.5M</h3>
          <p className="text-xs text-gray-500 mt-2">Historical library valuation</p>
        </div>
      </div>

      {/* AI Cost & Operations Dashboard */}
      <div className="bg-gradient-to-tr from-violet-600/10 to-indigo-600/5 border border-violet-500/20 p-6 rounded-2xl shadow-xl space-y-6">
        <h4 className="font-bold text-sm text-violet-400 flex items-center gap-2">
          <Cpu className="w-4.5 h-4.5" />
          <span>GenAI Token & Cost Operations Dashboard</span>
        </h4>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-black/40 border border-violet-500/20 p-5 rounded-xl">
            <div className="flex items-center gap-2 text-gray-400 text-xs font-semibold uppercase tracking-wider mb-2">
              <Cpu className="w-4 h-4 text-violet-400" /> Total Tokens Processed
            </div>
            <h3 className="text-2xl font-bold text-white">42.8M</h3>
            <p className="text-[11px] text-gray-500 mt-1">GPT-4o & Claude 3.5 Sonnet</p>
          </div>
          
          <div className="bg-black/40 border border-violet-500/20 p-5 rounded-xl">
            <div className="flex items-center gap-2 text-gray-400 text-xs font-semibold uppercase tracking-wider mb-2">
              <DollarSign className="w-4 h-4 text-emerald-400" /> Estimated API Cost
            </div>
            <h3 className="text-2xl font-bold text-emerald-400">$142.50</h3>
            <p className="text-[11px] text-gray-500 mt-1">Across 120 generated proposals</p>
          </div>

          <div className="bg-black/40 border border-violet-500/20 p-5 rounded-xl relative overflow-hidden">
            <div className="absolute top-0 right-0 p-4 opacity-10 text-violet-500">
              <Sparkles className="w-16 h-16" />
            </div>
            <div className="flex items-center gap-2 text-gray-400 text-xs font-semibold uppercase tracking-wider mb-2 relative z-10">
              <TrendingUp className="w-4 h-4 text-amber-400" /> Estimated Human Savings
            </div>
            <h3 className="text-2xl font-bold text-amber-400 relative z-10">$84,000+</h3>
            <p className="text-[11px] text-gray-500 mt-1 relative z-10">Based on $100/hr consultant rate</p>
          </div>
        </div>
      </div>

      {/* Charts section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Win Rate Over Time Line Chart (7 cols) */}
        <div className="lg:col-span-7 bg-[#0c0c12] border border-[#1a1a24] p-6 rounded-2xl space-y-4 shadow-xl">
          <h4 className="font-bold text-sm text-white flex items-center gap-2">
            <TrendingUp className="w-4.5 h-4.5 text-violet-400" />
            <span>Monthly Win Performance & AI Score correlation</span>
          </h4>

          <div className="h-[280px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={timelinePerformanceData} margin={{ left: 10, right: 30, top: 10, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#161622" />
                <XAxis dataKey="month" stroke="#52526b" />
                <YAxis stroke="#52526b" unit="%" />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0e0e16', border: '1px solid #222230', borderRadius: '12px' }}
                  labelStyle={{ color: '#fff', fontSize: 10, fontWeight: 'bold' }}
                />
                <Line type="monotone" dataKey="winRate" stroke="#8b5cf6" strokeWidth={3} name="Actual Win Rate" activeDot={{ r: 8 }} />
                <Line type="monotone" dataKey="avgScore" stroke="#10b981" strokeWidth={2} name="Avg ML Go Score" strokeDasharray="5 5" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Win/Loss Pie chart (5 cols) */}
        <div className="lg:col-span-5 bg-[#0c0c12] border border-[#1a1a24] p-6 rounded-2xl flex flex-col justify-between min-h-[340px] shadow-xl">
          <h4 className="font-bold text-sm text-white flex items-center gap-2">
            <Target className="w-4.5 h-4.5 text-emerald-400" />
            <span>Win / Loss Distribution</span>
          </h4>

          <div className="flex-1 flex justify-center items-center h-[200px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={winLossData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {winLossData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0e0e16', border: '1px solid #222230', borderRadius: '12px' }}
                  labelStyle={{ color: '#fff', fontSize: 10, fontWeight: 'bold' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="flex justify-center gap-6 text-xs font-semibold">
            <div className="flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 rounded-full bg-violet-500" />
              <span className="text-gray-400">Wins (69.0%)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 rounded-full bg-red-500" />
              <span className="text-gray-400">Losses (31.0%)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Sector Performance Bar Chart */}
      <div className="bg-[#0c0c12] border border-[#1a1a24] p-6 rounded-2xl space-y-4 shadow-xl">
        <h4 className="font-bold text-sm text-white flex items-center gap-2">
          <BarChart3 className="w-4.5 h-4.5 text-indigo-400" />
          <span>Sector / Industry Conversion Analysis</span>
        </h4>

        <div className="h-[280px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={sectorPerformanceData} margin={{ left: 10, right: 30, top: 10, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#161622" />
              <XAxis dataKey="name" stroke="#52526b" />
              <YAxis stroke="#52526b" />
              <Tooltip 
                contentStyle={{ backgroundColor: '#0e0e16', border: '1px solid #222230', borderRadius: '12px' }}
                labelStyle={{ color: '#fff', fontSize: 10, fontWeight: 'bold' }}
              />
              <Bar dataKey="bids" fill="#3b82f6" name="Total Submissions" radius={[4, 4, 0, 0]} />
              <Bar dataKey="wins" fill="#10b981" name="Successful Wins" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Competitor Intelligence DB */}
      <div className="bg-[#0c0c12] border border-[#1a1a24] p-6 rounded-2xl space-y-4 shadow-xl">
        <h4 className="font-bold text-sm text-white flex items-center gap-2">
          <Users className="w-4.5 h-4.5 text-blue-400" />
          <span>Competitor Intelligence Database</span>
        </h4>
        <p className="text-xs text-gray-400">Track competitor behavior and positioning to improve the ML Win Scorer accuracy.</p>

        <div className="overflow-x-auto mt-4">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-gray-500 uppercase bg-[#12121b] border-y border-[#1a1a24]">
              <tr>
                <th className="px-6 py-3">Competitor Name</th>
                <th className="px-6 py-3">Win Rate</th>
                <th className="px-6 py-3">Pricing Tier</th>
                <th className="px-6 py-3">Known Strengths</th>
                <th className="px-6 py-3 text-right">Known Weaknesses</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1a1a24]">
              {competitorData.map((comp) => (
                <tr key={comp.id} className="hover:bg-white/5 transition-colors">
                  <td className="px-6 py-4 font-semibold text-white">{comp.name}</td>
                  <td className="px-6 py-4">
                    <span className="text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded text-xs font-bold border border-emerald-500/20">
                      {comp.winRate}%
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 rounded text-[10px] font-bold ${
                      comp.pricing === 'HIGH' ? 'bg-red-500/10 text-red-400 border border-red-500/20' :
                      comp.pricing === 'MEDIUM' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
                      'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                    }`}>
                      {comp.pricing}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-xs text-gray-300">{comp.strength}</td>
                  <td className="px-6 py-4 text-xs text-gray-400 text-right">{comp.weakness}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
