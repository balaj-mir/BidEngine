'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { 
  ArrowLeft, 
  Search, 
  CheckCircle, 
  XCircle, 
  AlertCircle, 
  Loader2, 
  TrendingUp, 
  Award, 
  Briefcase,
  ChevronRight,
  Database,
  ThumbsUp,
  ThumbsDown,
  Info,
  Edit3
} from 'lucide-react';
import toast from 'react-hot-toast';
import { apiService } from '../../../../lib/api';
import { CapabilityMatch, Requirement } from '../../../../lib/types';

export default function MatchViewerPage() {
  const params = useParams();
  const router = useRouter();
  const workspaceId = params.id as string;

  const [matches, setMatches] = useState<CapabilityMatch[]>([]);
  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedMatch, setSelectedMatch] = useState<CapabilityMatch | null>(null);
  const [search, setSearch] = useState('');
  const [overrideCapId, setOverrideCapId] = useState('');
  const [showOverride, setShowOverride] = useState(false);

  useEffect(() => {
    fetchData();
  }, [workspaceId]);

  const fetchData = async () => {
    try {
      const [matchesData, reqsData] = await Promise.all([
        apiService.listMatches(workspaceId),
        apiService.listRequirements(workspaceId)
      ]);
      setMatches(matchesData);
      setRequirements(reqsData);
      if (matchesData.length > 0) {
        setSelectedMatch(matchesData[0]);
      }
    } catch (err) {
      toast.error('Failed to load RAG matches');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (matchId: string, approve: boolean) => {
    try {
      await apiService.approveMatch(workspaceId, matchId, approve);
      toast.success(approve ? 'Match approved!' : 'Match rejected');
      
      // Update state
      const updated = matches.map(m => m._id === matchId ? { ...m, is_approved: approve } : m);
      setMatches(updated);
      if (selectedMatch?._id === matchId) {
        setSelectedMatch({ ...selectedMatch, is_approved: approve });
      }
    } catch (err) {
      toast.error('Failed to update approval status');
    }
  };

  const handleOverride = async () => {
    if (!overrideCapId || !selectedMatch) return;
    try {
      await apiService.overrideMatch(workspaceId, selectedMatch._id, overrideCapId);
      toast.success('Capability overridden successfully');
      setShowOverride(false);
      setOverrideCapId('');
      fetchData(); // reload matches
    } catch (err) {
      toast.error('Failed to override capability');
    }
  };

  // Helper to find matching requirement text
  const getRequirementText = (reqId: string) => {
    return requirements.find(r => r._id === reqId)?.requirement_text || 'Unknown requirement clause';
  };

  // Filter list
  const filteredMatches = matches.filter(m => {
    const reqText = getRequirementText(m.requirement_id);
    const capTitle = m.capability_detail?.title || '';
    const capDesc = m.capability_detail?.description || '';
    
    return reqText.toLowerCase().includes(search.toLowerCase()) || 
           capTitle.toLowerCase().includes(search.toLowerCase()) ||
           capDesc.toLowerCase().includes(search.toLowerCase());
  });

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          href={`/workspace/${workspaceId}`}
          className="p-2.5 bg-[#0e0e16] hover:bg-[#13131f] border border-[#1a1a28] text-gray-400 hover:text-white rounded-xl transition-all"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">RAG Library Matches</h1>
          <p className="text-gray-400 text-sm mt-1">Audit mappings of requirements to the capability library.</p>
        </div>
      </div>

      {loading ? (
        <div className="py-32 flex flex-col items-center justify-center gap-3">
          <Loader2 className="w-8 h-8 text-violet-500 animate-spin" />
          <p className="text-gray-400">Loading RAG matcher...</p>
        </div>
      ) : matches.length === 0 ? (
        <div className="bg-[#0c0c12] border border-[#1a1a24] p-16 text-center rounded-2xl space-y-4">
          <AlertCircle className="w-12 h-12 text-gray-500 mx-auto" />
          <div>
            <h3 className="text-white font-semibold">No Matches Extracted</h3>
            <p className="text-gray-500 text-sm mt-1">Ensure the ingestion pipeline successfully processed the document.</p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left Panel: Matches List (4 cols) */}
          <div className="lg:col-span-5 bg-[#0c0c12] border border-[#1a1a24] rounded-2xl flex flex-col h-[650px] shadow-2xl">
            {/* Search */}
            <div className="p-4 border-b border-[#1a1a24]">
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-500">
                  <Search className="w-4 h-4" />
                </div>
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search matches or requirements..."
                  className="w-full pl-9 pr-4 py-2.5 bg-black/40 border border-[#222230] hover:border-zinc-700 focus:border-violet-500 rounded-xl text-white placeholder-gray-500 focus:outline-none transition-all duration-300 shadow-inner text-sm"
                />
              </div>
            </div>

            {/* List */}
            <div className="flex-1 overflow-y-auto divide-y divide-[#1a1a24] scrollbar-thin scrollbar-thumb-zinc-800">
              {filteredMatches.map((m) => {
                const reqText = getRequirementText(m.requirement_id);
                const isSelected = selectedMatch?._id === m._id;

                return (
                  <div
                    key={m._id}
                    onClick={() => setSelectedMatch(m)}
                    className={`p-4 cursor-pointer transition-all duration-150 flex items-start gap-3 border-l-2 ${
                      isSelected 
                        ? 'bg-violet-600/5 border-violet-500 text-white' 
                        : 'border-transparent text-gray-300 hover:bg-white/2'
                    }`}
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-xs text-gray-500 font-semibold uppercase tracking-wider">
                        REQ ID: {m.requirement_id.substring(m.requirement_id.length - 6)}
                      </p>
                      <p className="text-sm font-semibold truncate text-white mt-1">
                        {m.capability_detail?.title || 'Unknown Capability Record'}
                      </p>
                      <p className="text-xs text-gray-400 line-clamp-2 mt-1 leading-relaxed">
                        {reqText}
                      </p>
                    </div>

                    <div className="flex-shrink-0 pt-0.5">
                      {m.is_approved === true ? (
                        <CheckCircle className="w-4 h-4 text-emerald-400" />
                      ) : m.is_approved === false ? (
                        <XCircle className="w-4 h-4 text-red-400" />
                      ) : (
                        <div className="w-4 h-4 rounded-full border border-gray-600 bg-transparent" />
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right Panel: Match Details (7 cols) */}
          <div className="lg:col-span-7 space-y-6">
            {selectedMatch && (
              <>
                {/* Clause & Match Card */}
                <div className="bg-[#0c0c12] border border-[#1a1a24] p-6 rounded-2xl space-y-4 shadow-xl">
                  <div>
                    <span className="text-[10px] font-bold text-violet-400 uppercase tracking-widest bg-violet-500/10 border border-violet-500/20 px-2.5 py-1 rounded">
                      RFP Clause Checked
                    </span>
                    <h3 className="text-base text-white leading-relaxed mt-3">
                      "{getRequirementText(selectedMatch.requirement_id)}"
                    </h3>
                  </div>

                  <div className="border-t border-[#1a1a24] pt-4">
                    <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-widest bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 rounded">
                      Matched Capability Library Item
                    </span>
                    
                    {selectedMatch.capability_detail ? (
                      <div className="mt-4 space-y-3">
                        <h4 className="font-bold text-lg text-white">
                          {selectedMatch.capability_detail.title}
                        </h4>
                        <p className="text-sm text-gray-400 leading-relaxed">
                          {selectedMatch.capability_detail.description}
                        </p>
                        
                        {/* Capability specs */}
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-3 text-xs">
                          <div className="bg-[#12121b] p-3 rounded-xl border border-[#1d1d2b]">
                            <span className="text-gray-500 block">Sector</span>
                            <span className="font-semibold text-white mt-1 block">{selectedMatch.capability_detail.sector}</span>
                          </div>
                          <div className="bg-[#12121b] p-3 rounded-xl border border-[#1d1d2b]">
                            <span className="text-gray-500 block">Contract Value</span>
                            <span className="font-semibold text-white mt-1 block">
                              {(selectedMatch.capability_detail.contract_value / 1000000).toFixed(0)}M {selectedMatch.capability_detail.currency}
                            </span>
                          </div>
                          <div className="bg-[#12121b] p-3 rounded-xl border border-[#1d1d2b]">
                            <span className="text-gray-500 block">Year Completed</span>
                            <span className="font-semibold text-white mt-1 block">{selectedMatch.capability_detail.year_completed}</span>
                          </div>
                          <div className="bg-[#12121b] p-3 rounded-xl border border-[#1d1d2b]">
                            <span className="text-gray-500 block">Certifications</span>
                            <span className="font-semibold text-white mt-1 block truncate">
                              {selectedMatch.capability_detail.certifications.join(', ') || 'None'}
                            </span>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <p className="text-gray-500 text-sm mt-3">No detail record linked.</p>
                    )}
                  </div>
                </div>

                {/* Similarity Scores (KPI list) */}
                <div className="bg-[#0c0c12] border border-[#1a1a24] p-6 rounded-2xl space-y-4 shadow-xl">
                  <h4 className="font-bold text-sm text-white flex items-center gap-2">
                    <TrendingUp className="w-4.5 h-4.5 text-violet-400" />
                    <span>Hybrid Similarity Calibration Scores</span>
                  </h4>
                  
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                    <div className="bg-black/40 p-4 rounded-xl border border-[#1d1d2b] text-center">
                      <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider block">BM25 Term Match</span>
                      <span className="text-lg font-bold text-white mt-1.5 block">
                        {selectedMatch.bm25_score.toFixed(3)}
                      </span>
                    </div>

                    <div className="bg-black/40 p-4 rounded-xl border border-[#1d1d2b] text-center">
                      <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider block">Semantic Cosine</span>
                      <span className="text-lg font-bold text-white mt-1.5 block">
                        {selectedMatch.semantic_score.toFixed(3)}
                      </span>
                    </div>

                    <div className="bg-black/40 p-4 rounded-xl border border-[#1d1d2b] text-center">
                      <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider block">Rerank Score</span>
                      <span className="text-lg font-bold text-white mt-1.5 block font-mono">
                        {selectedMatch.rerank_score.toFixed(2)}
                      </span>
                    </div>

                    <div className="bg-gradient-to-tr from-violet-600/10 to-indigo-600/5 p-4 rounded-xl border border-violet-500/20 text-center shadow-md">
                      <span className="text-[10px] text-violet-400 font-bold uppercase tracking-wider block">Reciprocal Fusion</span>
                      <span className="text-lg font-black text-violet-300 mt-1.5 block">
                        {selectedMatch.final_score.toFixed(3)}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Evidence Panel & Actions */}
                <div className="bg-[#0c0c12] border border-[#1a1a24] p-6 rounded-2xl space-y-4 shadow-xl">
                  <h4 className="font-bold text-sm text-white flex items-center gap-2">
                    <Info className="w-4.5 h-4.5 text-indigo-400" />
                    <span>Match Justification Evidence</span>
                  </h4>
                  <div className="p-4 bg-[#12121b] border border-[#1d1d2b] rounded-xl text-sm text-gray-300 leading-relaxed font-mono">
                    {selectedMatch.match_evidence}
                  </div>

                  <div className="flex justify-between items-center pt-4 border-t border-[#1a1a24]">
                    <div>
                      <button 
                        onClick={() => setShowOverride(!showOverride)}
                        className="text-xs text-gray-500 hover:text-violet-400 flex items-center gap-1 transition-colors"
                      >
                        <Edit3 className="w-3 h-3" />
                        <span>Manual Override</span>
                      </button>
                    </div>

                    <div className="flex justify-end gap-3">
                      <button
                        onClick={() => handleApprove(selectedMatch._id, false)}
                        className={`flex items-center gap-2 px-5 py-2.5 text-sm font-semibold rounded-xl border transition-all duration-300 ${
                          selectedMatch.is_approved === false
                            ? 'bg-red-500/10 border-red-500 text-red-400'
                            : 'bg-black/40 border-[#222230] text-gray-400 hover:text-white hover:bg-white/5'
                        }`}
                      >
                        <ThumbsDown className="w-4 h-4" />
                        <span>Reject Match</span>
                      </button>
                      
                      <button
                        onClick={() => handleApprove(selectedMatch._id, true)}
                        className={`flex items-center gap-2 px-5 py-2.5 text-sm font-semibold rounded-xl border transition-all duration-300 shadow-md ${
                          selectedMatch.is_approved === true
                            ? 'bg-emerald-500/10 border-emerald-500 text-emerald-400 shadow-emerald-500/5'
                            : 'bg-gradient-to-r from-violet-600 to-indigo-600 text-white border-transparent hover:from-violet-500 hover:to-indigo-500 active:scale-95'
                        }`}
                      >
                        <ThumbsUp className="w-4 h-4" />
                        <span>Approve Match</span>
                      </button>
                    </div>
                  </div>
                  
                  {showOverride && (
                    <div className="p-4 bg-black/40 border border-[#222230] rounded-xl flex items-center gap-3 mt-4">
                      <input 
                        type="text" 
                        value={overrideCapId}
                        onChange={(e) => setOverrideCapId(e.target.value)}
                        placeholder="Paste new Capability ID (from DB)..."
                        className="flex-1 bg-[#12121b] border border-[#222230] text-sm text-white rounded-lg px-3 py-2 focus:border-violet-500 focus:outline-none"
                      />
                      <button 
                        onClick={handleOverride}
                        className="px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white text-sm font-semibold rounded-lg"
                      >
                        Swap
                      </button>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
