import React, { memo } from 'react';
import { ShieldCheck, ShieldAlert, AlertTriangle, Flame } from 'lucide-react';

const RiskGauge = memo(function RiskGauge({ 
  score = 0, 
  level = "LOW", 
  subMetrics = null 
}) {
  const normScore = Math.min(Math.max(score, 0), 100);

  const getLevelDetails = () => {
    switch (level?.toUpperCase()) {
      case "CRITICAL":
        return {
          stroke: "#f43f5e",
          bg: "bg-rose-500/10",
          border: "border-rose-500/20",
          text: "text-rose-400",
          label: "Critical Risk",
          icon: Flame
        };
      case "HIGH":
        return {
          stroke: "#f97316",
          bg: "bg-orange-500/10",
          border: "border-orange-500/20",
          text: "text-orange-400",
          label: "High Risk",
          icon: AlertTriangle
        };
      case "MEDIUM":
        return {
          stroke: "#f59e0b",
          bg: "bg-amber-500/10",
          border: "border-amber-500/20",
          text: "text-amber-400",
          label: "Medium Risk",
          icon: ShieldAlert
        };
      default:
        return {
          stroke: "#10b981",
          bg: "bg-emerald-500/10",
          border: "border-emerald-500/20",
          text: "text-emerald-400",
          label: "Low Risk",
          icon: ShieldCheck
        };
    }
  };

  const details = getLevelDetails();
  const Icon = details.icon;

  // SVG circular gauge math
  const radius = 38;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (normScore / 100) * circumference;

  // 4 Default / Computed Sub-Metrics
  const metrics = (subMetrics && subMetrics.length > 0) ? subMetrics : [
    { label: "Legal Exposure", value: Math.min(Math.round(normScore * 1.05), 100) },
    { label: "Financial Risk", value: Math.min(Math.round(normScore * 0.85), 100) },
    { label: "Regulatory Compliance", value: Math.min(Math.round(normScore * 0.95), 100) },
    { label: "Operational Continuity", value: Math.min(Math.round(normScore * 0.75), 100) },
  ];

  return (
    <div className="bg-zinc-900/60 border border-zinc-850 rounded-xl p-5 flex flex-col md:flex-row items-center justify-between gap-6 backdrop-blur-md">
      {/* Left: Radial SVG Meter & Global Score */}
      <div className="flex items-center space-x-5">
        <div className="relative w-24 h-24 flex items-center justify-center shrink-0">
          <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
            {/* Background track */}
            <circle
              cx="50"
              cy="50"
              r={radius}
              className="stroke-zinc-800"
              strokeWidth="7"
              fill="transparent"
            />
            {/* Animated Score stroke */}
            <circle
              cx="50"
              cy="50"
              r={radius}
              stroke={details.stroke}
              strokeWidth="7"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              fill="transparent"
              className="transition-all duration-700 ease-out"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-xl font-bold font-mono tracking-tight text-white leading-none">
              {normScore}
            </span>
            <span className="text-[10px] text-zinc-500 font-mono mt-0.5">/ 100</span>
          </div>
        </div>

        <div>
          <div className="flex items-center space-x-2">
            <span className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-md text-[11px] font-medium border ${details.bg} ${details.border} ${details.text}`}>
              <Icon className="w-3 h-3" />
              <span>{details.label}</span>
            </span>
          </div>
          <h3 className="text-sm font-semibold text-zinc-200 mt-1">Audit Risk Score</h3>
          <p className="text-xs text-zinc-500 max-w-xs leading-relaxed">
            Composite index evaluated across liability covenants, compliance clauses, and exposure factors.
          </p>
        </div>
      </div>

      {/* Right: 4 Sub-Metrics Breakdown */}
      <div className="w-full md:w-64 grid grid-cols-1 gap-2.5 border-t md:border-t-0 md:border-l border-zinc-850 pt-4 md:pt-0 md:pl-6">
        <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-500">
          Dimension Breakdown
        </span>
        {metrics.map((m, idx) => (
          <div key={idx} className="space-y-1">
            <div className="flex justify-between items-center text-[11px]">
              <span className="text-zinc-400">{m.label}</span>
              <span className="font-mono text-zinc-300">{m.value}%</span>
            </div>
            <div className="w-full bg-zinc-800 h-1 rounded-full overflow-hidden">
              <div 
                className="bg-zinc-400 h-full rounded-full transition-all duration-500"
                style={{ width: `${Math.max(m.value, 4)}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
});

export default RiskGauge;
