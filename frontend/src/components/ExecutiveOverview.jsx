import React, { useState, memo } from 'react';
import RiskGauge from './RiskGauge';
import { 
  Building2, 
  Scale, 
  Calendar, 
  Clock, 
  DollarSign, 
  AlertCircle, 
  CheckCircle2, 
  Shield, 
  Activity, 
  TrendingUp,
  FileCheck2,
  Settings2,
  Copy,
  Check
} from 'lucide-react';

const ParameterCard = memo(function ParameterCard({ icon: Icon, label, value, iconColor = "text-sky-400" }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (!value || value === 'N/A') return;
    navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className="group relative bg-zinc-950/50 border border-zinc-850/80 hover:border-zinc-700/80 rounded-lg p-3.5 transition flex flex-col justify-between">
      <div className="flex items-center justify-between text-zinc-400 text-xs mb-1.5">
        <div className="flex items-center space-x-1.5 font-mono text-[11px] text-zinc-500 uppercase tracking-wider">
          <Icon className={`w-3.5 h-3.5 ${iconColor}`} />
          <span>{label}</span>
        </div>
        <button
          onClick={handleCopy}
          className="opacity-0 group-hover:opacity-100 transition p-1 text-zinc-500 hover:text-zinc-200 rounded hover:bg-zinc-800"
          title="Copy to clipboard"
        >
          {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
        </button>
      </div>
      <p className="text-xs font-medium text-zinc-200 truncate">
        {value || 'N/A'}
      </p>
    </div>
  );
});

