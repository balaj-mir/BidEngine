'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { 
  ArrowLeft, 
  Download, 
  FileText, 
  Loader2, 
  AlertCircle, 
  Save, 
  History,
  CheckCircle,
  Clock,
  Sparkles,
  Info,
  Layers,
  CornerDownLeft
} from 'lucide-react';
import toast from 'react-hot-toast';
import { apiService } from '../../../../lib/api';
import { ProposalSection } from '../../../../lib/types';
import { format } from 'date-fns';

export default function DraftEditorPage() {
  const params = useParams();
  const router = useRouter();
  const workspaceId = params.id as string;

  const [sections, setSections] = useState<ProposalSection[]>([]);
  const [selectedSection, setSelectedSection] = useState<ProposalSection | null>(null);
  const [editedContent, setEditedContent] = useState('');
  const [status, setStatus] = useState<'draft' | 'reviewed' | 'approved'>('draft');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [versions, setVersions] = useState<any[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [stopping, setStopping] = useState(false);

  useEffect(() => {
    fetchSections();
  }, [workspaceId]);

  const fetchSections = async () => {
    try {
      const data = await apiService.listSections(workspaceId);
      // Sort sections by order_index
      const sorted = data.sort((a, b) => a.order_index - b.order_index);
      setSections(sorted);
      if (sorted.length > 0) {
        selectSection(sorted[0]);
      }
    } catch (err) {
      toast.error('Failed to load proposal sections');
    } finally {
      setLoading(false);
    }
  };

  const selectSection = (sec: ProposalSection) => {
    setSelectedSection(sec);
    setEditedContent(sec.user_edited_content || sec.ai_draft);
    setStatus(sec.status);
    setShowHistory(false);
  };

  const handleSave = async () => {
    if (!selectedSection) return;
    setSaving(true);
    try {
      const updated = await apiService.updateSection(workspaceId, selectedSection._id, editedContent, status);
      toast.success('Section saved successfully');
      
      // Update in local state
      const newSections = sections.map(s => s._id === selectedSection._id ? updated : s);
      setSections(newSections);
      setSelectedSection(updated);
    } catch (err) {
      toast.error('Failed to save changes');
    } finally {
      setSaving(false);
    }
  };

  const handleStatusChange = async (newStatus: 'draft' | 'reviewed' | 'approved') => {
    setStatus(newStatus);
    if (!selectedSection) return;
    try {
      const updated = await apiService.updateSectionStatus(workspaceId, selectedSection._id, newStatus);
      const newSections = sections.map(s => s._id === selectedSection._id ? updated : s);
      setSections(newSections);
      setSelectedSection(updated);
      toast.success(`Status updated to ${newStatus}`);
    } catch (err) {
      toast.error('Failed to update section status');
    }
  };

  const fetchVersions = async () => {
    if (!selectedSection) return;
    setHistoryLoading(true);
    setShowHistory(true);
    try {
      const data = await apiService.listVersions(workspaceId, selectedSection._id);
      setVersions(data);
    } catch (err) {
      toast.error('Failed to load version history');
    } finally {
      setHistoryLoading(false);
    }
  };

  const restoreVersion = (content: string) => {
    setEditedContent(content);
    toast.success('Version restored to editor (click Save to commit)');
    setShowHistory(false);
  };

  const handleStopGeneration = async () => {
    setStopping(true);
    try {
      await apiService.stopGeneration(workspaceId);
      toast.success('Stop signal sent to background workers');
    } catch (err) {
      toast.error('Failed to stop generation');
    } finally {
      setStopping(false);
    }
  };

  const handleGenerateWithAI = async () => {
    if (!selectedSection) return;
    setEditedContent('');
    setSaving(true);
    toast.success('CrewAI Agent Pipeline initialized...', { icon: '🤖' });
    
    try {
      const token = localStorage.getItem('token');
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${API_URL}/api/workspaces/${workspaceId}/draft/generate-section`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ section_title: selectedSection.section_title })
      });
      
      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) return;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.replace('data: ', ''));
              if (data.event === 'text_stream') {
                setEditedContent(prev => prev + data.text);
              } else if (data.event === 'agent_progress' || data.event === 'agent_start') {
                toast(data.message, { icon: '⚙️', style: { borderRadius: '10px', background: '#333', color: '#fff', fontSize: '12px' } });
              } else if (data.event === 'complete') {
                toast.success('Agent drafting complete!');
              }
            } catch(e) {}
          }
        }
      }
    } catch (err) {
      toast.error('Streaming connection failed');
    } finally {
      setSaving(false);
    }
  };

  // Helper to render NEEDS EVIDENCE tags in a sidebar list
  const getNeedsEvidenceFlags = (text: string) => {
    const regex = /\[NEEDS EVIDENCE:\s*([^\]]+)\]/g;
    const flags = [];
    let match;
    while ((match = regex.exec(text)) !== null) {
      flags.push(match[1]);
    }
    return flags;
  };

  const evidenceFlags = selectedSection ? getNeedsEvidenceFlags(editedContent) : [];

  return (
    <div className="space-y-8">
      {/* Header with Export triggers */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div className="flex items-center gap-4">
          <Link
            href={`/workspace/${workspaceId}`}
            className="p-2.5 bg-[#0e0e16] hover:bg-[#13131f] border border-[#1a1a28] text-gray-400 hover:text-white rounded-xl transition-all"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-3xl font-bold text-white tracking-tight">Proposal Editor</h1>
            <p className="text-gray-400 text-sm mt-1">Refine and export the CrewAI-generated drafts.</p>
          </div>
        </div>

        <div className="flex gap-3">
          <a
            href={apiService.exportProposalUrl(workspaceId, 'pdf')}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2.5 bg-[#12121b] hover:bg-[#1c1c2b] border border-[#222230] hover:border-[#33334d] text-gray-300 font-semibold rounded-xl text-sm transition-all"
          >
            <Download className="w-4 h-4 text-red-400" />
            <span>Export PDF</span>
          </a>
          <a
            href={apiService.exportProposalUrl(workspaceId, 'docx')}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-semibold rounded-xl text-sm shadow-lg shadow-violet-500/20 transition-all duration-300 active:scale-95"
          >
            <Download className="w-4 h-4" />
            <span>Export DOCX</span>
          </a>
        </div>
      </div>

      {loading ? (
        <div className="py-32 flex flex-col items-center justify-center gap-3">
          <Loader2 className="w-8 h-8 text-violet-500 animate-spin" />
          <p className="text-gray-400">Loading proposal draft sections...</p>
        </div>
      ) : sections.length === 0 ? (
        <div className="bg-[#0c0c12] p-16 text-center border border-[#1a1a24] rounded-2xl space-y-4">
          <AlertCircle className="w-12 h-12 text-gray-500 mx-auto" />
          <div>
            <h3 className="text-white font-semibold">No Sections Generated</h3>
            <p className="text-gray-500 text-sm mt-1">Make sure drafting completed successfully.</p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left Panel: Sections List (4 cols) */}
          <div className="lg:col-span-4 bg-[#0c0c12] border border-[#1a1a24] rounded-2xl flex flex-col h-[650px] shadow-2xl">
            <div className="p-4 border-b border-[#1a1a24] bg-black/40">
              <h3 className="font-bold text-sm text-white flex items-center gap-2">
                <Layers className="w-4 h-4 text-violet-400" />
                <span>Proposal Layout Outline</span>
              </h3>
            </div>
            
            <div className="flex-1 overflow-y-auto divide-y divide-[#1a1a24] scrollbar-thin scrollbar-thumb-zinc-800">
              {sections.map((sec) => {
                const isSelected = selectedSection?._id === sec._id;
                return (
                  <div
                    key={sec._id}
                    onClick={() => selectSection(sec)}
                    className={`p-4 cursor-pointer transition-all duration-150 flex justify-between items-center border-l-2 ${
                      isSelected 
                        ? 'bg-violet-600/5 border-violet-500 text-white font-semibold' 
                        : 'border-transparent text-gray-400 hover:bg-white/2 hover:text-white'
                    }`}
                  >
                    <div>
                      <p className="text-[10px] text-gray-500 font-bold uppercase">Section {sec.order_index + 1}</p>
                      <h4 className="text-sm font-semibold mt-1">{sec.section_title}</h4>
                      <p className="text-[11px] text-gray-500 mt-1">{sec.word_count} words</p>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${
                        sec.status === 'approved' 
                          ? 'bg-emerald-500 shadow-[0_0_8px_#10b981]' 
                          : sec.status === 'reviewed' 
                            ? 'bg-blue-500 shadow-[0_0_8px_#3b82f6]' 
                            : 'bg-amber-500 shadow-[0_0_8px_#f59e0b]'
                      }`} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right Panel: Editor (8 cols) */}
          <div className="lg:col-span-8 grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
            {/* Editor Text Area */}
            <div className={`${evidenceFlags.length > 0 ? 'md:col-span-8' : 'md:col-span-12'} bg-[#0c0c12] border border-[#1a1a24] rounded-2xl shadow-xl flex flex-col h-[650px] relative overflow-hidden`}>
              {/* Toolbar */}
              <div className="p-4 bg-black/40 border-b border-[#1a1a24] flex flex-wrap justify-between items-center gap-3">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-bold text-gray-400">STATUS:</span>
                  <select
                    value={status}
                    onChange={(e) => handleStatusChange(e.target.value as any)}
                    className="bg-[#12121b] border border-[#222230] text-gray-300 text-xs rounded-lg px-2.5 py-1.5 focus:border-violet-500 focus:outline-none font-semibold cursor-pointer"
                  >
                    <option value="draft">Draft (Yellow)</option>
                    <option value="reviewed">Reviewed (Blue)</option>
                    <option value="approved">Approved (Green)</option>
                  </select>
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={handleGenerateWithAI}
                    disabled={saving}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 hover:bg-indigo-500 hover:text-white rounded-lg text-xs font-semibold transition-all"
                    title="Regenerate this section using CrewAI"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>AI Rewrite</span>
                  </button>
                  <button
                    onClick={fetchVersions}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-[#12121b] border border-[#222230] text-gray-400 hover:text-white rounded-lg text-xs font-semibold transition-all"
                  >
                    <History className="w-3.5 h-3.5" />
                    <span>History</span>
                  </button>
                  <button
                    onClick={handleStopGeneration}
                    disabled={stopping}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-red-500/10 border border-red-500/30 text-red-400 hover:bg-red-500 hover:text-white rounded-lg text-xs font-semibold transition-all"
                  >
                    {stopping ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <AlertCircle className="w-3.5 h-3.5" />}
                    <span>Stop</span>
                  </button>
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="flex items-center gap-1.5 px-4 py-1.5 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white rounded-lg text-xs font-semibold shadow-md active:scale-95 transition-all duration-300"
                  >
                    {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                    <span>Save Draft</span>
                  </button>
                </div>
              </div>

              {/* Text editor body */}
              <textarea
                value={editedContent}
                onChange={(e) => setEditedContent(e.target.value)}
                className="flex-1 p-6 bg-transparent text-sm text-gray-200 font-mono focus:outline-none resize-none leading-relaxed overflow-y-auto scrollbar-thin scrollbar-thumb-zinc-800"
                placeholder="Write proposal draft here..."
              />

              {/* Version History Slide-over */}
              {showHistory && (
                <div className="absolute inset-0 bg-[#0e0e16]/95 border-l border-[#222230] flex flex-col z-30">
                  <div className="p-4 border-b border-[#222230] bg-black/60 flex justify-between items-center">
                    <h4 className="font-bold text-sm text-white flex items-center gap-2">
                      <History className="w-4 h-4 text-violet-400" />
                      <span>Version Archives</span>
                    </h4>
                    <button
                      onClick={() => setShowHistory(false)}
                      className="text-xs text-gray-500 hover:text-white hover:underline"
                    >
                      Close
                    </button>
                  </div>
                  
                  <div className="flex-1 overflow-y-auto p-4 space-y-3 scrollbar-thin scrollbar-thumb-zinc-800">
                    {historyLoading ? (
                      <div className="py-12 flex justify-center">
                        <Loader2 className="w-6 h-6 text-violet-500 animate-spin" />
                      </div>
                    ) : versions.length === 0 ? (
                      <p className="text-gray-500 text-xs italic text-center">No older versions saved.</p>
                    ) : (
                      versions.map((ver, idx) => (
                        <div 
                          key={idx}
                          className="p-3 bg-black/40 border border-[#222230] rounded-xl hover:border-violet-500/40 transition-colors flex justify-between items-start"
                        >
                          <div className="space-y-1">
                            <p className="text-xs font-semibold text-white">
                              {format(new Date(ver.timestamp), 'MMM dd, HH:mm:ss')}
                            </p>
                            <p className="text-[10px] text-gray-500">{ver.word_count} words</p>
                          </div>
                          <button
                            onClick={() => restoreVersion(ver.content)}
                            className="px-2.5 py-1 bg-violet-600/10 border border-violet-500/20 text-violet-400 hover:bg-violet-600 hover:text-white rounded text-[11px] font-semibold transition-all flex items-center gap-1"
                          >
                            <CornerDownLeft className="w-3 h-3" />
                            <span>Restore</span>
                          </button>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Sidebar of Active Gaps (Visible only when gaps exist) */}
            {evidenceFlags.length > 0 && (
              <div className="md:col-span-4 bg-[#0c0c12] border border-[#1a1a24] p-4 rounded-2xl shadow-xl space-y-4">
                <h4 className="font-bold text-xs text-amber-400 uppercase tracking-widest bg-amber-500/10 border border-amber-500/20 px-2.5 py-1.5 rounded flex items-center gap-1.5">
                  <AlertCircle className="w-4 h-4" />
                  <span>Pending Evidence Gaps</span>
                </h4>
                
                <div className="space-y-3">
                  {evidenceFlags.map((flag, idx) => (
                    <div 
                      key={idx}
                      className="p-3 bg-amber-500/5 border border-amber-500/20 rounded-xl text-xs text-gray-300 leading-relaxed font-mono"
                    >
                      <span className="font-semibold text-amber-400 block mb-1">Gap #{idx+1}:</span>
                      {flag}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
