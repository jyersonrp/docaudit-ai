import React, { useState } from 'react';
import { Download, FileText, FileCode, FileDown, Loader2 } from 'lucide-react';
import { api } from '../services/api';

export default function ExportToolbar({ docId, filename }) {
  const [downloadingFormat, setDownloadingFormat] = useState(null);

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
    } catch (e) {
      console.error("Download failed:", e);
    } finally {
      setTimeout(() => setDownloadingFormat(null), 1000);
    }
  };

  return (
    <div className="flex items-center space-x-2">
      <span className="text-xs text-slate-500 font-medium mr-1 hidden sm:inline">
        Export:
      </span>

      {/* PDF Button */}
      <button
        onClick={() => handleDownload('pdf')}
        disabled={downloadingFormat === 'pdf'}
        className="bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 text-xs font-semibold px-3 py-1.5 rounded-lg transition flex items-center space-x-1.5 shadow-sm"
        title="Download executive publication-grade PDF report"
      >
        {downloadingFormat === 'pdf' ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
        ) : (
          <FileDown className="w-3.5 h-3.5 text-rose-400" />
        )}
        <span>Executive PDF</span>
      </button>

      {/* Markdown Button */}
      <button
        onClick={() => handleDownload('markdown')}
        disabled={downloadingFormat === 'markdown'}
        className="bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold px-3 py-1.5 rounded-lg transition flex items-center space-x-1.5 shadow-sm"
        title="Download formatted Markdown summary"
      >
        {downloadingFormat === 'markdown' ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
        ) : (
          <FileText className="w-3.5 h-3.5 text-sky-400" />
        )}
        <span>Markdown</span>
      </button>

      {/* JSON Button */}
      <button
        onClick={() => handleDownload('json')}
        disabled={downloadingFormat === 'json'}
        className="bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold px-3 py-1.5 rounded-lg transition flex items-center space-x-1.5 shadow-sm"
        title="Download raw structured JSON dataset"
      >
        {downloadingFormat === 'json' ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
        ) : (
          <FileCode className="w-3.5 h-3.5 text-amber-400" />
        )}
        <span>JSON</span>
      </button>
    </div>
  );
}
