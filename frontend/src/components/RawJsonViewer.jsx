import React, { useState, memo } from 'react';
import { Copy, Check, Code } from 'lucide-react';

const RawJsonViewer = memo(function RawJsonViewer({ data }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(data, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-zinc-950/90 border border-zinc-850 rounded-xl overflow-hidden backdrop-blur-md">
      <div className="px-4 py-2.5 bg-zinc-900/70 border-b border-zinc-850 flex items-center justify-between">
        <div className="flex items-center space-x-2 text-xs font-medium text-zinc-300">
          <Code className="w-3.5 h-3.5 text-zinc-400" />
          <span className="font-mono text-[11px] text-zinc-400">Validated Pydantic v2 JSON Schema</span>
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center space-x-1.5 text-xs text-zinc-400 hover:text-zinc-100 bg-zinc-850 hover:bg-zinc-800 px-2.5 py-1 rounded-md transition font-mono text-[11px]"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3 text-emerald-400" />
              <span className="text-emerald-400">Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3 h-3" />
              <span>Copy JSON</span>
            </>
          )}
        </button>
      </div>

      <div className="p-4 max-h-[600px] overflow-auto bg-zinc-950/60">
        <pre className="text-xs text-zinc-300 font-mono leading-relaxed whitespace-pre-wrap">
          {JSON.stringify(data, null, 2)}
        </pre>
      </div>
    </div>
  );
});

export default RawJsonViewer;
