import React from 'react';
import { ShieldCheck, ShieldAlert, AlertTriangle, Flame } from 'lucide-react';

export default function RiskGauge({ score = 0, level = "LOW" }) {
  const getBadgeConfig = () => {
    switch (level.toUpperCase()) {
      case "CRITICAL":
        return {
          bg: "bg-rose-500/10",
          border: "border-rose-500/30",
          text: "text-rose-400",
          barColor: "bg-rose-500",
          icon: Flame,
          label: "Critical Risk"
        };
      case "HIGH":
        return {
          bg: "bg-orange-500/10",
          border: "border-orange-500/30",
          text: "text-orange-400",
          barColor: "bg-orange-500",
          icon: AlertTriangle,
          label: "High Risk"
        };
      case "MEDIUM":
        return {
          bg: "bg-amber-500/10",
          border: "border-amber-500/30",
          text: "text-amber-400",
          barColor: "bg-amber-500",
          icon: ShieldAlert,
          label: "Medium Risk"
        };
      default:
        return {
          bg: "bg-emerald-500/10",
          border: "border-emerald-500/30",
          text: "text-emerald-400",
          barColor: "bg-emerald-500",
          icon: ShieldCheck,
          label: "Low Risk"
        };
    }
  };

  const config = getBadgeConfig();
  const IconComponent = config.icon;

  return (
    <div className={`p-4 rounded-xl border ${config.bg} ${config.border} flex items-center justify-between`}>
      <div className="flex items-center space-x-3.5">
        <div className={`w-12 h-12 rounded-xl border ${config.border} bg-slate-900/60 flex items-center justify-center shrink-0`}>
          <IconComponent className={`w-6 h-6 ${config.text}`} />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <span className={`text-xs font-bold uppercase tracking-wider ${config.text}`}>
              {config.label}
            </span>
            <span className="text-slate-500 text-xs">&bull;</span>
            <span className="text-xs text-slate-400 font-medium">Global Assessment</span>
          </div>
          <div className="flex items-baseline space-x-1.5 mt-0.5">
            <span className="text-2xl font-black text-white">{score}</span>
            <span className="text-xs font-medium text-slate-400">/ 100</span>
          </div>
        </div>
      </div>

      {/* Mini Progress Bar */}
      <div className="w-32 hidden sm:block">
        <div className="flex justify-between text-[10px] text-slate-400 mb-1">
          <span>0 (Safe)</span>
          <span>100 (Severe)</span>
        </div>
        <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
          <div 
            className={`h-full ${config.barColor} transition-all duration-500 rounded-full`}
            style={{ width: `${Math.max(score, 5)}%` }}
          />
        </div>
      </div>
    </div>
  );
}
