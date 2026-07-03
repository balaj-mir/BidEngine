'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { 
  ArrowLeft, 
  RotateCcw, 
  TrendingUp, 
  AlertCircle, 
  Loader2, 
  ShieldAlert,
  Sliders,
  CheckCircle,
  HelpCircle,
  Award,
  DollarSign,
  Users
} from 'lucide-react';
import toast from 'react-hot-toast';
import { apiService } from '../../../../lib/api';
import { BidScore } from '../../../../lib/types';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';

export default function WinScorerPage() {
  const params = useParams();
  const router = useRouter();
  const workspaceId = params.id as string;

  const [score, setScore] = useState<BidScore | null>(null);
  const [loading, setLoading] = useState(true);
  const [recalculating, setRecalculating] = useState(false);

  const [simCompliance, setSimCompliance] = useState<number>(80);
  const [simCompetitors, setSimCompetitors] = useState<number>(4);
  const [simCertifications, setSimCertifications] = useState<boolean>(true);
  const [simContractValue, setSimContractValue] = useState<number>(1500000);
  const [simScore, setSimScore] = useState<any>(null);
  const [simulating, setSimulating] = useState(false);

  useEffect(() => {
    if (score) {
      setSimCompliance(Math.round(score.score_breakdown?.compliance_completeness * 100 || 80));
      setSimCompetitors(4);
      setSimCertifications(true);
      setSimContractValue(1500000);
      setSimScore(score);
    }
  }, [score]);

  const triggerSim = async (comp: number, compCount: number, certs: boolean, val: number) => {
    setSimulating(true);
    try {
      const payload = {
        compliance_score: comp,
        competitor_count: compCount,
        certifications_met: certs,
        contract_value: val
      };
      const data = await apiService.simulateScore(workspaceId, payload);
      setSimScore(data);
    } catch (err) {
      console.error("Simulation failed", err);
    } finally {
      setSimulating(false);
    }
  };

  useEffect(() => {
    fetchScore();
  }, [workspaceId]);

  const fetchScore = async () => {
    try {
      const data = await apiService.getScore(workspaceId);
      setScore(data);
    } catch (err) {
      toast.error('Failed to load ML scorecard');
    } finally {
      setLoading(false);
    }
  };

  const handleRecalculate = async () => {
    setRecalculating(true);
    try {
      const data = await apiService.recalculateScore(workspaceId);
      setScore(data);
      toast.success('ML Win Probability recalculated successfully!');
    } catch (err) {
      toast.error('Failed to recalculate score');
    } finally {
      setRecalculating(false);
    }
  };

  if (loading) {
    return (
      <div className="py-32 flex flex-col items-center justify-center gap-3">
        <Loader2 className="w-8 h-8 text-violet-500 animate-spin" />
        <p className="text-gray-400">Loading ML win predictor stats...</p>
      </div>
    );
  }

  // Prep Recharts data for feature importance
  const featureData = score?.feature_importance 
    ? Object.entries(score.feature_importance)
        .map(([key, val]) => ({
          name: key.replace(/_/g, ' ').toUpperCase(),
          weight: Math.round(val * 1000) / 10
        }))
        .sort((a, b) => b.weight - a.weight)
    : [];

  // Prep sub-scores data for visual bars
  const scoreBreakdown = score?.score_breakdown 
    ? [
        { name: 'Compliance Completeness', val: score.score_breakdown.compliance_completeness },
        { name: 'Domain Experience Fit', val: score.score_breakdown.domain_experience_match },
        { name: 'Budget Alignment', val: score.score_breakdown.budget_alignment },
        { name: 'Technical Fit', val: score.score_breakdown.technical_complexity_fit },
        { name: 'Timeline Feasibility', val: score.score_breakdown.timeline_feasibility },
        { name: 'Competitor Risk', val: score.score_breakdown.competition_risk },
      ]
    : [];

  const winProb = score ? Math.round(score.win_probability * 100) : 0;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-4">
          <Link
            href={`/workspace/${workspaceId}`}
            className="p-2.5 bg-[#0e0e16] hover:bg-[#13131f] border border-[#1a1a28] text-gray-400 hover:text-white rounded-xl transition-all"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-3xl font-bold text-white tracking-tight">Win Scorer Engine</h1>
            <p className="text-gray-400 text-sm mt-1">Calibrated ML win probability modeling & feature insights.</p>
          </div>
        </div>

        <button
          onClick={handleRecalculate}
          disabled={recalculating}
          className="flex items-center gap-2 px-5 py-3 bg-[#12121b] hover:bg-[#1c1c2b] border border-[#222230] hover:border-[#33334d] text-gray-300 font-semibold rounded-xl text-sm transition-all duration-300 active:scale-95 disabled:opacity-50"
        >
          {recalculating ? <Loader2 className="w-4 h-4 animate-spin" /> : <RotateCcw className="w-4 h-4" />}
          <span>Recalculate Win Score</span>
        </button>
      </div>

      {!score ? (
        <div className="bg-[#0c0c12] p-16 border border-[#1a1a24] text-center rounded-2xl space-y-4">
          <AlertCircle className="w-12 h-12 text-gray-500 mx-auto" />
          <div>
            <h3 className="text-white font-semibold">No Score Data Available</h3>
            <p className="text-gray-500 text-sm mt-1">Please ensure the pipeline has fully completed scoring.</p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left Panel: Win Probability Card (5 cols) */}
          <div className="lg:col-span-5 bg-[#0c0c12] border border-[#1a1a24] rounded-2xl p-6 shadow-2xl relative overflow-hidden flex flex-col justify-between min-h-[580px]">
            {/* Glow design */}
            <div className={`absolute top-[-20%] left-[-20%] w-[80%] h-[80%] rounded-full blur-[100px] pointer-events-none opacity-20 ${
              score.go_no_go === 'GO' ? 'bg-emerald-500' : score.go_no_go === 'NO-GO' ? 'bg-red-500' : 'bg-amber-500'
            }`} />

            <div className="space-y-6 relative z-10">
              <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest block">Machine Learning Prediction</span>
              
              {/* Circular probability display */}
              <div className="flex flex-col items-center justify-center py-6">
                <div className="relative w-44 h-44 flex items-center justify-center">
                  {/* Gauge backdrop */}
                  <svg className="w-full h-full transform -rotate-90">
                    <circle cx="88" cy="88" r="76" stroke="#1c1c28" strokeWidth="10" fill="transparent" />
                    <circle 
                      cx="88" 
                      cy="88" 
                      r="76" 
                      stroke={score.go_no_go === 'GO' ? '#10b981' : score.go_no_go === 'NO-GO' ? '#ef4444' : '#f59e0b'}
                      strokeWidth="10" 
                      fill="transparent" 
                      strokeDasharray="478"
                      strokeDashoffset={478 - (478 * winProb) / 100}
                      className="transition-all duration-1000 ease-out"
                    />
                  </svg>
                  
                  {/* Gauge values */}
                  <div className="absolute text-center">
                    <span className="text-4xl font-black text-white">{winProb}%</span>
                    <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider block mt-1">Win Probability</span>
                  </div>
                </div>
              </div>

              {/* Status flags */}
              <div className="grid grid-cols-2 gap-4 border-t border-[#1c1c28] pt-6">
                <div>
                  <span className="text-[10px] text-gray-500 font-bold uppercase block">GO/NO-GO DECISION</span>
                  <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border mt-2 ${
                    score.go_no_go === 'GO'
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                      : score.go_no_go === 'NO-GO'
                        ? 'bg-red-500/10 text-red-400 border-red-500/20'
                        : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                  }`}>
                    {score.go_no_go}
                  </span>
                </div>

                <div>
                  <span className="text-[10px] text-gray-500 font-bold uppercase block">MODEL CONFIDENCE</span>
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border border-[#222230] text-white mt-2 bg-[#12121b]">
                    {score.confidence_level}
                  </span>
                </div>
              </div>
            </div>

            {/* Decision Reasoning text */}
            <div className="border-t border-[#1c1c28] pt-6 space-y-2 relative z-10 mt-6">
              <span className="text-[10px] text-indigo-400 font-bold uppercase tracking-widest block">AI Decision Reasoning</span>
              <p className="text-xs text-gray-400 leading-relaxed font-mono">
                {score.go_no_go_reasoning}
              </p>
            </div>
          </div>

          {/* Right Panel: Feature Weights & Sub-scores (7 cols) */}
          <div className="lg:col-span-7 space-y-6">
            {/* Feature Weights Chart */}
            <div className="bg-[#0c0c12] border border-[#1a1a24] p-6 rounded-2xl space-y-4 shadow-xl">
              <h4 className="font-bold text-sm text-white flex items-center gap-2">
                <Sliders className="w-4.5 h-4.5 text-violet-400" />
                <span>Random Forest Model Feature Weights</span>
              </h4>

              <div className="h-[280px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={featureData} layout="vertical" margin={{ left: 10, right: 30, top: 10, bottom: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#161622" />
                    <XAxis type="number" stroke="#52526b" tickFormatter={(v) => `${v}%`} />
                    <YAxis dataKey="name" type="category" stroke="#52526b" width={140} tick={{ fill: '#9ca3af', fontSize: 9, fontWeight: 'bold' }} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#0e0e16', border: '1px solid #222230', borderRadius: '12px' }}
                      labelStyle={{ color: '#fff', fontSize: 10, fontWeight: 'bold' }}
                      formatter={(value) => [`${value}%`, 'Importance']}
                    />
                    <Bar dataKey="weight" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Sub-Scores Matrix (Radar Chart) */}
            <div className="bg-[#0c0c12] border border-[#1a1a24] p-6 rounded-2xl space-y-4 shadow-xl">
              <h4 className="font-bold text-sm text-white flex items-center gap-2">
                <TrendingUp className="w-4.5 h-4.5 text-emerald-400" />
                <span>Bid Scorecard Factors Breakdown</span>
              </h4>

              <div className="h-[280px]">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart cx="50%" cy="50%" outerRadius="80%" data={scoreBreakdown}>
                    <PolarGrid stroke="#222230" />
                    <PolarAngleAxis dataKey="name" tick={{ fill: '#9ca3af', fontSize: 10, fontWeight: 'bold' }} />
                    <PolarRadiusAxis angle={30} domain={[0, 1]} tick={false} axisLine={false} />
                    <Radar
                      name="Score"
                      dataKey="val"
                      stroke="#10b981"
                      fill="#10b981"
                      fillOpacity={0.4}
                      isAnimationActive={true}
                      animationDuration={1500}
                    />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0e0e16', border: '1px solid #222230', borderRadius: '12px' }}
                      labelStyle={{ color: '#fff', fontSize: 10, fontWeight: 'bold' }}
                      formatter={(value: any) => [`${Math.round(value * 100)}%`, 'Score']}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </div>

        {/* Dynamic Simulator Section */}
        <div className="bg-[#0c0c12] border border-[#1a1a24] rounded-2xl p-6 shadow-xl mt-8 space-y-6">
          <div>
            <h3 className="text-xl font-bold text-white flex items-center gap-2">
              <Sliders className="w-5 h-5 text-indigo-400" />
              <span>Sensitivity Simulation Sandbox</span>
            </h3>
            <p className="text-gray-400 text-xs mt-1">Adjust individual proposal parameters to preview simulated RFPs win probability and client impact.</p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            {/* Sliders Panel */}
            <div className="lg:col-span-7 space-y-6">
              {/* Compliance Slider */}
              <div className="space-y-2">
                <div className="flex justify-between items-center text-xs font-semibold">
                  <span className="text-gray-300">RFP Compliance Completeness</span>
                  <span className="text-indigo-400">{simCompliance}%</span>
                </div>
                <input 
                  type="range" 
                  min="0" 
                  max="100" 
                  value={simCompliance}
                  onChange={(e) => {
                    const val = Number(e.target.value);
                    setSimCompliance(val);
                    triggerSim(val, simCompetitors, simCertifications, simContractValue);
                  }}
                  className="w-full accent-indigo-500 bg-[#141420] h-2 rounded-lg cursor-pointer appearance-none"
                />
              </div>

              {/* Competitors Slider */}
              <div className="space-y-2">
                <div className="flex justify-between items-center text-xs font-semibold">
                  <span className="text-gray-300">Active Bidding Competitors</span>
                  <span className="text-indigo-400">{simCompetitors} competitors</span>
                </div>
                <input 
                  type="range" 
                  min="1" 
                  max="12" 
                  value={simCompetitors}
                  onChange={(e) => {
                    const val = Number(e.target.value);
                    setSimCompetitors(val);
                    triggerSim(simCompliance, val, simCertifications, simContractValue);
                  }}
                  className="w-full accent-indigo-500 bg-[#141420] h-2 rounded-lg cursor-pointer appearance-none"
                />
              </div>

              {/* Contract Value Slider */}
              <div className="space-y-2">
                <div className="flex justify-between items-center text-xs font-semibold">
                  <span className="text-gray-300">Simulated Contract Budget</span>
                  <span className="text-indigo-400">${(simContractValue / 1000000).toFixed(1)}M</span>
                </div>
                <input 
                  type="range" 
                  min="100000" 
                  max="10000000" 
                  step="100000"
                  value={simContractValue}
                  onChange={(e) => {
                    const val = Number(e.target.value);
                    setSimContractValue(val);
                    triggerSim(simCompliance, simCompetitors, simCertifications, val);
                  }}
                  className="w-full accent-indigo-500 bg-[#141420] h-2 rounded-lg cursor-pointer appearance-none"
                />
              </div>

              {/* Certifications Met Toggle */}
              <div className="flex items-center justify-between p-4 bg-black/30 border border-[#1a1a26] rounded-xl">
                <div>
                  <span className="text-xs font-semibold text-gray-300 block">Mandatory ISO / Security Certifications</span>
                  <span className="text-[10px] text-gray-500 block">Does your organization satisfy all mandatory credential checklists?</span>
                </div>
                <div className="flex gap-2">
                  <button 
                    onClick={() => {
                      setSimCertifications(true);
                      triggerSim(simCompliance, simCompetitors, true, simContractValue);
                    }}
                    className={`px-3 py-1.5 text-xs font-bold rounded-lg border transition-all ${
                      simCertifications 
                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' 
                        : 'bg-[#0e0e16] border-[#222230] text-gray-400 hover:text-gray-200'
                    }`}
                  >
                    All Met
                  </button>
                  <button 
                    onClick={() => {
                      setSimCertifications(false);
                      triggerSim(simCompliance, simCompetitors, false, simContractValue);
                    }}
                    className={`px-3 py-1.5 text-xs font-bold rounded-lg border transition-all ${
                      !simCertifications 
                        ? 'bg-red-500/10 text-red-400 border-red-500/20' 
                        : 'bg-[#0e0e16] border-[#222230] text-gray-400 hover:text-gray-200'
                    }`}
                  >
                    Gaps Present
                  </button>
                </div>
              </div>
            </div>

            {/* Results Panel */}
            <div className="lg:col-span-5 bg-black/40 border border-[#1d1d2b] p-6 rounded-2xl flex flex-col justify-between min-h-[350px] relative overflow-hidden">
              <div className={`absolute top-[-20%] right-[-20%] w-[70%] h-[70%] rounded-full blur-[90px] pointer-events-none opacity-20 ${
                (simScore || score).go_no_go === 'GO' ? 'bg-emerald-500' : (simScore || score).go_no_go === 'NO-GO' ? 'bg-red-500' : 'bg-amber-500'
              }`} />

              <div className="space-y-4 relative z-10">
                <span className="text-[10px] text-gray-400 font-bold uppercase tracking-widest block">Simulated Output</span>
                
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-[10px] text-gray-500 block uppercase font-semibold">Simulated Probability</span>
                    <span className="text-4xl font-black text-white mt-1">
                      {Math.round(((simScore || score).win_probability) * 100)}%
                    </span>
                  </div>
                  
                  <div className="text-right">
                    <span className="text-[10px] text-gray-500 block uppercase font-semibold">Projected Decision</span>
                    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border mt-2 ${
                      (simScore || score).go_no_go === 'GO'
                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                        : (simScore || score).go_no_go === 'NO-GO'
                          ? 'bg-red-500/10 text-red-400 border-red-500/20'
                          : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                    }`}>
                      {(simScore || score).go_no_go}
                    </span>
                  </div>
                </div>

                <div className="border-t border-[#1c1c28] pt-4 space-y-2">
                  <span className="text-[10px] text-indigo-400 font-bold uppercase tracking-wider block">Simulation Insights</span>
                  <p className="text-xs text-gray-300 leading-relaxed font-mono min-h-[80px]">
                    {(simScore || score).go_no_go_reasoning}
                  </p>
                </div>
              </div>

              {simulating && (
                <div className="absolute inset-0 bg-black/60 backdrop-blur-[2px] flex items-center justify-center gap-2">
                  <Loader2 className="w-5 h-5 text-indigo-500 animate-spin" />
                  <span className="text-xs font-semibold text-gray-300">Recalculating...</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
