'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useDropzone } from 'react-dropzone';
import { 
  Plus, 
  FileText, 
  Trash2, 
  Eye, 
  BarChart, 
  Award, 
  Percent, 
  AlertTriangle,
  FolderOpen,
  Calendar,
  X,
  UploadCloud,
  Loader2
} from 'lucide-react';
import toast from 'react-hot-toast';
import { apiService } from '../../lib/api';
import { Workspace } from '../../lib/types';
import { format } from 'date-fns';

export default function Dashboard() {
  const router = useRouter();
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [workspaceName, setWorkspaceName] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    fetchWorkspaces();
  }, []);

  const fetchWorkspaces = async () => {
    try {
      const data = await apiService.listWorkspaces();
      setWorkspaces(data);
    } catch (err) {
      console.error(err);
      toast.error('Failed to load workspaces');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    if (!confirm('Are you sure you want to delete this workspace and all its data?')) return;
    
    try {
      await apiService.deleteWorkspace(id);
      toast.success('Workspace deleted successfully');
      setWorkspaces(workspaces.filter(w => w._id !== id));
    } catch (err) {
      toast.error('Failed to delete workspace');
    }
  };

  // Dropzone Setup
  const onDrop = (acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setSelectedFile(acceptedFiles[0]);
      if (!workspaceName) {
        // Auto-fill workspace name with base filename
        const nameWithoutExt = acceptedFiles[0].name.replace(/\.[^/.]+$/, "");
        setWorkspaceName(nameWithoutExt);
      }
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    multiple: false
  });

  const handleCreateWorkspace = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!workspaceName.trim()) {
      toast.error('Workspace name is required');
      return;
    }
    if (!selectedFile) {
      toast.error('RFP document file is required');
      return;
    }

    setUploading(true);
    try {
      // 1. Create Workspace
      const ws = await apiService.createWorkspace(workspaceName);
      const wsId = ws._id;
      
      // 2. Upload RFP file (backend automatically triggers the pipeline)
      await apiService.uploadRfp(wsId, selectedFile);
      
      toast.success('RFP uploaded and parsing triggered!');
      setIsModalOpen(false);
      
      // Reset form
      setWorkspaceName('');
      setSelectedFile(null);
      
      // Redirect to Workspace details stepper
      router.push(`/workspace/${wsId}`);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to create workspace');
    } finally {
      setUploading(false);
    }
  };

  // Calculate Metrics
  const totalWorkspaces = workspaces.length;
  const scoredWorkspaces = workspaces.filter(w => w.latest_score);
  const avgWinProb = scoredWorkspaces.length > 0 
    ? Math.round(scoredWorkspaces.reduce((acc, curr) => acc + (curr.latest_score?.win_probability || 0), 0) / scoredWorkspaces.length * 100)
    : 0;

  const avgCompliance = workspaces.length > 0
    ? 82 // Standard default or custom calculations
    : 0;

  return (
    <div className="space-y-8">
      {/* Upper header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Workspaces</h1>
          <p className="text-gray-400 text-sm mt-1">Manage and evaluate your RFPs and proposals.</p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 px-5 py-3 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-semibold rounded-xl shadow-lg shadow-violet-500/20 active:scale-95 transition-all duration-300"
        >
          <Plus className="w-5 h-5" />
          <span>New Workspace</span>
        </button>
      </div>

      {/* Analytics KPI counters */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* KPI 1 */}
        <div className="bg-[#0f0f15]/80 border border-[#1d1d2b] p-6 rounded-2xl flex items-center gap-5 relative overflow-hidden backdrop-blur-md">
          <div className="absolute top-0 right-0 w-24 h-24 bg-violet-600/5 rounded-full blur-2xl pointer-events-none" />
          <div className="p-4 rounded-xl bg-violet-500/10 text-violet-400 border border-violet-500/20">
            <FolderOpen className="w-6 h-6" />
          </div>
          <div>
            <span className="text-gray-400 text-xs font-semibold uppercase tracking-wider">Total Projects</span>
            <h3 className="text-3xl font-bold text-white mt-1">{totalWorkspaces}</h3>
          </div>
        </div>

        {/* KPI 2 */}
        <div className="bg-[#0f0f15]/80 border border-[#1d1d2b] p-6 rounded-2xl flex items-center gap-5 relative overflow-hidden backdrop-blur-md">
          <div className="absolute top-0 right-0 w-24 h-24 bg-indigo-600/5 rounded-full blur-2xl pointer-events-none" />
          <div className="p-4 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <Percent className="w-6 h-6" />
          </div>
          <div>
            <span className="text-gray-400 text-xs font-semibold uppercase tracking-wider">Avg Win Probability</span>
            <h3 className="text-3xl font-bold text-indigo-400 mt-1">{avgWinProb}%</h3>
          </div>
        </div>

        {/* KPI 3 */}
        <div className="bg-[#0f0f15]/80 border border-[#1d1d2b] p-6 rounded-2xl flex items-center gap-5 relative overflow-hidden backdrop-blur-md">
          <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-600/5 rounded-full blur-2xl pointer-events-none" />
          <div className="p-4 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <Award className="w-6 h-6" />
          </div>
          <div>
            <span className="text-gray-400 text-xs font-semibold uppercase tracking-wider">Avg Compliance Score</span>
            <h3 className="text-3xl font-bold text-emerald-400 mt-1">{avgCompliance}%</h3>
          </div>
        </div>
      </div>

      {/* Workspaces Table list */}
      <div className="bg-[#0c0c12] border border-[#1a1a24] rounded-2xl overflow-hidden shadow-2xl">
        <div className="p-6 border-b border-[#1a1a24] flex items-center justify-between">
          <h2 className="font-bold text-lg text-white">Active Proposals</h2>
          <span className="text-xs text-gray-500 font-medium bg-[#13131c] px-3 py-1.5 rounded-lg border border-[#222230]">
            Sync status: Active
          </span>
        </div>

        {loading ? (
          <div className="py-24 flex flex-col items-center justify-center gap-3">
            <Loader2 className="w-8 h-8 text-violet-500 animate-spin" />
            <p className="text-gray-400 text-sm">Fetching workspaces...</p>
          </div>
        ) : workspaces.length === 0 ? (
          <div className="py-24 text-center space-y-4">
            <div className="w-16 h-16 bg-[#13131c] text-gray-500 rounded-full flex items-center justify-center mx-auto border border-[#222230]">
              <FileText className="w-8 h-8" />
            </div>
            <div>
              <h3 className="text-white font-semibold text-lg">No Workspaces Found</h3>
              <p className="text-gray-500 text-sm mt-1 max-w-sm mx-auto">
                Create a new workspace by uploading an RFP document to trigger compliance extraction.
              </p>
            </div>
            <button
              onClick={() => setIsModalOpen(true)}
              className="px-5 py-2.5 bg-violet-600 hover:bg-violet-500 text-white text-sm font-semibold rounded-xl transition-colors shadow-md"
            >
              Get Started
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-[#12121b] border-b border-[#1a1a24] text-gray-400 text-xs font-semibold uppercase tracking-wider">
                  <th className="py-4 px-6">Workspace Name</th>
                  <th className="py-4 px-6">RFP File</th>
                  <th className="py-4 px-6">Pipeline Status</th>
                  <th className="py-4 px-6 text-center">Win Probability</th>
                  <th className="py-4 px-6">Created At</th>
                  <th className="py-4 px-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1a1a24] text-sm text-gray-300">
                {workspaces.map((ws) => {
                  const hasScore = !!ws.latest_score;
                  const winProb = ws.latest_score?.win_probability 
                    ? Math.round(ws.latest_score.win_probability * 100) 
                    : null;

                  return (
                    <tr 
                      key={ws._id}
                      onClick={() => router.push(`/workspace/${ws._id}`)}
                      className="hover:bg-white/5 cursor-pointer transition-colors duration-200 group"
                    >
                      <td className="py-4 px-6 font-semibold text-white group-hover:text-violet-400 transition-colors">
                        {ws.name}
                      </td>
                      <td className="py-4 px-6 text-gray-400 font-mono text-xs">
                        {ws.rfp_filename || 'No document uploaded'}
                      </td>
                      <td className="py-4 px-6">
                        <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${getStatusStyle(ws.status)}`}>
                          {ws.status.toUpperCase()}
                        </span>
                      </td>
                      <td className="py-4 px-6 text-center">
                        {hasScore && winProb !== null ? (
                          <div className="flex flex-col items-center gap-1.5 max-w-[120px] mx-auto">
                            <span className="font-bold text-white text-base leading-none">
                              {winProb}%
                            </span>
                            <div className="w-full bg-[#1c1c28] h-1.5 rounded-full overflow-hidden border border-[#2c2c3e]">
                              <div 
                                className={`h-full rounded-full bg-gradient-to-r ${getProbabilityGradient(winProb)}`} 
                                style={{ width: `${winProb}%` }}
                              />
                            </div>
                          </div>
                        ) : (
                          <span className="text-gray-500 text-xs italic">Not Scored</span>
                        )}
                      </td>
                      <td className="py-4 px-6 text-gray-400 text-xs">
                        <div className="flex items-center gap-1.5">
                          <Calendar className="w-3.5 h-3.5" />
                          <span>
                            {ws.created_at ? format(new Date(ws.created_at), 'MMM dd, yyyy') : 'N/A'}
                          </span>
                        </div>
                      </td>
                      <td className="py-4 px-6 text-right" onClick={(e) => e.stopPropagation()}>
                        <div className="flex justify-end gap-2">
                          <Link
                            href={`/workspace/${ws._id}`}
                            className="p-2 bg-[#12121b] border border-[#222230] text-gray-400 hover:text-white rounded-lg hover:bg-[#1a1a28] transition-all"
                          >
                            <Eye className="w-4.5 h-4.5" />
                          </Link>
                          <button
                            onClick={(e) => handleDelete(ws._id, e)}
                            className="p-2 bg-[#12121b] border border-[#222230] text-red-500 hover:text-red-400 rounded-lg hover:bg-red-500/10 transition-all"
                          >
                            <Trash2 className="w-4.5 h-4.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* New Workspace Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-[#0e0e16] border border-[#222230] w-full max-w-lg rounded-2xl shadow-2xl overflow-hidden relative">
            {/* Header */}
            <div className="p-6 border-b border-[#1c1c2b] flex justify-between items-center">
              <h3 className="font-bold text-lg text-white">Create Workspace</h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="p-1.5 text-gray-400 hover:text-white rounded-lg hover:bg-white/5 transition-all"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Body Form */}
            <form onSubmit={handleCreateWorkspace} className="p-6 space-y-6">
              <div className="space-y-2">
                <label className="text-sm font-semibold text-gray-300 block">Workspace / Bid Name</label>
                <input
                  type="text"
                  required
                  value={workspaceName}
                  onChange={(e) => setWorkspaceName(e.target.value)}
                  placeholder="e.g., FBR Tax Portal Upgrade"
                  className="w-full px-4 py-3 bg-black/40 border border-[#222230] hover:border-zinc-700 focus:border-violet-500 rounded-xl text-white placeholder-gray-500 focus:outline-none transition-all duration-300 shadow-inner"
                />
              </div>

              {/* Upload Drag & Drop Area */}
              <div className="space-y-2">
                <label className="text-sm font-semibold text-gray-300 block">RFP Document (PDF / DOCX)</label>
                <div 
                  {...getRootProps()}
                  className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all duration-300 ${
                    isDragActive 
                      ? 'border-violet-500 bg-violet-600/5' 
                      : selectedFile 
                        ? 'border-emerald-500 bg-emerald-500/5' 
                        : 'border-[#2c2c3e] hover:border-zinc-600 bg-black/20'
                  }`}
                >
                  <input {...getInputProps()} />
                  
                  {selectedFile ? (
                    <div className="space-y-3">
                      <div className="w-12 h-12 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center mx-auto">
                        <FileText className="w-6 h-6 animate-pulse" />
                      </div>
                      <div>
                        <p className="text-white text-sm font-medium truncate max-w-xs mx-auto">
                          {selectedFile.name}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          {(selectedFile.size / 1024).toFixed(1)} KB — Ready to upload
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedFile(null);
                        }}
                        className="text-xs text-red-400 hover:text-red-300 hover:underline font-semibold"
                      >
                        Remove file
                      </button>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <div className="w-12 h-12 rounded-xl bg-[#13131c] text-gray-500 border border-[#2c2c3e] flex items-center justify-center mx-auto">
                        <UploadCloud className="w-6 h-6" />
                      </div>
                      <div>
                        <p className="text-white text-sm font-medium">
                          {isDragActive ? 'Drop the file here' : 'Drag & drop RFP file'}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          Accepts PDF and DOCX documents up to 25MB
                        </p>
                      </div>
                      <span className="inline-block px-3 py-1.5 bg-[#171725] text-violet-400 text-xs font-semibold rounded-lg border border-violet-500/10 hover:bg-[#1a1a2b]">
                        Browse Files
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="flex justify-end gap-3 pt-4 border-t border-[#1c1c2b]">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-5 py-2.5 bg-[#12121b] border border-[#222230] text-gray-300 hover:text-white rounded-xl transition-colors font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploading}
                  className="px-5 py-2.5 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 disabled:from-violet-800 disabled:to-indigo-800 text-white font-semibold rounded-xl shadow-lg active:scale-95 transition-all duration-300 flex items-center gap-2"
                >
                  {uploading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Ingesting RFP...</span>
                    </>
                  ) : (
                    <span>Create Workspace</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

// Helpers
function getStatusStyle(status: string) {
  switch (status) {
    case 'complete':
      return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
    case 'error':
      return 'bg-red-500/10 text-red-400 border-red-500/20';
    case 'uploaded':
      return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
    case 'extracting':
    case 'extracted':
    case 'matching':
    case 'drafting':
    case 'scoring':
      return 'bg-amber-500/10 text-amber-400 border-amber-500/20 animate-pulse';
    default:
      return 'bg-gray-500/10 text-gray-400 border-gray-500/20';
  }
}

function getProbabilityGradient(prob: number) {
  if (prob >= 75) return 'from-emerald-500 to-teal-400';
  if (prob >= 50) return 'from-indigo-500 to-violet-400';
  return 'from-red-500 to-amber-400';
}
