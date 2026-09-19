import React, { useState, useMemo, memo } from 'react';
import { 
  FileText, 
  Trash2, 
  CheckCircle2, 
  AlertCircle, 
  Loader2, 
  Scale, 
  BarChart3, 
  Settings2,
  Search,
  X
} from 'lucide-react';

const DocumentList = memo(function DocumentList({ 
  documents, 
  selectedDocId, 
  onSelectDoc, 
  onDeleteDoc 
}) {
  const [searchFilter, setSearchFilter] = useState('');

  const filteredDocs = useMemo(() => {
    if (!searchFilter.trim()) return documents;
    const query = searchFilter.toLowerCase();
    return documents.filter(d => 
      d.filename.toLowerCase().includes(query) ||
      d.id.toLowerCase().includes(query) ||
      (d.audit_type && d.audit_type.toLowerCase().includes(query))
    );
  }, [documents, searchFilter]);

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
          <span className="inline-flex items-center space-x-1 text-emerald-400 text-[10px] font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            <span>Ready</span>
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center space-x-1 text-rose-400 text-[10px] font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
            <span>Failed</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1 text-amber-400 text-[10px] font-medium">
            <Loader2 className="w-2.5 h-2.5 animate-spin" />
            <span>{doc.progress}%</span>
          </span>
        );
    }
  };

  return (
    <div className="bg-zinc-900/60 border border-zinc-850 rounded-xl overflow-hidden flex flex-col h-full backdrop-blur-md">
      {/* Sidebar Header */}
      <div className="px-3.5 py-3 border-b border-zinc-850 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <FileText className="w-3.5 h-3.5 text-zinc-400" />
          <h3 className="text-xs font-medium text-zinc-300">
            Documents
          </h3>
        </div>
        <span className="text-[11px] font-mono text-zinc-500 bg-zinc-800/80 px-2 py-0.5 rounded">
          {documents.length}
        </span>
      </div>

      {/* Real-Time Filter Search Bar */}
      <div className="p-2 border-b border-zinc-850/60">
        <div className="relative flex items-center">
          <Search className="w-3 h-3 absolute left-2.5 text-zinc-500 pointer-events-none" />
          <input
            type="text"
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            placeholder="Search documents..."
            className="w-full bg-zinc-950/80 border border-zinc-800 rounded-lg pl-8 pr-7 py-1 text-xs text-zinc-200 placeholder:text-zinc-600 focus:outline-none focus:border-zinc-700"
          />
          {searchFilter && (
            <button
              onClick={() => setSearchFilter('')}
              className="absolute right-2 text-zinc-500 hover:text-zinc-300"
            >
              <X className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>

      {/* Document Items List */}
      <div className="p-1.5 space-y-1 overflow-y-auto flex-1">
        {filteredDocs.length === 0 ? (
          <div className="p-6 text-center text-zinc-600 text-xs">
            {searchFilter ? "No matching documents found." : "No documents uploaded yet."}
          </div>
        ) : (
          filteredDocs.map((doc) => {
            const isSelected = selectedDocId === doc.id;
            return (
              <div
                key={doc.id}
                onClick={() => onSelectDoc(doc.id)}
                className={`group relative p-2.5 rounded-lg border transition cursor-pointer flex flex-col space-y-1.5 ${
                  isSelected
                    ? "bg-zinc-850/90 border-zinc-700 text-zinc-100 shadow-sm"
                    : "bg-zinc-950/40 border-zinc-850/60 hover:border-zinc-800 hover:bg-zinc-900/60 text-zinc-400 hover:text-zinc-200"
                }`}
              >
                {/* Active Indicator Strip */}
                {isSelected && (
                  <div className="absolute left-0 top-2 bottom-2 w-0.5 bg-sky-500 rounded-r" />
                )}

                <div className="flex items-start justify-between gap-1">
                  <div className="flex items-center space-x-2 min-w-0">
                    <div className="p-1 rounded bg-zinc-900 border border-zinc-800 shrink-0">
                      {getAuditTypeIcon(doc.audit_type)}
                    </div>
                    <div className="truncate">
                      <p className={`text-xs font-medium truncate ${isSelected ? "text-zinc-100" : "text-zinc-300"}`}>
                        {doc.filename}
                      </p>
                      <p className="text-[10px] text-zinc-500 font-mono">id: {doc.id}</p>
                    </div>
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteDoc(doc.id);
                    }}
                    className="opacity-0 group-hover:opacity-100 text-zinc-500 hover:text-rose-400 transition p-1 rounded hover:bg-zinc-800"
                    title="Delete document"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>

                {/* Progress bar if processing */}
                {doc.status !== 'COMPLETED' && doc.status !== 'FAILED' && (
                  <div className="w-full bg-zinc-800 h-1 rounded-full overflow-hidden">
                    <div 
                      className="bg-sky-500 h-full transition-all duration-300 rounded-full"
                      style={{ width: `${Math.max(doc.progress, 10)}%` }}
                    />
                  </div>
                )}

                <div className="flex items-center justify-between text-[10px] text-zinc-500 pt-1 border-t border-zinc-850/40 font-mono">
                  <div className="flex items-center space-x-1.5">
                    <span className="capitalize">{doc.audit_type || 'legal'}</span>
                    <span>&bull;</span>
                    <span>{doc.total_pages} {doc.total_pages === 1 ? 'pg' : 'pgs'}</span>
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
});

export default DocumentList;
