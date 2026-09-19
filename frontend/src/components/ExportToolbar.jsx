import React, { useState, memo } from 'react';
import { FileText, FileCode, FileDown, Loader2, Check } from 'lucide-react';
import { api } from '../services/api';

const ExportToolbar = memo(function ExportToolbar({ docId, filename }) {
  const [downloadingFormat, setDownloadingFormat] = useState(null);
  const [downloadedFormat, setDownloadedFormat] = useState(null);

  const handleDownload = async (format) => {
    setDownloadingFormat(format);
    try {
      const url = api.getExportUrl(docId, format);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `DocAudit_${format.toUpperCase()}_${filename || docId}`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      setDownloadedFormat(format);
      setTimeout(() => setDownloadedFormat(null), 2000);
    } catch (e) {
      console.error("Download failed:", e);
    } finally {
      setTimeout(() => setDownloadingFormat(null), 800);
    }
  };

  return (
    <div className="flex items-center space-x-1.5">
      <span className="text-[11px] font-mono text-zinc-500 mr-1 hidden sm:inline">
        Export:
      </span>

      {/* PDF Button */}
      <button
        onClick={() => handleDownload('pdf')}
        disabled={downloadingFormat === 'pdf'}
        className="bg-zinc-900/90 hover:bg-zinc-850 text-zinc-300 border border-zinc-800 hover:border-zinc-700 text-xs font-medium px-2.5 py-1.5 rounded-lg transition flex items-center space-x-1.5 shadow-sm"
        title="Download executive PDF report"
      >
        {downloadingFormat === 'pdf' ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin text-rose-400" />
        ) : downloadedFormat === 'pdf' ? (
          <Check className="w-3.5 h-3.5 text-emerald-400" />
        ) : (
          <FileDown className="w-3.5 h-3.5 text-rose-400" />
        )}
        <span>PDF</span>
      </button>

      {/* Markdown Button */}
      <button
        onClick={() => handleDownload('markdown')}
        disabled={downloadingFormat === 'markdown'}
        className="bg-zinc-900/90 hover:bg-zinc-850 text-zinc-300 border border-zinc-800 hover:border-zinc-700 text-xs font-medium px-2.5 py-1.5 rounded-lg transition flex items-center space-x-1.5 shadow-sm"
        title="Download formatted Markdown summary"
      >
        {downloadingFormat === 'markdown' ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin text-sky-400" />
        ) : downloadedFormat === 'markdown' ? (
          <Check className="w-3.5 h-3.5 text-emerald-400" />
        ) : (
          <FileText className="w-3.5 h-3.5 text-sky-400" />
        )}
        <span>Markdown</span>
      </button>

      {/* JSON Button */}
      <button
        onClick={() => handleDownload('json')}
        disabled={downloadingFormat === 'json'}
        className="bg-zinc-900/90 hover:bg-zinc-850 text-zinc-300 border border-zinc-800 hover:border-zinc-700 text-xs font-medium px-2.5 py-1.5 rounded-lg transition flex items-center space-x-1.5 shadow-sm"
        title="Download raw structured JSON dataset"
      >
        {downloadingFormat === 'json' ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-400" />
        ) : downloadedFormat === 'json' ? (
          <Check className="w-3.5 h-3.5 text-emerald-400" />
        ) : (
          <FileCode className="w-3.5 h-3.5 text-amber-400" />
        )}
        <span>JSON</span>
      </button>
    </div>
  );
});

export default ExportToolbar;