const ExecutiveOverview = memo(function ExecutiveOverview({ auditData }) {
  if (!auditData) return null;

  const { audit_type, legal_audit, financial_audit, custom_audit } = auditData;
  const activeAudit = legal_audit || financial_audit || custom_audit;
  if (!activeAudit) return null;

  // Extract sub-metrics from risk matrix if available
  const subMetrics = activeAudit.risk_matrix?.map(r => ({
    label: r.dimension,
    value: r.score
  }));

  return (
    <div className="space-y-5">
      {/* Top Banner: SVG Radial Risk Gauge & Classification */}
      <RiskGauge 
        score={activeAudit.overall_risk_score} 
        level={activeAudit.overall_risk_level}
        subMetrics={subMetrics}
      />

      {/* Model & Classification Metadata Bar */}
      <div className="bg-zinc-900/40 border border-zinc-850 rounded-xl px-4 py-3 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center space-x-2">
          <span className="text-zinc-500 font-mono text-[11px]">AUDIT TYPE:</span>
          <span className="font-semibold text-zinc-200 uppercase tracking-wide bg-zinc-800/80 px-2 py-0.5 rounded text-[11px]">
            {audit_type}
          </span>
          <span className="text-zinc-600">&bull;</span>
          <span className="text-zinc-400 font-mono text-[11px]">Schema: Pydantic v2</span>
        </div>
        <div className="flex items-center space-x-2 font-mono text-[11px] text-zinc-400">
          <span>Engine:</span>
          <span className="text-zinc-200 font-semibold">{auditData.provider_used}</span>
          <span className="text-zinc-600">({auditData.model_used})</span>
        </div>
      </div>

      {/* Executive Briefing */}
      <div className="bg-zinc-900/60 border border-zinc-850 rounded-xl p-5 backdrop-blur-sm">
        <h4 className="text-xs font-mono font-semibold uppercase tracking-wider text-zinc-400 mb-2 flex items-center space-x-2">
          <Shield className="w-3.5 h-3.5 text-sky-400" />
          <span>Executive Synthesis</span>
        </h4>
        <p className="text-xs text-zinc-300 leading-relaxed">
          {activeAudit.executive_summary}
        </p>
      </div>

      {/* Structured Core Parameters Grid for Legal Contracts */}
      {legal_audit && (
        <div className="bg-zinc-900/60 border border-zinc-850 rounded-xl p-5 backdrop-blur-sm">
          <h4 className="text-xs font-mono font-semibold uppercase tracking-wider text-zinc-400 mb-3 flex items-center space-x-2">
            <Scale className="w-3.5 h-3.5 text-sky-400" />
            <span>Key Contractual Covenants</span>
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            <ParameterCard 
              icon={Building2} 
              label="Identified Parties" 
              value={legal_audit.parties?.join(' & ') || 'N/A'} 
            />
            <ParameterCard 
              icon={Scale} 
              label="Governing Jurisdiction" 
              value={legal_audit.governing_law || 'N/A'} 
            />
            <ParameterCard 
              icon={Calendar} 
              label="Effective Term" 
              value={`${legal_audit.effective_date || 'N/A'} to ${legal_audit.expiration_date || 'N/A'}`} 
            />
            <ParameterCard 
              icon={Clock} 
              label="Termination Notice" 
              value={legal_audit.termination_notice_period || 'N/A'} 
            />
            <ParameterCard 
              icon={DollarSign} 
              label="Liability Cap" 
              value={legal_audit.liability_cap || 'N/A'} 
              iconColor="text-emerald-400"
            />
            <ParameterCard 
              icon={Shield} 
              label="Indemnification Scope" 
              value={legal_audit.indemnification_scope || 'Standard'} 
              iconColor="text-amber-400"
            />
          </div>
        </div>
      )}

      {/* Structured Core Parameters Grid for Financial Reports */}
      {financial_audit && (
        <div className="bg-zinc-900/60 border border-zinc-850 rounded-xl p-5 backdrop-blur-sm">
          <h4 className="text-xs font-mono font-semibold uppercase tracking-wider text-zinc-400 mb-3 flex items-center space-x-2">
            <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
            <span>Financial & Balance Sheet Parameters</span>
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            <ParameterCard 
              icon={Building2} 
              label="Entity & Period" 
              value={`${financial_audit.company_name || 'N/A'} (${financial_audit.reporting_period || 'N/A'})`} 
            />
            <ParameterCard 
              icon={DollarSign} 
              label="Total Revenue" 
              value={financial_audit.total_revenue || 'N/A'} 
              iconColor="text-emerald-400"
            />
            <ParameterCard 
              icon={Activity} 
              label="Net Income & Margin" 
              value={`${financial_audit.net_income || 'N/A'} (Margin: ${financial_audit.operating_margin || 'N/A'})`} 
            />
            <ParameterCard 
              icon={FileCheck2} 
              label="Auditor Opinion" 
              value={financial_audit.auditor_opinion || 'Unqualified'} 
              iconColor="text-indigo-400"
            />
            <ParameterCard 
              icon={Scale} 
              label="Debt-to-Equity Ratio" 
              value={financial_audit.debt_to_equity || '0.27x'} 
              iconColor="text-amber-400"
            />
          </div>
        </div>
      )}

      {/* Custom Audit Extracted Criteria Grid */}
      {custom_audit && custom_audit.extracted_fields && Object.keys(custom_audit.extracted_fields).length > 0 && (
        <div className="bg-zinc-900/60 border border-zinc-850 rounded-xl p-5 backdrop-blur-sm">
          <h4 className="text-xs font-mono font-semibold uppercase tracking-wider text-zinc-400 mb-3 flex items-center space-x-2">
            <Settings2 className="w-3.5 h-3.5 text-purple-400" />
            <span>Custom Verification Criteria ({custom_audit.audit_name})</span>
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {Object.entries(custom_audit.extracted_fields).map(([key, val], idx) => (
              <ParameterCard 
                key={idx}
                icon={Settings2}
                label={key.replace(/_/g, ' ')}
                value={typeof val === 'object' ? JSON.stringify(val) : String(val)}
                iconColor="text-purple-400"
              />
            ))}
          </div>
        </div>
      )}

      {/* Risk Matrix Dimensions Grid */}
      {activeAudit.risk_matrix && activeAudit.risk_matrix.length > 0 && (
        <div className="bg-zinc-900/60 border border-zinc-850 rounded-xl p-5 backdrop-blur-sm">
          <h4 className="text-xs font-mono font-semibold uppercase tracking-wider text-zinc-400 mb-3 flex items-center space-x-2">
            <Activity className="w-3.5 h-3.5 text-sky-400" />
            <span>Risk Dimensions Matrix</span>
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {activeAudit.risk_matrix.map((r, idx) => {
              const badgeCol = r.level === 'LOW' 
                ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
                : r.level === 'MEDIUM'
                  ? 'text-amber-400 bg-amber-500/10 border-amber-500/20'
                  : 'text-rose-400 bg-rose-500/10 border-rose-500/20';

              return (
                <div key={idx} className="bg-zinc-950/50 border border-zinc-850/80 rounded-lg p-4 flex flex-col justify-between space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-zinc-200">{r.dimension}</span>
                    <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${badgeCol}`}>
                      {r.level} ({r.score}/100)
                    </span>
                  </div>
                  {/* Micro Progress Bar */}
                  <div className="w-full bg-zinc-850 h-1 rounded-full overflow-hidden">
                    <div 
                      className={`h-full rounded-full transition-all duration-500 ${
                        r.level === 'LOW' ? 'bg-emerald-400' : r.level === 'MEDIUM' ? 'bg-amber-400' : 'bg-rose-400'
                      }`}
                      style={{ width: `${Math.max(r.score, 5)}%` }}
                    />
                  </div>
                  <p className="text-xs text-zinc-400 leading-relaxed">{r.summary}</p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Compliance Checklist */}
      {activeAudit.compliance_checklist && Object.keys(activeAudit.compliance_checklist).length > 0 && (
        <div className="bg-zinc-900/60 border border-zinc-850 rounded-xl p-5 backdrop-blur-sm">
          <h4 className="text-xs font-mono font-semibold uppercase tracking-wider text-zinc-400 mb-3 flex items-center space-x-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>Compliance & Covenant Verification</span>
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {Object.entries(activeAudit.compliance_checklist).map(([rule, passed], idx) => (
              <div 
                key={idx}
                className="flex items-center space-x-2.5 p-2.5 rounded-lg bg-zinc-950/40 border border-zinc-850/60 text-xs"
              >
                {passed ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                ) : (
                  <AlertCircle className="w-3.5 h-3.5 text-rose-400 shrink-0" />
                )}
                <span className={passed ? "text-zinc-200" : "text-rose-300 font-medium"}>
                  {rule}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
});

export default ExecutiveOverview;
