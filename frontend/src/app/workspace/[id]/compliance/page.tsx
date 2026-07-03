'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { 
  ArrowLeft, 
  Download, 
  CheckCircle, 
  AlertTriangle, 
  XCircle, 
  Loader2, 
  AlertCircle, 
  SlidersHorizontal,
  Bookmark,
  MessageSquare,
  Sparkles,
  HelpCircle
} from 'lucide-react';
import toast from 'react-hot-toast';
import { apiService } from '../../../../lib/api';
import { ComplianceItem } from '../../../../lib/types';

export default function ComplianceMatrixPage() {
  const params = useParams();
  const router = useRouter();
  const workspaceId = params.id as string;

  const [complianceItems, setComplianceItems] = useState<ComplianceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedItem, setSelectedItem] = useState<ComplianceItem | null>(null);
  
  // Override Form states
  const [isOverrideOpen, setIsOverrideOpen] = useState(false);
  const [overrideStatus, setOverrideStatus] = useState<string>('pass');
  const [overrideNotes, setOverrideNotes] = useState<string>('');
  const [submittingOverride, setSubmittingOverride] = useState(false);

  useEffect(() => {
    fetchCompliance();
  }, [workspaceId]);

  const fetchCompliance = async () => {
    try {
      const data = await apiService.getComplianceReport(workspaceId);
      setComplianceItems(data);
      if (data.length > 0) {
        setSelectedItem(data[0]);
      }
    } catch (err) {
      toast.error('Failed to load compliance report');
    } finally {
      setLoading(false);
    }
  };

  const openOverrideModal = (item: ComplianceItem) => {
    setSelectedItem(item);
    setOverrideStatus(item.status);
    setOverrideNotes(item.notes || '');
    setIsOverrideOpen(true);
  };

  const handleOverrideSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedItem) return;
    
    setSubmittingOverride(true);
    try {
      const updated = await apiService.overrideCompliance(
        workspaceId, 
        selectedItem._id, 
        overrideStatus, 
        overrideNotes
      );
      toast.success('Compliance audit overwritten successfully!');
      setIsOverrideOpen(false);
      
      // Update locally
      const updatedItems = complianceItems.map(item => item._id === selectedItem._id ? updated : item);
      setComplianceItems(updatedItems);
      setSelectedItem(updated);
    } catch (err) {
      toast.error('Failed to submit compliance override');
    } finally {
      setSubmittingOverride(false);
    }
  };

  // Calculations
  const total = complianceItems.length;
  const passCount = complianceItems.filter(i => i.status === 'pass').length;
  const partialCount = complianceItems.filter(i => i.status === 'partial').length;
  const failCount = complianceItems.filter(i => i.status === 'fail').length;
  
  const complianceCompleteness = total > 0 
    ? Math.round((passCount / total) * 100) 
    : 0;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div className="flex items-center gap-4">
          <Link
            href={`/workspace/${workspaceId}`}
            className="p-2.5 bg-[#0e0e16] hover:bg-[#13131f] border border-[#1a1a28] text-gray-400 hover:text-white rounded-xl transition-all"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-3xl font-bold text-white tracking-tight">Compliance Matrix</h1>
            <p className="text-gray-400 text-sm mt-1">Audit organizational compliance and gap-analysis reports.</p>
          </div>
        </div>

        <a
          href={apiService.exportComplianceUrl(workspaceId)}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 px-5 py-3 bg-[#12121b] hover:bg-[#1c1c2b] border border-[#222230] hover:border-[#33334d] text-gray-300 font-semibold rounded-xl text-sm transition-all"
        >
          <Download className="w-5 h-5" />
          <span>Export Excel Matrix</span>
        </a>
      </div>

      {/* KPI Stats counters */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        {/* Completeness */}
        <div className="bg-[#0c0c12] border border-[#1a1a24] p-5 rounded-xl text-center md:col-span-2 flex flex-col justify-center">
          <span className="text-gray-500 text-xs font-semibold uppercase tracking-wider">Compliance Completeness</span>
          <div className="flex items-center justify-center gap-3 mt-1.5">
            <h3 className="text-3xl font-extrabold text-white">{complianceCompleteness}%</h3>
            <div className="w-24 bg-[#1c1c28] h-2.5 rounded-full overflow-hidden border border-[#2c2c3e]">
              <div 
                className="h-full rounded-full bg-emerald-500" 
                style={{ width: `${complianceCompleteness}%` }}
              />
            </div>
          </div>
        </div>

        {/* PASS */}
        <div className="bg-[#0c0c12] border border-[#1a1a24] p-5 rounded-xl text-center">
          <span className="text-emerald-400 text-xs font-semibold uppercase tracking-wider block">PASS</span>
          <h3 className="text-2xl font-bold text-white mt-1">{passCount}</h3>
        </div>

        {/* PARTIAL */}
        <div className="bg-[#0c0c12] border border-[#1a1a24] p-5 rounded-xl text-center">
          <span className="text-amber-400 text-xs font-semibold uppercase tracking-wider block">PARTIAL</span>
          <h3 className="text-2xl font-bold text-white mt-1">{partialCount}</h3>
        </div>

        {/* FAIL */}
        <div className="bg-[#0c0c12] border border-[#1a1a24] p-5 rounded-xl text-center">
          <span className="text-red-400 text-xs font-semibold uppercase tracking-wider block">FAIL</span>
          <h3 className="text-2xl font-bold text-white mt-1">{failCount}</h3>
        </div>
      </div>

      {loading ? (
        <div className="py-32 flex flex-col items-center justify-center gap-3">
          <Loader2 className="w-8 h-8 text-violet-500 animate-spin" />
          <p className="text-gray-400">Loading compliance audit...</p>
        </div>
      ) : complianceItems.length === 0 ? (
        <div className="bg-[#0c0c12] p-16 text-center border border-[#1a1a24] rounded-2xl space-y-4">
          <AlertCircle className="w-12 h-12 text-gray-500 mx-auto" />
          <div>
            <h3 className="text-white font-semibold">No Compliance Items audited</h3>
            <p className="text-gray-500 text-sm mt-1">Check workspace processing log stream.</p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left Panel: Compliance List (5 cols) */}
          <div className="lg:col-span-5 bg-[#0c0c12] border border-[#1a1a24] rounded-2xl flex flex-col h-[650px] shadow-2xl">
            <div className="p-4 border-b border-[#1a1a24] bg-black/40">
              <h3 className="font-bold text-sm text-white">Clauses Checklist</h3>
            </div>
            
            <div className="flex-1 overflow-y-auto divide-y divide-[#1a1a24] scrollbar-thin scrollbar-thumb-zinc-800">
              {complianceItems.map((item) => {
                const isSelected = selectedItem?._id === item._id;
                return (
                  <div
                    key={item._id}
                    onClick={() => setSelectedItem(item)}
                    className={`p-4 cursor-pointer transition-all duration-150 flex items-start gap-3 border-l-2 ${
                      isSelected 
                        ? 'bg-violet-600/5 border-violet-500 text-white font-semibold' 
                        : 'border-transparent text-gray-400 hover:bg-white/2 hover:text-white'
                    }`}
                  >
                    <div className="flex-shrink-0 mt-0.5">
                      {item.status === 'pass' ? (
                        <CheckCircle className="w-4.5 h-4.5 text-emerald-400" />
                      ) : item.status === 'partial' ? (
                        <AlertTriangle className="w-4.5 h-4.5 text-amber-400" />
                      ) : (
                        <XCircle className="w-4.5 h-4.5 text-red-400" />
                      )}
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <p className="text-xs text-gray-500 font-mono">ID: {item.requirement_id.substring(item.requirement_id.length - 6)}</p>
                      <p className="text-sm line-clamp-2 mt-1 leading-relaxed text-gray-200">
                        {item.requirement_text || 'RFP requirement clause text.'}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right Panel: Audit Details (7 cols) */}
          <div className="lg:col-span-7 space-y-6">
            {selectedItem && (
              <>
                {/* Requirement audit detail card */}
                <div className="bg-[#0c0c12] border border-[#1a1a24] p-6 rounded-2xl space-y-5 shadow-xl">
                  <div>
                    <span className="text-[10px] font-bold text-gray-500 uppercase tracking-widest block">Clause Checked</span>
                    <p className="text-base text-white leading-relaxed mt-2 font-semibold">
                      "{selectedItem.requirement_text || 'RFP requirement clause text.'}"
                    </p>
                  </div>

                  <div className="border-t border-[#1a1a24] pt-4 grid grid-cols-2 gap-4">
                    <div>
                      <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider block">Compliance Status</span>
                      <span className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-bold border mt-2 ${
                        selectedItem.status === 'pass' 
                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' 
                          : selectedItem.status === 'partial' 
                            ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' 
                            : 'bg-red-500/10 text-red-400 border-red-500/20'
                      }`}>
                        {selectedItem.status.toUpperCase()}
                      </span>
                    </div>

                    <div>
                      <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider block">Calibrated Fit Score</span>
                      <span className="text-lg font-black text-white mt-1.5 block">
                        {Math.round(selectedItem.final_score * 100)}%
                      </span>
                    </div>
                  </div>

                  {/* AI audit reasoning */}
                  {selectedItem.ai_reasoning && (
                    <div className="bg-[#12121b] border border-[#1d1d2b] p-4 rounded-xl space-y-2">
                      <span className="text-[10px] text-violet-400 font-bold uppercase tracking-widest flex items-center gap-1">
                        <Sparkles className="w-3.5 h-3.5 animate-pulse" />
                        <span>AI Compliance Auditor Reasoning</span>
                      </span>
                      <p className="text-sm text-gray-300 leading-relaxed font-mono">
                        {selectedItem.ai_reasoning}
                      </p>
                    </div>
                  )}
                </div>

                {/* Gap & Recommendation analysis (Visible only when status !== pass) */}
                {selectedItem.status !== 'pass' && (
                  <div className="bg-[#0c0c12] border border-[#1a1a24] p-6 rounded-2xl space-y-4 shadow-xl">
                    <h4 className="font-bold text-sm text-amber-400 flex items-center gap-2">
                      <AlertTriangle className="w-4.5 h-4.5" />
                      <span>Missing Capabilities & Recommendation</span>
                    </h4>

                    {selectedItem.gap_description && (
                      <div className="p-4 bg-red-500/5 border border-red-500/20 rounded-xl space-y-1">
                        <span className="text-[10px] font-bold text-red-400 uppercase">Gap Description:</span>
                        <p className="text-xs text-gray-300 leading-relaxed">{selectedItem.gap_description}</p>
                      </div>
                    )}

                    {selectedItem.recommendation && (
                      <div className="p-4 bg-amber-500/5 border border-amber-500/20 rounded-xl space-y-1">
                        <span className="text-[10px] font-bold text-amber-400 uppercase">Recommendation:</span>
                        <p className="text-xs text-gray-300 leading-relaxed">{selectedItem.recommendation}</p>
                      </div>
                    )}
                  </div>
                )}

                {/* Audit notes and Manual Overrides */}
                <div className="bg-[#0c0c12] border border-[#1a1a24] p-6 rounded-2xl space-y-4 shadow-xl">
                  <div className="flex justify-between items-center">
                    <h4 className="font-bold text-sm text-white flex items-center gap-2">
                      <MessageSquare className="w-4.5 h-4.5 text-indigo-400" />
                      <span>Audit Notes</span>
                    </h4>
                    
                    <button
                      onClick={() => openOverrideModal(selectedItem)}
                      className="px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white text-xs font-semibold rounded-xl shadow-md active:scale-95 transition-all"
                    >
                      Audit Manual Override
                    </button>
                  </div>
                  
                  <div className="p-4 bg-[#12121b] border border-[#1d1d2b] rounded-xl text-xs text-gray-400 leading-relaxed font-mono">
                    {selectedItem.notes ? (
                      <p className="text-gray-300 font-semibold">"{selectedItem.notes}"</p>
                    ) : (
                      <p className="italic text-gray-600">No custom notes added for this matrix entry.</p>
                    )}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* Manual Override modal */}
      {isOverrideOpen && selectedItem && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-[#0e0e16] border border-[#222230] w-full max-w-md rounded-2xl shadow-2xl overflow-hidden">
            <div className="p-6 border-b border-[#1c1c2b]">
              <h3 className="font-bold text-lg text-white">Manual Override Compliance</h3>
              <p className="text-gray-500 text-xs mt-1 truncate">REQ ID: {selectedItem.requirement_id}</p>
            </div>

            <form onSubmit={handleOverrideSubmit} className="p-6 space-y-6">
              <div className="space-y-2">
                <label className="text-sm font-semibold text-gray-300 block">Override Status</label>
                <div className="grid grid-cols-3 gap-2">
                  {['pass', 'partial', 'fail'].map((st) => (
                    <button
                      key={st}
                      type="button"
                      onClick={() => setOverrideStatus(st)}
                      className={`py-2 px-3 text-xs font-bold rounded-xl border capitalize transition-all ${
                        overrideStatus === st
                          ? st === 'pass' 
                            ? 'bg-emerald-500/10 border-emerald-500 text-emerald-400' 
                            : st === 'partial'
                              ? 'bg-amber-500/10 border-amber-500 text-amber-400'
                              : 'bg-red-500/10 border-red-500 text-red-400'
                          : 'bg-black/40 border-[#222230] text-gray-400 hover:text-white hover:bg-white/5'
                      }`}
                    >
                      {st}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold text-gray-300 block">Audit Notes / Rationale</label>
                <textarea
                  required
                  value={overrideNotes}
                  onChange={(e) => setOverrideNotes(e.target.value)}
                  placeholder="Explain why the compliance matrix status was changed..."
                  className="w-full px-4 py-3 bg-black/40 border border-[#222230] focus:border-violet-500 rounded-xl text-white placeholder-gray-600 focus:outline-none transition-all duration-300 text-xs font-mono h-24"
                />
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-[#1c1c2b]">
                <button
                  type="button"
                  onClick={() => setIsOverrideOpen(false)}
                  className="px-4 py-2 bg-[#12121b] border border-[#222230] text-gray-300 hover:text-white rounded-xl text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingOverride}
                  className="px-4 py-2 bg-gradient-to-r from-violet-600 to-indigo-600 text-white rounded-xl text-xs font-semibold shadow-md flex items-center gap-1.5"
                >
                  {submittingOverride && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  <span>Save Override</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
