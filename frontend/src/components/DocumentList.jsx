import React from 'react';
import { 
  FileText, 
  Trash2, 
  Clock, 
  CheckCircle2, 
  AlertCircle, 
  Loader2, 
  Scale, 
  BarChart3, 
  Settings2 
} from 'lucide-react';

export default function DocumentList({ 
  documents, 
  selectedDocId, 
  onSelectDoc, 
  onDeleteDoc 
}) {
  const getAuditTypeIcon = (type) => {
    switch (type) {
      case 'financial':
        return <BarChart3 className="w-3.5 h-3.5 text-emerald-400" />;
      case 'custom':
        return <Settings2 className="w-3.5 h-3.5 text-purple-400" />;
      default:
        return <Scale className="w-3.5 h-3.5 text-sky-400" />;
    }
  };

  const getStatusBadge = (doc) => {
    switch (doc.status) {
      case 'COMPLETED':
        return (
          <span className="flex items-center space-x-1 text-emerald-400 text-[10px] font-semibold">
            <CheckCircle2 className="w-3 h-3" />
            <span>Ready</span>
          </span>
        );
      case 'FAILED':
        return (
          <span className="flex items-center space-x-1 text-rose-400 text-[10px] font-semibold">
            <AlertCircle className="w-3 h-3" />
            <span>Failed</span>
          </span>
        );
      default:
        return (
          <span className="flex items-center space-x-1 text-amber-400 text-[10px] font-semibold">
            <Loader2 className="w-3 h-3 animate-spin" />
            <span>{doc.progress}%</span>
          </span>
        );
    }
  };

  return (
    <div className="bg-slate-900/70 border border-slate-800 rounded-2xl overflow-hidden flex flex-col h-full">
      <div className="px-4 py-3.5 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <FileText className="w-4 h-4 text-sky-400" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Document Repository
          </h3>
        </div>
        <span className="text-[11px] font-bold text-slate-400 bg-slate-800 px-2 py-0.5 rounded-full">
          {documents.length}
        </span>
      </div>

      <div className="p-2 space-y-1.5 overflow-y-auto flex-1">
        {documents.length === 0 ? (
          <div className="p-6 text-center text-slate-500 text-xs">
            No documents uploaded yet. Use the Upload or Sample buttons to get started.
          </div>
        ) : (
          documents.map((doc) => {
            const isSelected = selectedDocId === doc.id;
            return (
              <div
                key={doc.id}
                onClick={() => onSelectDoc(doc.id)}
                className={`group p-3 rounded-xl border transition cursor-pointer flex flex-col space-y-2 ${
                  isSelected
                    ? "bg-sky-500/10 border-sky-500/50 shadow-sm"
                    : "bg-slate-950/40 border-slate-800/60 hover:border-slate-700 hover:bg-slate-950/80"
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-2 min-w-0">
                    <div className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 shrink-0">
                      {getAuditTypeIcon(doc.audit_type)}
                    </div>
                    <div className="truncate">
                      <p className={`text-xs font-semibold truncate ${isSelected ? "text-white" : "text-slate-200"}`}>
                        {doc.filename}
                      </p>
                      <p className="text-[10px] text-slate-500 font-mono">ID: {doc.id}</p>
                    </div>
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteDoc(doc.id);
                    }}
                    className="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-rose-400 transition p-1 rounded"
                    title="Delete document"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>

                {/* Progress bar if processing */}
                {doc.status !== 'COMPLETED' && doc.status !== 'FAILED' && (
                  <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                    <div 
                      className="bg-sky-500 h-full transition-all duration-300 rounded-full"
                      style={{ width: `${Math.max(doc.progress, 10)}%` }}
                    />
                  </div>
                )}

                <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1 border-t border-slate-800/40">
                  <div className="flex items-center space-x-2">
                    <span className="capitalize">{doc.audit_type || 'legal'}</span>
                    <span>&bull;</span>
                    <span>{doc.total_pages} {doc.total_pages === 1 ? 'page' : 'pages'}</span>
                  </div>
                  <div>{getStatusBadge(doc)}</div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
