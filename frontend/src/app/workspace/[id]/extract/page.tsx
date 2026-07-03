'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { 
  ArrowLeft, 
  Search, 
  Filter, 
  Loader2, 
  AlertCircle, 
  Calendar, 
  SlidersHorizontal,
  Bookmark,
  Layers,
  Sparkles,
  Trash2,
  Edit2
} from 'lucide-react';
import toast from 'react-hot-toast';
import { apiService } from '../../../../lib/api';
import { Requirement } from '../../../../lib/types';
import { format } from 'date-fns';

export default function RequirementsPage() {
  const params = useParams();
  const router = useRouter();
  const workspaceId = params.id as string;

  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [mandatoryFilter, setMandatoryFilter] = useState<string>('all');
  const [clusterFilter, setClusterFilter] = useState<string>('all');

  useEffect(() => {
    fetchRequirements();
  }, [workspaceId]);

  const fetchRequirements = async () => {
    try {
      const data = await apiService.listRequirements(workspaceId);
      setRequirements(data);
    } catch (err) {
      toast.error('Failed to load requirements');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (reqId: string) => {
    if (!confirm('Are you sure you want to delete this requirement?')) return;
    try {
      await apiService.deleteRequirement(workspaceId, reqId);
      setRequirements(requirements.filter(r => r._id !== reqId));
      toast.success('Requirement deleted');
    } catch (err) {
      toast.error('Failed to delete requirement');
    }
  };

  // Extract list of all unique categories & clusters
  const categories = Array.from(new Set(requirements.map(r => r.category)));
  const clusters = Array.from(new Set(requirements.map(r => r.cluster_id).filter(c => c !== undefined && c !== null)));

  // Filter requirements
  const filteredReqs = requirements.filter(r => {
    const matchesSearch = r.requirement_text.toLowerCase().includes(search.toLowerCase()) || 
                          (r.section && r.section.toLowerCase().includes(search.toLowerCase()));
    const matchesCategory = categoryFilter === 'all' || r.category === categoryFilter;
    const matchesMandatory = mandatoryFilter === 'all' || 
                             (mandatoryFilter === 'mandatory' && r.is_mandatory) || 
                             (mandatoryFilter === 'optional' && !r.is_mandatory);
    const matchesCluster = clusterFilter === 'all' || r.cluster_id?.toString() === clusterFilter;

    return matchesSearch && matchesCategory && matchesMandatory && matchesCluster;
  });

  const mandatoryCount = requirements.filter(r => r.is_mandatory).length;
  const deadlineCount = requirements.filter(r => r.deadline_date).length;

  return (
    <div className="space-y-8">
      {/* Upper navigation header */}
      <div className="flex items-center gap-4">
        <Link
          href={`/workspace/${workspaceId}`}
          className="p-2.5 bg-[#0e0e16] hover:bg-[#13131f] border border-[#1a1a28] text-gray-400 hover:text-white rounded-xl transition-all"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Requirements Ingestion</h1>
          <p className="text-gray-400 text-sm mt-1">Review extracted clauses and cluster groups.</p>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-[#0c0c12] border border-[#1a1a24] p-5 rounded-xl text-center">
          <span className="text-gray-500 text-xs font-semibold uppercase tracking-wider">Total Requirements</span>
          <h3 className="text-2xl font-bold text-white mt-1">{requirements.length}</h3>
        </div>
        <div className="bg-[#0c0c12] border border-[#1a1a24] p-5 rounded-xl text-center">
          <span className="text-amber-400 text-xs font-semibold uppercase tracking-wider">Mandatory Clauses</span>
          <h3 className="text-2xl font-bold text-amber-400 mt-1">{mandatoryCount}</h3>
        </div>
        <div className="bg-[#0c0c12] border border-[#1a1a24] p-5 rounded-xl text-center">
          <span className="text-blue-400 text-xs font-semibold uppercase tracking-wider">With Deadlines</span>
          <h3 className="text-2xl font-bold text-blue-400 mt-1">{deadlineCount}</h3>
        </div>
        <div className="bg-[#0c0c12] border border-[#1a1a24] p-5 rounded-xl text-center">
          <span className="text-violet-400 text-xs font-semibold uppercase tracking-wider">KMeans Clusters</span>
          <h3 className="text-2xl font-bold text-violet-400 mt-1">{clusters.length} Groups</h3>
        </div>
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
            placeholder="Search requirement content..."
            className="w-full pl-11 pr-4 py-2.5 bg-black/40 border border-[#222230] hover:border-zinc-700 focus:border-violet-500 rounded-xl text-white placeholder-gray-500 focus:outline-none transition-all duration-300 shadow-inner text-sm"
          />
        </div>

        {/* Filter dropdowns */}
        <div className="flex flex-wrap gap-3 w-full md:w-auto justify-end">
          {/* Category Dropdown */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-500" />
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="bg-[#12121b] border border-[#222230] text-gray-300 text-sm rounded-xl px-3.5 py-2.5 focus:border-violet-500 focus:outline-none"
            >
              <option value="all">All Categories</option>
              {categories.map(cat => (
                <option key={cat} value={cat}>{cat.toUpperCase()}</option>
              ))}
            </select>
          </div>

          {/* Mandatory Dropdown */}
          <select
            value={mandatoryFilter}
            onChange={(e) => setMandatoryFilter(e.target.value)}
            className="bg-[#12121b] border border-[#222230] text-gray-300 text-sm rounded-xl px-3.5 py-2.5 focus:border-violet-500 focus:outline-none"
          >
            <option value="all">All Priority</option>
            <option value="mandatory">Mandatory Only</option>
            <option value="optional">Optional Only</option>
          </select>

          {/* Cluster Dropdown */}
          <select
            value={clusterFilter}
            onChange={(e) => setClusterFilter(e.target.value)}
            className="bg-[#12121b] border border-[#222230] text-gray-300 text-sm rounded-xl px-3.5 py-2.5 focus:border-violet-500 focus:outline-none"
          >
            <option value="all">All Clusters</option>
            {clusters.sort().map(c => (
              <option key={c} value={c.toString()}>Cluster {c}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Main Checklist panel */}
      <div className="bg-[#0c0c12] border border-[#1a1a24] rounded-2xl overflow-hidden shadow-2xl">
        {loading ? (
          <div className="py-24 flex flex-col items-center justify-center gap-3">
            <Loader2 className="w-8 h-8 text-violet-500 animate-spin" />
            <p className="text-gray-400 text-sm">Fetching requirements checklist...</p>
          </div>
        ) : filteredReqs.length === 0 ? (
          <div className="py-24 text-center space-y-4">
            <AlertCircle className="w-12 h-12 text-gray-500 mx-auto" />
            <div>
              <h3 className="text-white font-semibold">No Matching Requirements</h3>
              <p className="text-gray-500 text-sm mt-1">Try resetting your filters or modifying search criteria.</p>
            </div>
          </div>
        ) : (
          <div className="divide-y divide-[#1a1a24]">
            {filteredReqs.map((req) => (
              <div 
                key={req._id}
                className="group p-6 hover:bg-white/2 cursor-pointer transition-colors duration-150 flex flex-col md:flex-row justify-between gap-4 items-start md:items-center"
              >
                <div className="flex-1 space-y-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-[11px] font-bold px-2 py-0.5 bg-[#171725] text-gray-400 border border-[#262638] rounded">
                      {req.section}
                    </span>
                    <span className={`text-[11px] font-bold px-2 py-0.5 rounded ${
                      req.is_mandatory 
                        ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' 
                        : 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                    }`}>
                      {req.is_mandatory ? 'MANDATORY' : 'OPTIONAL'}
                    </span>
                    <span className="text-[11px] font-bold px-2 py-0.5 bg-violet-500/10 text-violet-400 border border-violet-500/20 rounded">
                      Category: {req.category.toUpperCase()}
                    </span>
                    {req.cluster_id !== undefined && (
                      <span className="text-[11px] font-bold px-2 py-0.5 bg-[#121b1b] text-teal-400 border border-teal-500/20 rounded flex items-center gap-1">
                        <Layers className="w-3 h-3" />
                        <span>Cluster {req.cluster_id}</span>
                      </span>
                    )}
                    {req.source_page && (
                      <span className="text-[11px] font-semibold text-gray-500">
                        Page {req.source_page}
                      </span>
                    )}
                  </div>
                  <p className="text-white text-sm leading-relaxed max-w-4xl">
                    {req.requirement_text}
                  </p>
                </div>

                {/* Right actions/indicators */}
                <div className="flex flex-col items-end gap-2 flex-shrink-0">
                  {req.deadline_date && (
                    <div className="flex items-center gap-2 text-xs text-blue-400 bg-blue-500/10 border border-blue-500/20 px-3.5 py-2 rounded-xl">
                      <Calendar className="w-4 h-4" />
                      <span className="font-semibold">{req.deadline_date}</span>
                    </div>
                  )}
                  
                  <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button 
                      className="p-1.5 text-gray-400 hover:text-white hover:bg-white/10 rounded transition-colors"
                      title="Edit (Coming soon)"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button 
                      onClick={(e) => { e.stopPropagation(); handleDelete(req._id); }}
                      className="p-1.5 text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded transition-colors"
                      title="Delete requirement"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
