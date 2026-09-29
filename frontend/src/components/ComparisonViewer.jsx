import React, { useState, useMemo } from 'react';
import { 
  GitCompare, 
  ArrowRight, 
  AlertTriangle, 
  CheckCircle, 
  TrendingUp, 
  TrendingDown, 
  Minus, 
  Download, 
  Sparkles, 
  Filter, 
  FileText, 
  ShieldAlert, 
  ChevronRight,
  ExternalLink
} from 'lucide-react';
import { api } from '../services/api';

export default function ComparisonViewer({ 
  documents = [], 
  selectedProvider = null,
  onDocumentsUpdated = () => {} 
}) {
  const [doc1Id, setDoc1Id] = useState('');
  const [doc2Id, setDoc2Id] = useState('');
  const [comparison, setComparison] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingSample, setIsLoadingSample] = useState(false);
  const [filterType, setFilterType] = useState('ALL'); // ALL, CRITICAL, ADVERSE, MODIFIED
  const [error, setError] = useState(null);

  const completedDocs = useMemo(() => {
    return documents.filter(d => d.status === 'COMPLETED');
  }, [documents]);

  const handleRunComparison = async (overrideDoc1 = null, overrideDoc2 = null) => {
    const d1 = overrideDoc1 || doc1Id;
    const d2 = overrideDoc2 || doc2Id;
    if (!d1 || !d2) {
      setError("Please select both a baseline and a revision document.");
      return;
    }
    if (d1 === d2) {
      setError("Please choose two different documents to compare.");
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const res = await api.compareDocuments(d1, d2, selectedProvider);
      setComparison(res);
    } catch (e) {
      console.error("Comparison error:", e);
      setError(e.message || "Failed to execute comparative audit.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleLoadSamplePair = async () => {
    setIsLoadingSample(true);
    setError(null);
    try {
      const res = await api.loadComparisonSamplePair(selectedProvider);
      if (res.comparison) {
        setComparison(res.comparison);
        setDoc1Id(res.doc1.id);
        setDoc2Id(res.doc2.id);
      }
      if (onDocumentsUpdated) {
        onDocumentsUpdated();
      }
    } catch (e) {
      console.error("Sample pair error:", e);
      setError(e.message || "Failed to load sample comparison pair.");
    } finally {
      setIsLoadingSample(false);
    }
  };

  const filteredDiffs = useMemo(() => {
    if (!comparison || !comparison.clause_diffs) return [];
    if (filterType === 'ALL') return comparison.clause_diffs;
    if (filterType === 'CRITICAL') {
      return comparison.clause_diffs.filter(d => d.risk_impact === 'CRITICAL_ESCALATION');
    }
    if (filterType === 'ADVERSE') {
      return comparison.clause_diffs.filter(d => d.risk_impact === 'ADVERSE' || d.risk_impact === 'CRITICAL_ESCALATION');
    }
    if (filterType === 'MODIFIED') {
      return comparison.clause_diffs.filter(d => d.change_type === 'MODIFIED');
    }
    return comparison.clause_diffs;
  }, [comparison, filterType]);

  const getImpactBadge = (impact) => {
    switch (impact) {
      case 'CRITICAL_ESCALATION':
        return {
          bg: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
          dot: 'bg-rose-500',
          label: 'Critical Escalation'
        };
      case 'ADVERSE':
        return {
          bg: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
          dot: 'bg-amber-500',
          label: 'Adverse Shift'
        };
      case 'FAVORABLE':
        return {
          bg: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
          dot: 'bg-emerald-500',
          label: 'Favorable Protection'
        };
      default:
        return {
          bg: 'bg-zinc-800 text-zinc-300 border-zinc-700',
          dot: 'bg-zinc-400',
          label: 'Neutral Shift'
        };
    }
  };

  const getDeltaBadge = (delta) => {
    if (delta.score_delta > 0) {
      return {
        bg: 'bg-rose-500/10 text-rose-400 border-rose-500/25',
        icon: TrendingUp,
        text: `+${delta.score_delta} pts Risk Increase`
      };
    } else if (delta.score_delta < 0) {
      return {
        bg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/25',
        icon: TrendingDown,
        text: `${delta.score_delta} pts Risk Reduced`
      };
    }
    return {
      bg: 'bg-zinc-800 text-zinc-300 border-zinc-700',
      icon: Minus,
      text: '0 pts Risk Delta (Neutral)'
    };
  };

  return (
    <div className="flex flex-col space-y-6">
      {/* Top Header & Selector Box */}
      <div className="bg-zinc-900/60 border border-zinc-850 rounded-xl p-5 backdrop-blur-md flex flex-col space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-zinc-850">
          <div>
            <div className="flex items-center space-x-2">
              <span className="p-1.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                <GitCompare className="w-4 h-4" />
              </span>
              <h2 className="text-base font-semibold text-zinc-100 tracking-tight">
                Multi-Document Redline & Comparative Audit
              </h2>
            </div>
            <p className="text-xs text-zinc-400 mt-1">
              Select two contracts or financial filings to evaluate clause modifications, exposure deltas, and renegotiation leverage.
            </p>
          </div>

          {/* Quick-action 1-click sample pair */}
          <button
            onClick={handleLoadSamplePair}
            disabled={isLoadingSample || isLoading}
            className="self-start sm:self-center bg-gradient-to-r from-indigo-900/40 via-zinc-900 to-indigo-950/40 hover:from-indigo-900/60 hover:to-indigo-900/40 text-indigo-200 border border-indigo-500/30 hover:border-indigo-500/50 px-3.5 py-1.5 rounded-lg text-xs font-medium transition flex items-center space-x-2 shadow-sm shrink-0"
            title="Load sample MSA v1 (Baseline) vs MSA v2 (Counterparty Redline)"
          >
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            <span>{isLoadingSample ? 'Seeding Sample Pair...' : '⚡ Load Sample Redline Pair'}</span>
          </button>
        </div>

        {/* Document Selection Grid */}
        <div className="grid grid-cols-1 md:grid-cols-7 gap-3 items-center">
          {/* Doc 1 (Baseline) */}
          <div className="md:col-span-3 flex flex-col space-y-1.5">
            <label className="text-[11px] font-mono uppercase tracking-wider text-zinc-400">
              Document 1 (Baseline / Original)
            </label>
            <select
              value={doc1Id}
              onChange={(e) => setDoc1Id(e.target.value)}
              className="bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-xs text-zinc-200 focus:outline-none focus:border-indigo-500 transition"
            >
              <option value="">-- Choose baseline document --</option>
              {completedDocs.map(d => (
                <option key={d.id} value={d.id}>
                  {d.filename} ({d.audit_type || 'legal'})
                </option>
              ))}
            </select>
          </div>

          {/* VS Divider */}
          <div className="md:col-span-1 flex justify-center items-center pt-4 md:pt-0">
            <span className="bg-zinc-850 border border-zinc-750 text-zinc-400 text-[10px] font-mono font-bold px-2 py-1 rounded-full uppercase tracking-widest">
              VS
            </span>
          </div>

          {/* Doc 2 (Revision) */}
          <div className="md:col-span-3 flex flex-col space-y-1.5">
            <label className="text-[11px] font-mono uppercase tracking-wider text-zinc-400">
              Document 2 (Revision / Counterparty Draft)
            </label>
            <select
              value={doc2Id}
              onChange={(e) => setDoc2Id(e.target.value)}
              className="bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-xs text-zinc-200 focus:outline-none focus:border-indigo-500 transition"
            >
              <option value="">-- Choose revision document --</option>
              {completedDocs.map(d => (
                <option key={d.id} value={d.id}>
                  {d.filename} ({d.audit_type || 'legal'})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Compare Trigger Button */}
        <div className="flex justify-end pt-2">
          <button
            onClick={() => handleRunComparison()}
            disabled={isLoading || !doc1Id || !doc2Id || doc1Id === doc2Id}
            className="bg-indigo-600 hover:bg-indigo-500 disabled:bg-zinc-800 disabled:text-zinc-600 disabled:cursor-not-allowed text-white text-xs font-medium px-4 py-2 rounded-lg transition flex items-center space-x-2 shadow-sm"
          >
            <GitCompare className="w-3.5 h-3.5" />
            <span>{isLoading ? 'Analyzing Differences...' : 'Run Comparative Redline Audit'}</span>
          </button>
        </div>

        {error && (
          <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-lg text-xs text-rose-300 flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Comparison Results Dashboard */}
      {comparison && (
        <div className="flex flex-col space-y-6">
          {/* Executive Risk Shift Banner */}
          <div className="bg-zinc-900/60 border border-zinc-850 rounded-xl p-6 backdrop-blur-md flex flex-col space-y-5">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-zinc-850">
              <div>
                <span className="text-[11px] font-mono uppercase tracking-wider text-indigo-400 font-semibold">
                  Executive Redline Audit Briefing
                </span>
                <h3 className="text-base font-semibold text-zinc-100 mt-1">
                  {comparison.doc1_name} <span className="text-zinc-500 font-normal">vs.</span> {comparison.doc2_name}
                </h3>
                <p className="text-xs text-zinc-400 mt-1 leading-relaxed max-w-3xl">
                  {comparison.executive_comparison || comparison.risk_delta.summary}
                </p>
              </div>

              {/* PDF Export Action */}
              <a
                href={api.getComparisonPdfUrl(comparison.id)}
                download={`DocAudit_Comparative_${comparison.doc1_id.slice(0, 6)}_vs_${comparison.doc2_id.slice(0, 6)}.pdf`}
                target="_blank"
                rel="noreferrer"
                className="bg-zinc-900 hover:bg-zinc-850 text-zinc-200 border border-zinc-750 text-xs font-medium px-3.5 py-2 rounded-lg transition flex items-center space-x-2 shrink-0 self-start lg:self-center shadow-sm"
              >
                <Download className="w-3.5 h-3.5 text-indigo-400" />
                <span>Export Redline PDF</span>
              </a>
            </div>

            {/* Score Comparison KPI Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {/* Baseline KPI */}
              <div className="bg-zinc-950 p-4 rounded-xl border border-zinc-800/80 flex flex-col justify-between">
                <span className="text-[11px] font-mono uppercase tracking-wider text-zinc-500">
                  Baseline (Doc 1)
                </span>
                <div className="mt-2 flex items-baseline space-x-2">
                  <span className="text-2xl font-bold font-mono text-zinc-200">
                    {comparison.risk_delta.doc1_score}
                  </span>
                  <span className="text-xs text-zinc-500 font-mono">/ 100</span>
                </div>
                <span className="text-[11px] font-medium text-zinc-400 mt-1">
                  Tier: {comparison.risk_delta.doc1_level}
                </span>
              </div>

              {/* Revision KPI */}
              <div className="bg-zinc-950 p-4 rounded-xl border border-zinc-800/80 flex flex-col justify-between">
                <span className="text-[11px] font-mono uppercase tracking-wider text-zinc-500">
                  Revision (Doc 2)
                </span>
                <div className="mt-2 flex items-baseline space-x-2">
                  <span className="text-2xl font-bold font-mono text-zinc-200">
                    {comparison.risk_delta.doc2_score}
                  </span>
                  <span className="text-xs text-zinc-500 font-mono">/ 100</span>
                </div>
                <span className="text-[11px] font-medium text-zinc-400 mt-1">
                  Tier: {comparison.risk_delta.doc2_level}
                </span>
              </div>

              {/* Delta KPI */}
              {(() => {
                const deltaB = getDeltaBadge(comparison.risk_delta);
                const DeltaIcon = deltaB.icon;
                return (
                  <div className={`p-4 rounded-xl border flex flex-col justify-between ${deltaB.bg}`}>
                    <span className="text-[11px] font-mono uppercase tracking-wider opacity-80">
                      Net Exposure Delta
                    </span>
                    <div className="mt-2 flex items-center space-x-2">
                      <DeltaIcon className="w-5 h-5 shrink-0" />
                      <span className="text-xl font-bold font-mono">
                        {deltaB.text}
                      </span>
                    </div>
                    <span className="text-[11px] font-semibold uppercase tracking-wider mt-1 opacity-90">
                      Verdict: {comparison.risk_delta.verdict.replace(/_/g, ' ')}
                    </span>
                  </div>
                );
              })()}
            </div>
          </div>

          {/* Metric Comparison Table (if available) */}
          {comparison.metric_comparisons && comparison.metric_comparisons.length > 0 && (
            <div className="bg-zinc-900/60 border border-zinc-850 rounded-xl p-5 backdrop-blur-md flex flex-col space-y-3">
              <h4 className="text-xs font-semibold text-zinc-300 font-mono uppercase tracking-wider">
                Key Parameters & Ratios Comparison
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-zinc-950 text-zinc-400 font-mono uppercase text-[10px] border-b border-zinc-800">
                    <tr>
                      <th className="py-2.5 px-3">Metric</th>
                      <th className="py-2.5 px-3">Baseline (v1)</th>
                      <th className="py-2.5 px-3">Revision (v2)</th>
                      <th className="py-2.5 px-3">Delta Impact</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-850">
                    {comparison.metric_comparisons.map((m, idx) => (
                      <tr key={idx} className="hover:bg-zinc-850/30 transition">
                        <td className="py-2.5 px-3 font-medium text-zinc-200">{m.metric_name}</td>
                        <td className="py-2.5 px-3 font-mono text-zinc-400">{m.doc1_value || 'N/A'}</td>
                        <td className="py-2.5 px-3 font-mono text-zinc-200">{m.doc2_value || 'N/A'}</td>
                        <td className="py-2.5 px-3 text-zinc-300 flex items-center space-x-1.5">
                          {m.is_risk_increase ? (
                            <span className="text-rose-400 font-medium">⚠️ {m.change_summary}</span>
                          ) : (
                            <span className="text-zinc-400">{m.change_summary}</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Clause Diff Analysis & Filter Chips */}
          <div className="bg-zinc-900/60 border border-zinc-850 rounded-xl p-5 backdrop-blur-md flex flex-col space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-zinc-850">
              <div className="flex items-center space-x-2">
                <ShieldAlert className="w-4 h-4 text-indigo-400" />
                <h4 className="text-sm font-semibold text-zinc-100">
                  Itemized Clause Redlines ({filteredDiffs.length} items)
                </h4>
              </div>

              {/* Filter Chips */}
              <div className="flex items-center space-x-1.5 overflow-x-auto text-[11px]">
                <button
                  onClick={() => setFilterType('ALL')}
                  className={`px-2.5 py-1 rounded-md font-medium transition ${filterType === 'ALL' ? 'bg-indigo-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200'}`}
                >
                  All ({comparison.clause_diffs?.length || 0})
                </button>
                <button
                  onClick={() => setFilterType('CRITICAL')}
                  className={`px-2.5 py-1 rounded-md font-medium transition ${filterType === 'CRITICAL' ? 'bg-rose-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:text-rose-300'}`}
                >
                  Critical Escalations
                </button>
                <button
                  onClick={() => setFilterType('ADVERSE')}
                  className={`px-2.5 py-1 rounded-md font-medium transition ${filterType === 'ADVERSE' ? 'bg-amber-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:text-amber-300'}`}
                >
                  Adverse Shifts
                </button>
                <button
                  onClick={() => setFilterType('MODIFIED')}
                  className={`px-2.5 py-1 rounded-md font-medium transition ${filterType === 'MODIFIED' ? 'bg-zinc-700 text-white' : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200'}`}
                >
                  Modified
                </button>
              </div>
            </div>

            {/* Diff Cards List */}
            <div className="space-y-4">
              {filteredDiffs.map((diff, index) => {
                const badge = getImpactBadge(diff.risk_impact);
                return (
                  <div key={index} className="bg-zinc-950 border border-zinc-800/80 rounded-xl p-4 flex flex-col space-y-3 hover:border-zinc-750 transition">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2.5 border-b border-zinc-850">
                      <div className="flex items-center space-x-2">
                        <span className="font-semibold text-xs text-zinc-200">
                          {diff.category}
                        </span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-zinc-850 text-zinc-400 border border-zinc-750 uppercase">
                          {diff.change_type}
                        </span>
                      </div>
                      <div className={`self-start sm:self-center px-2 py-0.5 rounded-full border text-[10px] font-medium flex items-center space-x-1.5 ${badge.bg}`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${badge.dot}`} />
                        <span>{badge.label}</span>
                      </div>
                    </div>

                    {/* Side by side comparison */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                      {/* Baseline */}
                      <div className="bg-zinc-900/60 p-3 rounded-lg border border-zinc-800 flex flex-col space-y-1">
                        <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-500">
                          Baseline Provision (Doc 1)
                        </span>
                        <p className="text-zinc-300 leading-relaxed italic text-xs">
                          "{diff.doc1_clause || 'No clause provision specified in baseline.'}"
                        </p>
                      </div>

                      {/* Revision */}
                      <div className="bg-zinc-900/60 p-3 rounded-lg border border-zinc-800 flex flex-col space-y-1">
                        <span className="text-[10px] font-mono uppercase tracking-wider text-indigo-400">
                          Revision Amendment (Doc 2)
                        </span>
                        <p className="text-zinc-200 leading-relaxed font-medium text-xs">
                          "{diff.doc2_clause || 'Clause deleted in revision draft.'}"
                        </p>
                      </div>
                    </div>

                    {/* Legal & Business Impact Callout */}
                    <div className="bg-zinc-900/40 p-3 rounded-lg border border-zinc-800/80 flex items-start space-x-2 text-xs">
                      <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                      <div>
                        <span className="font-semibold text-zinc-200">Commercial Exposure Analysis: </span>
                        <span className="text-zinc-400 leading-relaxed">{diff.analysis}</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Strategic Counter-Proposals */}
          {comparison.renegotiation_strategy && comparison.renegotiation_strategy.length > 0 && (
            <div className="bg-zinc-900/60 border border-zinc-850 rounded-xl p-5 backdrop-blur-md flex flex-col space-y-3">
              <h4 className="text-xs font-semibold text-zinc-200 font-mono uppercase tracking-wider flex items-center space-x-2">
                <CheckCircle className="w-4 h-4 text-emerald-400" />
                <span>Strategic Counter-Proposals & Next Steps</span>
              </h4>
              <div className="space-y-2 text-xs">
                {comparison.renegotiation_strategy.map((item, idx) => (
                  <div key={idx} className="bg-zinc-950 p-3 rounded-lg border border-zinc-800 flex items-start space-x-2.5">
                    <span className="bg-emerald-500/10 text-emerald-400 font-mono font-bold text-[11px] px-2 py-0.5 rounded border border-emerald-500/20 shrink-0">
                      STEP {idx + 1}
                    </span>
                    <span className="text-zinc-300 leading-relaxed">{item}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
