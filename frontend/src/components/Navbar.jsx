import React from 'react';
import { ShieldAlert, FileText, Cpu, Sparkles, Plus, RefreshCw, BarChart3 } from 'lucide-react';

export default function Navbar({ 
  providers, 
  selectedProvider, 
  onSelectProvider, 
  onOpenUpload, 
  onLoadSample, 
  isLoadingSample,
  systemHealth
}) {
  return (
    <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur-md sticky top-0 z-40 px-6 py-3.5">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-sky-500/20">
            <ShieldAlert className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg text-white tracking-tight">DocAudit</span>
              <span className="bg-sky-500/10 text-sky-400 border border-sky-500/20 text-xs font-semibold px-2 py-0.5 rounded-full">
                AI Engine
              </span>
            </div>
            <p className="text-xs text-slate-400">Asynchronous Document Audit & Extraction</p>
          </div>
        </div>

        {/* Center: AI Provider Selector & Health Indicator */}
        <div className="hidden md:flex items-center space-x-3">
          <div className="flex items-center space-x-2 bg-slate-900 border border-slate-800 rounded-lg p-1">
            <div className="flex items-center space-x-1.5 px-2 text-xs font-medium text-slate-400">
              <Cpu className="w-3.5 h-3.5 text-sky-400" />
              <span>AI Provider:</span>
            </div>
            <select 
              value={selectedProvider || 'mock'} 
              onChange={(e) => onSelectProvider(e.target.value)}
              className="bg-slate-950 text-slate-200 text-xs border border-slate-700/60 rounded px-2.5 py-1 focus:outline-none focus:border-sky-500 font-medium cursor-pointer"
            >
              {providers.map(p => (
                <option key={p.id} value={p.id}>
                  {p.name} {p.available ? '' : '(Key needed)'}
                </option>
              ))}
            </select>
          </div>

          {systemHealth && (
            <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-[11px] font-semibold text-emerald-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="capitalize">{systemHealth.status}</span>
            </div>
          )}
        </div>

        {/* Quick Sample & Upload Buttons */}
        <div className="flex items-center space-x-2">
          {/* Load Sample Dropdown/Buttons */}
          <button
            onClick={() => onLoadSample('legal')}
            disabled={isLoadingSample}
            className="text-xs bg-slate-800/80 hover:bg-slate-800 text-slate-200 border border-slate-700/60 px-3 py-2 rounded-lg font-medium transition flex items-center space-x-1.5 disabled:opacity-50"
            title="Load standard Legal Contract sample for instant testing"
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            <span>Sample Contract</span>
          </button>

          <button
            onClick={() => onLoadSample('financial')}
            disabled={isLoadingSample}
            className="text-xs bg-slate-800/80 hover:bg-slate-800 text-slate-200 border border-slate-700/60 px-3 py-2 rounded-lg font-medium transition flex items-center space-x-1.5 disabled:opacity-50"
            title="Load Financial Statements sample for instant testing"
          >
            <BarChart3 className="w-3.5 h-3.5 text-emerald-400" />
            <span>Sample Financials</span>
          </button>

          {/* Upload Button */}
          <button
            onClick={onOpenUpload}
            className="text-xs bg-sky-600 hover:bg-sky-500 text-white font-semibold px-3.5 py-2 rounded-lg shadow-sm shadow-sky-600/30 transition flex items-center space-x-1.5"
          >
            <Plus className="w-4 h-4" />
            <span>Upload Document</span>
          </button>
        </div>
      </div>
    </header>
  );
}
