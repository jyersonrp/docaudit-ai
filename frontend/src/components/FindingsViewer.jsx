import React, { useState } from 'react';
import { 
  AlertTriangle, 
  Flame, 
  ShieldAlert, 
  CheckCircle, 
  Quote, 
  Filter, 
  Search, 
  Lightbulb, 
  ArrowRight,
  Bookmark
} from 'lucide-react';

export default function FindingsViewer({ auditData }) {
  const [selectedSeverity, setSelectedSeverity] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  if (!auditData) return null;
  const activeAudit = auditData.legal_audit || auditData.financial_audit || auditData.custom_audit;
  const findings = activeAudit?.key_findings || [];

  const filteredFindings = findings.filter(f => {
    const matchesSeverity = selectedSeverity === 'ALL' || f.severity.toUpperCase() === selectedSeverity;
    const matchesSearch = searchQuery === '' || 
      f.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.category.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSeverity && matchesSearch;
  });

  const getSeverityBadge = (severity) => {
    switch (severity.toUpperCase()) {
      case 'CRITICAL':
        return 'text-rose-400 bg-rose-500/10 border-rose-500/30';
      case 'HIGH':
        return 'text-orange-400 bg-orange-500/10 border-orange-500/30';
      case 'MEDIUM':
        return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
      default:
        return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
    }
  };

  const countBySeverity = (sev) => {
    if (sev === 'ALL') return findings.length;
    return findings.filter(f => f.severity.toUpperCase() === sev).length;
  };

  return (
    <div className="space-y-4">
      {/* Filters & Search Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-900/70 border border-slate-800 rounded-xl p-3">
        {/* Severity Tabs */}
        <div className="flex items-center space-x-1.5 overflow-x-auto">
          {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((sev) => {
            const count = countBySeverity(sev);
            return (
              <button
                key={sev}
                onClick={() => setSelectedSeverity(sev)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition flex items-center space-x-1.5 shrink-0 ${
                  selectedSeverity === sev
                    ? "bg-sky-600 text-white shadow-sm shadow-sky-600/30"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
                }`}
              >
                <span>{sev}</span>
                <span className={`text-[10px] px-1.5 py-0.2 rounded-full ${
                  selectedSeverity === sev ? "bg-white/20 text-white" : "bg-slate-800 text-slate-400"
                }`}>
                  {count}
                </span>
              </button>
            );
          })}
        </div>

        {/* Search Input */}
        <div className="relative min-w-[200px]">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search findings..."
            className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500 placeholder:text-slate-600"
          />
        </div>
      </div>

      {/* Findings List */}
      {filteredFindings.length === 0 ? (
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-8 text-center">
          <p className="text-sm text-slate-400 font-medium">No findings match the selected criteria.</p>
        </div>
      ) : (
        <div className="space-y-3.5">
          {filteredFindings.map((finding) => (
            <div 
              key={finding.id}
              className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 hover:border-slate-700/80 transition space-y-3.5"
            >
              {/* Finding Header */}
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center space-x-2.5">
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${getSeverityBadge(finding.severity)}`}>
                    {finding.severity}
                  </span>
                  <span className="text-xs font-semibold text-slate-400">
                    {finding.category}
                  </span>
                  <span className="text-slate-600 text-xs">&bull;</span>
                  <span className="text-xs text-slate-500 font-mono">{finding.id}</span>
                </div>

                {finding.page_number && (
                  <div className="flex items-center space-x-1 bg-slate-800/80 border border-slate-700/50 text-slate-300 text-[11px] font-medium px-2 py-0.5 rounded-md">
                    <Bookmark className="w-3 h-3 text-sky-400" />
                    <span>Page {finding.page_number}</span>
                  </div>
                )}
              </div>

              {/* Title & Description */}
              <div>
                <h4 className="text-sm font-bold text-white mb-1">
                  {finding.title}
                </h4>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {finding.description}
                </p>
              </div>

              {/* Impact Callout */}
              <div className="bg-slate-950/60 border border-slate-800/60 rounded-lg p-3 text-xs flex items-start space-x-2.5">
                <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold text-slate-300">Consequence / Exposure: </span>
                  <span className="text-slate-400">{finding.impact}</span>
                </div>
              </div>

              {/* Actionable Remediation Advice */}
              <div className="bg-sky-500/5 border border-sky-500/20 rounded-lg p-3 text-xs flex items-start space-x-2.5">
                <Lightbulb className="w-4 h-4 text-sky-400 shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold text-sky-300">Actionable Remediation: </span>
                  <span className="text-slate-300">{finding.recommendation}</span>
                </div>
              </div>

              {/* Verbatim Excerpt */}
              {finding.quote && (
                <div className="bg-slate-950/80 border-l-2 border-sky-500 p-3 rounded-r-lg text-xs italic text-slate-400 flex items-start space-x-2">
                  <Quote className="w-3.5 h-3.5 text-sky-400 shrink-0 mt-0.5" />
                  <span>"{finding.quote}"</span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
