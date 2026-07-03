'use client';

import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { 
  FileText, 
  Terminal, 
  ArrowRight, 
  CheckCircle2, 
  AlertCircle, 
  Loader2, 
  Check, 
  Search, 
  FileCheck2, 
  BookOpen, 
  TrendingUp,
  FileSignature
} from 'lucide-react';
import toast from 'react-hot-toast';
import { apiService } from '../../../lib/api';
import { Workspace } from '../../../lib/types';
import { format } from 'date-fns';

interface LogLine {
  timestamp: string;
  stage: string;
  message: string;
  status: string;
}

export default function WorkspaceStatusPage() {
  const params = useParams();
  const router = useRouter();
  const workspaceId = params.id as string;

  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [logs, setLogs] = useState<LogLine[]>([]);
  const [pipelineStatus, setPipelineStatus] = useState<string>('uploaded');
  const [loading, setLoading] = useState(true);
  
  const terminalEndRef = useRef<HTMLDivElement>(null);

  // Stepper Stage mapping
  const stages = [
    { key: 'creation', label: 'RFP Uploaded', icon: FileText },
    { key: 'extraction', label: 'Requirements Ingestion', icon: Search },
    { key: 'matching', label: 'Hybrid RAG Search', icon: BookOpen },
    { key: 'drafting', label: 'Multi-Agent Drafting', icon: FileSignature },
    { key: 'scoring', label: 'Calibrated Win Scoring', icon: TrendingUp },
  ];

  useEffect(() => {
    fetchWorkspace();
    
    // Setup SSE connection
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const eventSource = new EventSource(`${API_URL}/api/workspaces/${workspaceId}/status/stream`);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.status) {
          setPipelineStatus(data.status);
        }
        
        // Append log line
        if (data.message) {
          setLogs((prev) => {
            // Avoid duplicates
            const isDup = prev.some(l => l.message === data.message && l.stage === data.stage);
            if (isDup) return prev;
            return [...prev, {
              timestamp: data.timestamp || new Date().toISOString(),
              stage: data.stage || 'pipeline',
              message: data.message,
              status: data.status || 'running'
            }];
          });
        }
      } catch (err) {
        console.error('Error parsing SSE event:', err);
      }
    };

    eventSource.onerror = (err) => {
      console.log('SSE connection closed or completed.');
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [workspaceId]);

  useEffect(() => {
    if (terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  const fetchWorkspace = async () => {
    try {
      const data = await apiService.getWorkspace(workspaceId);
      setWorkspace(data);
      setPipelineStatus(data.status);
    } catch (err) {
      toast.error('Failed to load workspace details');
      router.push('/dashboard');
    } finally {
      setLoading(false);
    }
  };

  const getStageIndex = (stageKey: string) => {
    return stages.findIndex(s => s.key === stageKey);
  };

  const currentActiveStageIndex = () => {
    switch (pipelineStatus) {
      case 'uploaded': return 0;
      case 'extracting': return 1;
      case 'extracted': return 2;
      case 'matching': return 2;
      case 'drafting': return 3;
      case 'scoring': return 4;
      case 'complete': return 5;
      default: return 0;
    }
  };

  if (loading) {
    return (
      <div className="py-32 flex flex-col items-center justify-center gap-3">
        <Loader2 className="w-8 h-8 text-violet-500 animate-spin" />
        <p className="text-gray-400">Loading pipeline status...</p>
      </div>
    );
  }

  const activeIndex = currentActiveStageIndex();

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold text-white tracking-tight">{workspace?.name}</h1>
            <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${
              pipelineStatus === 'complete' 
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' 
                : pipelineStatus === 'error'
                  ? 'bg-red-500/10 text-red-400 border-red-500/20'
                  : 'bg-amber-500/10 text-amber-400 border-amber-500/20 animate-pulse'
            }`}>
              {pipelineStatus.toUpperCase()}
            </span>
          </div>
          <p className="text-gray-400 text-sm mt-1.5">
            RFP Source File:{' '}
            <span className="font-mono text-xs text-gray-500">{workspace?.rfp_filename}</span>
          </p>
        </div>
        
        {pipelineStatus === 'complete' && (
          <Link
            href={`/workspace/${workspaceId}/compliance`}
            className="flex items-center gap-2 px-5 py-3 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-semibold rounded-xl shadow-lg shadow-violet-500/20 transition-all duration-300"
          >
            <span>View Compliance Matrix</span>
            <ArrowRight className="w-5 h-5" />
          </Link>
        )}
      </div>

      {/* Stepper Status Indicators */}
      <div className="bg-[#0c0c12] border border-[#1a1a24] p-8 rounded-2xl">
        <div className="relative flex flex-col md:flex-row justify-between items-center gap-8 md:gap-4">
          {stages.map((stage, idx) => {
            const Icon = stage.icon;
            const isCompleted = idx < activeIndex;
            const isActive = idx === activeIndex;
            const isPending = idx > activeIndex;

            return (
              <React.Fragment key={stage.key}>
                {/* Connector line */}
                {idx > 0 && (
                  <div className={`hidden md:block flex-1 h-0.5 transition-all duration-500 ${
                    idx <= activeIndex ? 'bg-violet-500' : 'bg-[#1e1e2c]'
                  }`} />
                )}

                {/* Step Circle */}
                <div className="flex flex-col items-center text-center relative z-10">
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center border transition-all duration-500 ${
                    isCompleted 
                      ? 'bg-violet-600 border-violet-500 text-white' 
                      : isActive 
                        ? 'bg-violet-500/10 border-violet-500 text-violet-400 shadow-[0_0_15px_rgba(139,92,246,0.3)] animate-pulse' 
                        : 'bg-[#13131c] border-[#222230] text-gray-500'
                  }`}>
                    {isCompleted ? <Check className="w-6 h-6" /> : <Icon className="w-5 h-5" />}
                  </div>
                  <span className={`text-xs font-semibold mt-3 ${
                    isActive ? 'text-violet-400' : isCompleted ? 'text-white' : 'text-gray-500'
                  }`}>
                    {stage.label}
                  </span>
                </div>
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {/* Shortcut Panels (Visible only when completed) */}
      {pipelineStatus === 'complete' && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <Link
            href={`/workspace/${workspaceId}/extract`}
            className="bg-[#0e0e16]/80 hover:bg-[#13131f] border border-[#1d1d2b] hover:border-violet-500/35 p-5 rounded-2xl flex flex-col justify-between h-36 transition-all duration-300 group shadow-md"
          >
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20 flex items-center justify-center group-hover:scale-110 transition-transform">
              <Search className="w-5 h-5" />
            </div>
            <div>
              <h4 className="font-bold text-white text-sm">Requirements Checklist</h4>
              <span className="text-gray-500 text-xs mt-1 block">47 records extracted</span>
            </div>
          </Link>

          <Link
            href={`/workspace/${workspaceId}/match`}
            className="bg-[#0e0e16]/80 hover:bg-[#13131f] border border-[#1d1d2b] hover:border-violet-500/35 p-5 rounded-2xl flex flex-col justify-between h-36 transition-all duration-300 group shadow-md"
          >
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 flex items-center justify-center group-hover:scale-110 transition-transform">
              <BookOpen className="w-5 h-5" />
            </div>
            <div>
              <h4 className="font-bold text-white text-sm">RAG Library Matches</h4>
              <span className="text-gray-500 text-xs mt-1 block">43 records generated</span>
            </div>
          </Link>

          <Link
            href={`/workspace/${workspaceId}/draft`}
            className="bg-[#0e0e16]/80 hover:bg-[#13131f] border border-[#1d1d2b] hover:border-violet-500/35 p-5 rounded-2xl flex flex-col justify-between h-36 transition-all duration-300 group shadow-md"
          >
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center justify-center group-hover:scale-110 transition-transform">
              <FileSignature className="w-5 h-5" />
            </div>
            <div>
              <h4 className="font-bold text-white text-sm">Proposal Editor</h4>
              <span className="text-gray-500 text-xs mt-1 block">9 sections generated</span>
            </div>
          </Link>

          <Link
            href={`/workspace/${workspaceId}/compliance`}
            className="bg-[#0e0e16]/80 hover:bg-[#13131f] border border-[#1d1d2b] hover:border-violet-500/35 p-5 rounded-2xl flex flex-col justify-between h-36 transition-all duration-300 group shadow-md"
          >
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center group-hover:scale-110 transition-transform">
              <FileCheck2 className="w-5 h-5" />
            </div>
            <div>
              <h4 className="font-bold text-white text-sm">Compliance Matrix</h4>
              <span className="text-gray-500 text-xs mt-1 block">82% overall score</span>
            </div>
          </Link>

          <Link
            href={`/workspace/${workspaceId}/score`}
            className="bg-[#0e0e16]/80 hover:bg-[#13131f] border border-[#1d1d2b] hover:border-violet-500/35 p-5 rounded-2xl flex flex-col justify-between h-36 transition-all duration-300 group shadow-md"
          >
            <div className="w-10 h-10 rounded-xl bg-violet-500/10 text-violet-400 border border-violet-500/20 flex items-center justify-center group-hover:scale-110 transition-transform">
              <TrendingUp className="w-5 h-5" />
            </div>
            <div>
              <h4 className="font-bold text-white text-sm">Win Predictor</h4>
              <span className="text-gray-500 text-xs mt-1 block">74% probability score</span>
            </div>
          </Link>
        </div>
      )}

      {/* Agent Collaboration Trace Graph */}
      <div className="bg-[#0c0c12] border border-[#1a1a24] rounded-2xl p-6 shadow-2xl space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-violet-500 animate-pulse" />
            <span className="text-sm font-bold text-white tracking-tight">Agent Collaboration Trace</span>
          </div>
          <span className="text-[10px] text-gray-500 font-mono uppercase tracking-widest">Multi-Agent Pipeline Flow</span>
        </div>

        <div className="relative w-full overflow-x-auto">
          <svg viewBox="0 0 940 180" className="w-full min-w-[700px] h-auto" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <filter id="glow-active">
                <feGaussianBlur stdDeviation="6" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
              <linearGradient id="line-grad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#8b5cf6" stopOpacity="0.8" />
                <stop offset="100%" stopColor="#6366f1" stopOpacity="0.3" />
              </linearGradient>
            </defs>

            {/* Connector lines */}
            {[
              { x1: 120, y1: 90, x2: 250, y2: 90 },
              { x1: 340, y1: 90, x2: 410, y2: 90 },
              { x1: 500, y1: 90, x2: 570, y2: 90 },
              { x1: 660, y1: 90, x2: 730, y2: 90 },
              { x1: 820, y1: 90, x2: 890, y2: 55 },
            ].map((line, i) => {
              const isActive = i < activeIndex;
              const isCurrent = i === activeIndex - 1;
              return (
                <line
                  key={`conn-${i}`}
                  x1={line.x1} y1={line.y1} x2={line.x2} y2={line.y2}
                  stroke={isActive ? '#8b5cf6' : '#1e1e2c'}
                  strokeWidth={isActive ? 2.5 : 1.5}
                  strokeDasharray={isCurrent ? '6 4' : 'none'}
                  className={isCurrent ? 'animate-pulse' : ''}
                />
              );
            })}

            {/* Agent Nodes */}
            {[
              { cx: 80, cy: 90, label: 'RFP Parser', sub: 'Document Ingestor', color: '#3b82f6', stageIdx: 0, icon: '📄' },
              { cx: 250, cy: 90, label: 'NER Extractor', sub: 'spaCy + Gemini', color: '#8b5cf6', stageIdx: 1, icon: '🔍' },
              { cx: 420, cy: 90, label: 'RAG Matcher', sub: 'BM25 + ChromaDB', color: '#6366f1', stageIdx: 2, icon: '🧠' },
              { cx: 590, cy: 90, label: 'CrewAI Writer', sub: '5-Agent Collab', color: '#f59e0b', stageIdx: 3, icon: '✍️' },
              { cx: 760, cy: 90, label: 'Compliance Auditor', sub: 'Pass/Fail Gate', color: '#10b981', stageIdx: 4, icon: '✅' },
              { cx: 900, cy: 45, label: 'ML Win Scorer', sub: 'RandomForest', color: '#ef4444', stageIdx: 4, icon: '📊' },
            ].map((node, i) => {
              const isCompleted = node.stageIdx < activeIndex;
              const isActive = node.stageIdx === activeIndex;
              const nodeColor = isCompleted ? node.color : isActive ? node.color : '#2a2a3d';
              const textColor = isCompleted || isActive ? '#ffffff' : '#555566';

              return (
                <g key={`node-${i}`} filter={isActive ? 'url(#glow-active)' : undefined}>
                  {/* Outer ring */}
                  <circle
                    cx={node.cx} cy={node.cy} r={32}
                    fill="none"
                    stroke={nodeColor}
                    strokeWidth={isActive ? 2.5 : 1}
                    strokeDasharray={isActive ? '4 3' : 'none'}
                    opacity={isCompleted || isActive ? 1 : 0.3}
                    className={isActive ? 'animate-spin' : ''}
                    style={isActive ? { transformOrigin: `${node.cx}px ${node.cy}px`, animationDuration: '8s' } : undefined}
                  />
                  {/* Inner fill */}
                  <circle
                    cx={node.cx} cy={node.cy} r={24}
                    fill={isCompleted ? nodeColor : isActive ? `${nodeColor}33` : '#13131c'}
                    stroke={nodeColor}
                    strokeWidth={1}
                    opacity={isCompleted || isActive ? 1 : 0.4}
                  />
                  {/* Icon */}
                  <text x={node.cx} y={node.cy + 5} textAnchor="middle" fontSize="16" fill={textColor}>
                    {node.icon}
                  </text>
                  {/* Label */}
                  <text x={node.cx} y={node.cy + 52} textAnchor="middle" fontSize="10" fontWeight="bold" fill={textColor}>
                    {node.label}
                  </text>
                  <text x={node.cx} y={node.cy + 65} textAnchor="middle" fontSize="8" fill="#555566">
                    {node.sub}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>

        {/* Live metrics strip */}
        <div className="flex items-center gap-6 border-t border-[#1c1c28] pt-4">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-violet-500" />
            <span className="text-[10px] text-gray-400 font-semibold uppercase">Active Stage</span>
            <span className="text-[10px] text-white font-bold">{stages[Math.min(activeIndex, stages.length - 1)]?.label}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span className="text-[10px] text-gray-400 font-semibold uppercase">Agents Used</span>
            <span className="text-[10px] text-white font-bold">{Math.min(activeIndex + 1, 6)} / 6</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-amber-500" />
            <span className="text-[10px] text-gray-400 font-semibold uppercase">Pipeline Status</span>
            <span className={`text-[10px] font-bold ${pipelineStatus === 'complete' ? 'text-emerald-400' : 'text-amber-400'}`}>
              {pipelineStatus.toUpperCase()}
            </span>
          </div>
        </div>
      </div>

      {/* Terminal logs pane */}
      <div className="bg-black border border-[#1c1c2b] rounded-2xl overflow-hidden shadow-2xl">
        <div className="px-6 py-4 bg-[#09090f] border-b border-[#1c1c2b] flex items-center justify-between">
          <div className="flex items-center gap-2 text-gray-400">
            <Terminal className="w-4.5 h-4.5 text-violet-500" />
            <span className="text-sm font-semibold font-mono">Pipeline Execution Console</span>
          </div>
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping" />
        </div>
        
        <div className="p-6 h-[320px] overflow-y-auto font-mono text-xs space-y-2.5 scrollbar-thin scrollbar-thumb-zinc-800">
          {logs.length === 0 ? (
            <p className="text-gray-600 italic">Console initialized. Waiting for pipeline updates...</p>
          ) : (
            logs.map((log, index) => (
              <div key={index} className="flex gap-4 items-start group">
                <span className="text-gray-600 select-none">
                  [{format(new Date(log.timestamp), 'HH:mm:ss')}]
                </span>
                <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold tracking-wider select-none ${
                  log.stage === 'finished' 
                    ? 'bg-emerald-500/10 text-emerald-400' 
                    : 'bg-violet-500/10 text-violet-400'
                }`}>
                  {log.stage}
                </span>
                <span className={`${
                  log.stage === 'finished' 
                    ? 'text-emerald-400 font-semibold' 
                    : log.status === 'error'
                      ? 'text-red-400 font-semibold'
                      : 'text-gray-300'
                }`}>
                  {log.message}
                </span>
              </div>
            ))
          )}
          <div ref={terminalEndRef} />
        </div>
      </div>
    </div>
  );
}
