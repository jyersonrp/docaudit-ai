import React from 'react';
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
  Settings2
} from 'lucide-react';

export default function ExecutiveOverview({ auditData }) {
  if (!auditData) return null;

  const { audit_type, legal_audit, financial_audit, custom_audit } = auditData;
  const activeAudit = legal_audit || financial_audit || custom_audit;
  if (!activeAudit) return null;

  return (
    <div className="space-y-6">
      {/* Top Banner: Risk Gauge & Model Info */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="md:col-span-2">
          <RiskGauge 
            score={activeAudit.overall_risk_score} 
            level={activeAudit.overall_risk_level} 
          />
        </div>
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex flex-col justify-center">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            Audit Classification
          </span>
          <div className="flex items-center space-x-2 mt-1">
            <span className="text-base font-bold text-white uppercase">{audit_type}</span>
            <span className="bg-slate-800 text-sky-400 text-[10px] font-semibold px-2 py-0.5 rounded">
              Pydantic v2
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Processed via <b className="text-slate-200">{auditData.provider_used}</b> ({auditData.model_used})
          </p>
        </div>
      </div>

      {/* Executive Briefing */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5">
        <h4 className="text-xs font-bold uppercase tracking-wider text-sky-400 mb-2 flex items-center space-x-2">
          <Shield className="w-4 h-4" />
          <span>Executive Summary</span>
        </h4>
        <p className="text-sm text-slate-300 leading-relaxed">
          {activeAudit.executive_summary}
        </p>
      </div>

      {/* Structured Core Parameters Grid */}
      {legal_audit && (
        <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-4 flex items-center space-x-2">
            <Scale className="w-4 h-4 text-sky-400" />
            <span>Key Contractual Parameters</span>
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="bg-slate-950/50 border border-slate-800/80 rounded-lg p-3.5">
              <div className="flex items-center space-x-2 text-slate-400 text-xs mb-1">
                <Building2 className="w-3.5 h-3.5 text-sky-400" />
                <span>Identified Parties</span>
              </div>
              <p className="text-xs font-semibold text-white">
                {legal_audit.parties?.join(' & ') || 'N/A'}
              </p>
            </div>

            <div className="bg-slate-950/50 border border-slate-800/80 rounded-lg p-3.5">
              <div className="flex items-center space-x-2 text-slate-400 text-xs mb-1">
                <Scale className="w-3.5 h-3.5 text-sky-400" />
                <span>Governing Law & Venue</span>
              </div>
              <p className="text-xs font-semibold text-white">
                {legal_audit.governing_law || 'N/A'}
              </p>
            </div>

            <div className="bg-slate-950/50 border border-slate-800/80 rounded-lg p-3.5">
              <div className="flex items-center space-x-2 text-slate-400 text-xs mb-1">
                <Calendar className="w-3.5 h-3.5 text-sky-400" />
                <span>Effective Term</span>
              </div>
              <p className="text-xs font-semibold text-white">
                {legal_audit.effective_date || 'N/A'} to {legal_audit.expiration_date || 'N/A'}
              </p>
            </div>

            <div className="bg-slate-950/50 border border-slate-800/80 rounded-lg p-3.5">
              <div className="flex items-center space-x-2 text-slate-400 text-xs mb-1">
                <Clock className="w-3.5 h-3.5 text-sky-400" />
                <span>Termination Notice</span>
              </div>
              <p className="text-xs font-semibold text-white">
                {legal_audit.termination_notice_period || 'N/A'}
              </p>
            </div>

            <div className="bg-slate-950/50 border border-slate-800/80 rounded-lg p-3.5">
              <div className="flex items-center space-x-2 text-slate-400 text-xs mb-1">
                <DollarSign className="w-3.5 h-3.5 text-emerald-400" />
                <span>Liability Cap</span>
              </div>
              <p className="text-xs font-semibold text-white">
                {legal_audit.liability_cap || 'N/A'}
              </p>
            </div>

            <div className="bg-slate-950/50 border border-slate-800/80 rounded-lg p-3.5">
              <div className="flex items-center space-x-2 text-slate-400 text-xs mb-1">
                <Shield className="w-3.5 h-3.5 text-amber-400" />
                <span>Indemnification Scope</span>
              </div>
              <p className="text-xs font-semibold text-white truncate">
                {legal_audit.indemnification_scope || 'Standard'}
              </p>
            </div>
          </div>
        </div>
      )}

      {financial_audit && (
        <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-4 flex items-center space-x-2">
            <TrendingUp className="w-4 h-4 text-emerald-400" />
            <span>Audited Financial Statements Metrics</span>
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="bg-slate-950/50 border border-slate-800/80 rounded-lg p-3.5">
              <div className="flex items-center space-x-2 text-slate-400 text-xs mb-1">
                <Building2 className="w-3.5 h-3.5 text-sky-400" />
                <span>Company & Period</span>
              </div>
              <p className="text-xs font-semibold text-white">
                {financial_audit.company_name || 'N/A'} ({financial_audit.reporting_period || 'N/A'})
              </p>
            </div>

            <div className="bg-slate-950/50 border border-slate-800/80 rounded-lg p-3.5">
              <div className="flex items-center space-x-2 text-slate-400 text-xs mb-1">
                <DollarSign className="w-3.5 h-3.5 text-emerald-400" />
                <span>Total Recorded Revenue</span>
              </div>
              <p className="text-base font-bold text-emerald-400">
                {financial_audit.total_revenue || 'N/A'}
              </p>
            </div>

            <div className="bg-slate-950/50 border border-slate-800/80 rounded-lg p-3.5">
              <div className="flex items-center space-x-2 text-slate-400 text-xs mb-1">
                <Activity className="w-3.5 h-3.5 text-sky-400" />
                <span>Net Income & Margins</span>
              </div>
              <p className="text-xs font-semibold text-white">
                {financial_audit.net_income || 'N/A'} (Margin: {financial_audit.operating_margin || 'N/A'})
              </p>
            </div>

            <div className="bg-slate-950/50 border border-slate-800/80 rounded-lg p-3.5">
              <div className="flex items-center space-x-2 text-slate-400 text-xs mb-1">
                <FileCheck2 className="w-3.5 h-3.5 text-indigo-400" />
                <span>Auditor's Opinion</span>
              </div>
              <p className="text-xs font-semibold text-white">
                {financial_audit.auditor_opinion || 'Unqualified'}
              </p>
            </div>

            <div className="bg-slate-950/50 border border-slate-800/80 rounded-lg p-3.5">
              <div className="flex items-center space-x-2 text-slate-400 text-xs mb-1">
                <Scale className="w-3.5 h-3.5 text-amber-400" />
                <span>Debt-to-Equity</span>
              </div>
              <p className="text-xs font-semibold text-white">
                {financial_audit.debt_to_equity || '0.27x'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Custom Audit Extracted Criteria Grid */}
      {custom_audit && custom_audit.extracted_fields && Object.keys(custom_audit.extracted_fields).length > 0 && (
        <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-4 flex items-center space-x-2">
            <Settings2 className="w-4 h-4 text-purple-400" />
            <span>Extracted Custom Verification Criteria ({custom_audit.audit_name})</span>
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(custom_audit.extracted_fields).map(([key, val], idx) => (
              <div key={idx} className="bg-slate-950/50 border border-slate-800/80 rounded-lg p-3.5">
                <span className="text-slate-400 text-xs block mb-1 font-medium capitalize">
                  {key.replace(/_/g, ' ')}
                </span>
                <p className="text-xs font-semibold text-white truncate">
                  {typeof val === 'object' ? JSON.stringify(val) : String(val)}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Risk Matrix Dimensions Grid */}
      {activeAudit.risk_matrix && activeAudit.risk_matrix.length > 0 && (
        <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-4 flex items-center space-x-2">
            <Activity className="w-4 h-4 text-sky-400" />
            <span>Risk Dimensions Matrix</span>
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {activeAudit.risk_matrix.map((r, idx) => {
              const badgeCol = r.level === 'LOW' 
                ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
                : r.level === 'MEDIUM'
                  ? 'text-amber-400 bg-amber-500/10 border-amber-500/20'
                  : 'text-rose-400 bg-rose-500/10 border-rose-500/20';

              return (
                <div key={idx} className="bg-slate-950/50 border border-slate-800/80 rounded-xl p-4 flex flex-col justify-between">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold text-slate-200">{r.dimension}</span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${badgeCol}`}>
                      {r.level} ({r.score}/100)
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">{r.summary}</p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Compliance Checklist */}
      {activeAudit.compliance_checklist && Object.keys(activeAudit.compliance_checklist).length > 0 && (
        <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>Regulatory & Operational Checklist</span>
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {Object.entries(activeAudit.compliance_checklist).map(([rule, passed], idx) => (
              <div 
                key={idx}
                className="flex items-center space-x-2.5 p-2.5 rounded-lg bg-slate-950/40 border border-slate-800/60 text-xs"
              >
                {passed ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
                )}
                <span className={passed ? "text-slate-200" : "text-rose-300 font-medium"}>
                  {rule}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
