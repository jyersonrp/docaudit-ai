import React, { memo } from 'react';
import { ShieldCheck, Cpu, Sparkles, Plus, BarChart3, ChevronDown, AlertTriangle } from 'lucide-react';

const Navbar = memo(function Navbar({ 
  providers, 
  selectedProvider, 
  onSelectProvider, 
  onOpenUpload, 
  onLoadSample, 
  isLoadingSample,
  systemHealth,
  healthStatus,
  onRetryHealth
}) {
  const currentProviderObj = providers.find(p => p.id === (selectedProvider || 'mock'));
  const isCurrentUnavailable = currentProviderObj && !currentProviderObj.available;

  return (
    <header className="border-b border-zinc-850 bg-zinc-950/80 backdrop-blur-xl sticky top-0 z-40 px-6 py-3">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Brand Logo & Tag */}
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-zinc-900 border border-zinc-800 flex items-center justify-center shadow-inner">
            <ShieldCheck className="w-4 h-4 text-sky-400" />
          </div>
          <div className="flex items-center space-x-2.5">
            <span className="font-semibold text-sm text-zinc-100 tracking-tight">DocAudit</span>
            <span className="bg-zinc-900 text-zinc-400 border border-zinc-800 text-[10px] font-mono px-2 py-0.5 rounded-md">
              v1.0 enterprise
            </span>
          </div>
        </div>

        {/* Center: AI Provider Selector & Health Indicator */}
        <div className="hidden md:flex items-center space-x-3">
          <div className={`flex items-center space-x-2 bg-zinc-900/90 border rounded-lg px-2.5 py-1 transition ${
            isCurrentUnavailable ? 'border-amber-500/50 bg-amber-950/10' : 'border-zinc-800/80'
          }`}>
            {isCurrentUnavailable ? (
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" title={currentProviderObj.status_message} />
            ) : (
              <Cpu className="w-3.5 h-3.5 text-zinc-400 shrink-0" />
            )}
            <span className="text-xs text-zinc-400 font-medium">Engine:</span>
            <div className="relative flex items-center">
              <select 
                value={selectedProvider || 'mock'} 
                onChange={(e) => onSelectProvider(e.target.value)}
                className={`bg-transparent text-xs font-medium appearance-none pr-5 pl-1 focus:outline-none cursor-pointer ${
                  isCurrentUnavailable ? 'text-amber-300' : 'text-zinc-200'
                }`}
              >
                {providers.map(p => {
                  let suffix = '';
                  if (!p.available) {
                    if (p.id === 'ollama') {
                      if (p.online === false) suffix = ' (Offline)';
                      else if (p.model_installed === false) suffix = ' (llama3 missing)';
                      else suffix = ' (Unavailable)';
                    } else {
                      suffix = ' (Key needed)';
                    }
                  }
                  return (
                    <option key={p.id} value={p.id} className="bg-zinc-900 text-zinc-200">
                      {p.name}{suffix}
                    </option>
                  );
                })}
              </select>
              <ChevronDown className="w-3 h-3 text-zinc-500 absolute right-0 pointer-events-none" />
            </div>
          </div>

          {healthStatus === 'healthy' && systemHealth && (
            <div 
              className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-zinc-900/90 border border-zinc-800/80 text-[11px] font-medium text-emerald-400"
              title={`Service: ${systemHealth.service} (v${systemHealth.version}) - Engine: ${systemHealth.active_provider}`}
            >
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse shadow-sm shadow-emerald-400/50" />
              <span>System Online</span>
            </div>
          )}
          {healthStatus === 'checking' && (
            <div 
              className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-zinc-900/90 border border-zinc-800/80 text-[11px] font-medium text-amber-400/90"
              title="Connecting to backend service (Render free tier spin-up takes ~30-50s on cold start)"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping" />
              <span>Connecting...</span>
            </div>
          )}
          {healthStatus === 'offline' && (
            <button 
              onClick={onRetryHealth}
              className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-red-950/20 border border-red-800/40 text-[11px] font-medium text-red-400 hover:bg-red-950/40 transition"
              title="Backend service unreachable. Click to retry connection."
            >
              <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
              <span>Offline (Retry)</span>
            </button>
          )}
        </div>

        {/* Grouped Actions: Quick Samples & Upload */}
        <div className="flex items-center space-x-2">
          <div className="flex items-center bg-zinc-900/90 border border-zinc-800/80 rounded-lg p-0.5">
            <button
              onClick={() => onLoadSample('legal')}
              disabled={isLoadingSample}
              className="text-xs text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/70 px-2.5 py-1 rounded-md font-medium transition flex items-center space-x-1.5 disabled:opacity-50"
              title="Load standard Legal Contract sample"
            >
              <Sparkles className="w-3 h-3 text-amber-400" />
              <span>Contract</span>
            </button>
            <div className="w-[1px] h-3.5 bg-zinc-800" />
            <button
              onClick={() => onLoadSample('financial')}
              disabled={isLoadingSample}
              className="text-xs text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/70 px-2.5 py-1 rounded-md font-medium transition flex items-center space-x-1.5 disabled:opacity-50"
              title="Load Financial Statements sample"
            >
              <BarChart3 className="w-3 h-3 text-emerald-400" />
              <span>Financials</span>
            </button>
          </div>

          {/* High-Contrast Modern Upload Button */}
          <button
            onClick={onOpenUpload}
            className="text-xs bg-zinc-100 hover:bg-white text-zinc-950 font-medium px-3.5 py-1.5 rounded-lg shadow-sm transition flex items-center space-x-1.5"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Upload Document</span>
          </button>
        </div>
      </div>
    </header>
  );
});

export default Navbar;
