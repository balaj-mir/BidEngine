'use client';

import React, { useState, useEffect } from 'react';
import { 
  BookOpen, 
  Search, 
  Filter, 
  Loader2, 
  AlertCircle, 
  Briefcase, 
  Calendar, 
  DollarSign, 
  Award,
  Users,
  Clock,
  ExternalLink
} from 'lucide-react';
import toast from 'react-hot-toast';
import { apiService } from '../../lib/api';
import { CapabilityRecord } from '../../lib/types';

export default function CapabilityLibraryPage() {
  const [capabilities, setCapabilities] = useState<CapabilityRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [sectorFilter, setSectorFilter] = useState<string>('all');

  useEffect(() => {
    fetchCapabilities();
  }, []);

  const fetchCapabilities = async () => {
    try {
      const data = await apiService.listCapabilities();
      setCapabilities(data);
    } catch (err) {
      toast.error('Failed to load capability library');
    } finally {
      setLoading(false);
    }
  };

  const sectors = Array.from(new Set(capabilities.map(c => c.sector)));

  const filteredCaps = capabilities.filter(c => {
    const matchesSearch = c.title.toLowerCase().includes(search.toLowerCase()) || 
                          c.description.toLowerCase().includes(search.toLowerCase()) ||
                          c.keywords.some(k => k.toLowerCase().includes(search.toLowerCase()));
    const matchesSector = sectorFilter === 'all' || c.sector === sectorFilter;
    
    return matchesSearch && matchesSector;
  });

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white tracking-tight">Capability Library</h1>
        <p className="text-gray-400 text-sm mt-1">Audit and search reference credentials and compliance baselines.</p>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-[#0e0e16]/80 border border-[#1d1d2b] p-6 rounded-2xl flex flex-col md:flex-row gap-4 justify-between items-center backdrop-blur-md">
        {/* Search */}
        <div className="relative w-full md:w-80">
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-gray-500">
            <Search className="w-5 h-5" />
          </div>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search credentials, keywords..."
            className="w-full pl-11 pr-4 py-2.5 bg-black/40 border border-[#222230] hover:border-zinc-700 focus:border-violet-500 rounded-xl text-white placeholder-gray-500 focus:outline-none transition-all duration-300 shadow-inner text-sm"
          />
        </div>

        {/* Sector Filter */}
        <div className="flex items-center gap-2 w-full md:w-auto justify-end">
          <Filter className="w-4 h-4 text-gray-500" />
          <select
            value={sectorFilter}
            onChange={(e) => setSectorFilter(e.target.value)}
            className="bg-[#12121b] border border-[#222230] text-gray-300 text-sm rounded-xl px-3.5 py-2.5 focus:border-violet-500 focus:outline-none"
          >
            <option value="all">All Sectors</option>
            {sectors.map(sec => (
              <option key={sec} value={sec}>{sec.toUpperCase()}</option>
            ))}
          </select>
        </div>
      </div>

      {loading ? (
        <div className="py-32 flex flex-col items-center justify-center gap-3">
          <Loader2 className="w-8 h-8 text-violet-500 animate-spin" />
          <p className="text-gray-400">Loading capabilities...</p>
        </div>
      ) : filteredCaps.length === 0 ? (
        <div className="bg-[#0c0c12] p-16 border border-[#1a1a24] text-center rounded-2xl space-y-4">
          <AlertCircle className="w-12 h-12 text-gray-500 mx-auto" />
          <div>
            <h3 className="text-white font-semibold">No Credentials Found</h3>
            <p className="text-gray-500 text-sm mt-1">Try modifying your search or filter keywords.</p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredCaps.map((cap) => (
            <div 
              key={cap._id} 
              className="bg-[#0c0c12] border border-[#1a1a24] p-6 rounded-2xl flex flex-col justify-between h-[360px] hover:border-violet-500/35 transition-all duration-300 group shadow-md"
            >
              <div className="space-y-3">
                <div className="flex justify-between items-start">
                  <span className="text-[10px] text-violet-400 font-bold uppercase tracking-widest bg-violet-500/10 border border-violet-500/20 px-2.5 py-1 rounded">
                    {cap.sector}
                  </span>
                  <span className="text-[10px] text-gray-500 font-mono">ID: {cap._id}</span>
                </div>

                <h3 className="font-bold text-white text-base line-clamp-1 group-hover:text-violet-400 transition-colors">
                  {cap.title}
                </h3>
                <p className="text-gray-400 text-xs leading-relaxed line-clamp-3">
                  {cap.description}
                </p>
                
                {/* Keywords list */}
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {cap.keywords.slice(0, 4).map((word, idx) => (
                    <span 
                      key={idx}
                      className="text-[9px] text-gray-500 bg-[#12121b] border border-[#222230] px-2 py-0.5 rounded font-mono"
                    >
                      {word}
                    </span>
                  ))}
                </div>
              </div>

              {/* Spec properties details list */}
              <div className="border-t border-[#1a1a24] pt-4 mt-4 grid grid-cols-2 gap-y-3 gap-x-2 text-[11px] text-gray-400">
                <div className="flex items-center gap-1.5">
                  <DollarSign className="w-3.5 h-3.5 text-emerald-400" />
                  <span>{(cap.contract_value / 1000000).toFixed(1)}M {cap.currency}</span>
                </div>
                
                <div className="flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5 text-blue-400" />
                  <span>Completed: {cap.year_completed}</span>
                </div>

                <div className="flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5 text-amber-400" />
                  <span>Duration: {cap.duration_months} Months</span>
                </div>

                <div className="flex items-center gap-1.5">
                  <Users className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Team: {cap.team_size} Staff</span>
                </div>

                <div className="col-span-2 pt-1.5 border-t border-[#161622] flex items-center gap-1.5 text-emerald-500">
                  <Award className="w-3.5 h-3.5" />
                  <span className="font-medium truncate max-w-[200px]">
                    Outcome: {cap.outcome}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
