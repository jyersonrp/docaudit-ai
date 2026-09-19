import React, { useState, useMemo, memo } from 'react';
import { 
  AlertTriangle, 
  Lightbulb, 
  Quote, 
  Search, 
  Bookmark, 
  ChevronDown, 
  ChevronUp, 
  X,
  Filter
} from 'lucide-react';

const FindingCard = memo(function FindingCard({ finding }) {
  const [isExpanded, setIsExpanded] = useState(true);

  const getSeverityBadge = (severity) => {
    switch (severity?.toUpperCase()) {
      case 'CRITICAL':
        return 'text-rose-400 bg-rose-500/10 border-rose-500/20';
      case 'HIGH':
        return 'text-orange-400 bg-orange-500/10 border-orange-500/20';
      case 'MEDIUM':
        return 'text-amber-400 bg-amber-500/10 border-amber-500/20';
      default:
        return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
    }
  };

  return (
    <div className="bg-zinc-900/70 border border-zinc-850 rounded-xl overflow-hidden transition hover:border-zinc-700/85">
      {/* Header bar */}
      <div 
        onClick={() => setIsExpanded(prev => !prev)}
        className="p-4 cursor-pointer flex items-center justify-between gap-3 select-none bg-zinc-900/50 hover:bg-zinc-850/50 transition"
      >
        <div className="flex items-center space-x-2.5 min-w-0">
          <span className={`text-[10px] font-mono font-medium px-2 py-0.5 rounded border shrink-0 ${getSeverityBadge(finding.severity)}`}>
            {finding.severity}
          </span>
          <span className="text-xs font-semibold text-zinc-100 truncate">
            {finding.title}
          </span>
          <span className="text-zinc-600 text-xs hidden sm:inline">&bull;</span>
          <span className="text-[11px] text-zinc-500 font-mono hidden sm:inline">{finding.category}</span>
        </div>

        <div className="flex items-center space-x-2 shrink-0">
          {finding.page_number && (
            <div className="flex items-center space-x-1 bg-zinc-950 border border-zinc-800 text-zinc-400 text-[10px] font-mono px-2 py-0.5 rounded">
              <Bookmark className="w-3 h-3 text-sky-400" />
              <span>pg {finding.page_number}</span>
            </div>
          )}
          <button className="text-zinc-500 hover:text-zinc-300 p-1">
            {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Expandable Body */}
      {isExpanded && (
        <div className="px-5 pb-5 pt-1 space-y-3.5 border-t border-zinc-850/60">
          {/* Finding Description */}
          <p className="text-xs text-zinc-300 leading-relaxed pt-2">
            {finding.description}
          </p>

          {/* Impact & Consequence */}
          <div className="bg-zinc-950/60 border border-zinc-850/80 rounded-lg p-3 text-xs flex items-start space-x-2.5">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-medium text-zinc-200">Exposure Impact: </span>
              <span className="text-zinc-400 leading-relaxed">{finding.impact}</span>
            </div>
          </div>

          {/* Actionable Remediation Advice */}
          <div className="bg-sky-500/5 border border-sky-500/20 rounded-lg p-3 text-xs flex items-start space-x-2.5">
            <Lightbulb className="w-4 h-4 text-sky-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-medium text-sky-300">Actionable Remediation: </span>
              <span className="text-zinc-300 leading-relaxed">{finding.recommendation}</span>
            </div>
          </div>

          {/* Verbatim Excerpt */}
          {finding.quote && (
            <div className="bg-zinc-950/80 border-l-2 border-sky-500/80 px-3.5 py-2.5 rounded-r-lg text-xs italic text-zinc-400 flex items-start space-x-2">
              <Quote className="w-3.5 h-3.5 text-sky-400 shrink-0 mt-0.5" />
              <span className="leading-relaxed">"{finding.quote}"</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
});

const FindingsViewer = memo(function FindingsViewer({ auditData }) {
  const [selectedSeverity, setSelectedSeverity] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  if (!auditData) return null;
  const activeAudit = auditData.legal_audit || auditData.financial_audit || auditData.custom_audit;
  const findings = activeAudit?.key_findings || [];

  const filteredFindings = useMemo(() => {
    return findings.filter(f => {
      const matchesSeverity = selectedSeverity === 'ALL' || f.severity.toUpperCase() === selectedSeverity;
      const matchesSearch = searchQuery === '' || 
        f.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        f.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        f.category.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesSeverity && matchesSearch;
    });
  }, [findings, selectedSeverity, searchQuery]);

  const countBySeverity = (sev) => {
    if (sev === 'ALL') return findings.length;
    return findings.filter(f => f.severity.toUpperCase() === sev).length;
  };

  return (
    <div className="space-y-4">
      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-zinc-900/60 border border-zinc-850 rounded-xl p-2.5 backdrop-blur-md">
        {/* Severity Tabs */}
        <div className="flex items-center space-x-1 overflow-x-auto">
          {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((sev) => {
            const count = countBySeverity(sev);
            const isSelected = selectedSeverity === sev;
            return (
              <button
                key={sev}
                onClick={() => setSelectedSeverity(sev)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition flex items-center space-x-1.5 shrink-0 ${
                  isSelected
                    ? "bg-zinc-100 text-zinc-950 shadow-sm"
                    : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/60"
                }`}
              >
                <span>{sev}</span>
                <span className={`text-[10px] font-mono px-1.5 py-0.2 rounded-full ${
                  isSelected ? "bg-zinc-300 text-zinc-950 font-bold" : "bg-zinc-800 text-zinc-400"
                }`}>
                  {count}
                </span>
              </button>
            );
          })}
        </div>

        {/* Search Input */}
        <div className="relative min-w-[220px]">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter findings..."
            className="w-full bg-zinc-950/80 border border-zinc-800 rounded-lg pl-8 pr-7 py-1.5 text-xs text-zinc-200 placeholder:text-zinc-600 focus:outline-none focus:border-zinc-700"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300"
            >
              <X className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>

      {/* Findings Accordion List */}
      {filteredFindings.length === 0 ? (
        <div className="bg-zinc-900/40 border border-zinc-850 rounded-xl p-10 text-center">
          <p className="text-xs text-zinc-500">No findings match the selected criteria.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredFindings.map((finding, idx) => (
            <FindingCard key={finding.id || `finding-${idx}`} finding={finding} />
          ))}
        </div>
      )}
    </div>
  );
});

export default FindingsViewer;
