import React, { useState } from 'react';
import { X, UploadCloud, FileText, AlertCircle, CheckCircle2 } from 'lucide-react';

export default function UploadModal({ isOpen, onClose, onUpload, isUploading }) {
  const [file, setFile] = useState(null);
  const [auditType, setAuditType] = useState('legal');
  const [customPrompt, setCustomPrompt] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (selected) => {
    setError(null);
    const validExts = ['.pdf', '.docx', '.doc', '.txt', '.md'];
    const hasValidExt = validExts.some(ext => selected.name.toLowerCase().endsWith(ext));
    if (!hasValidExt) {
      setError("Please select a valid document: PDF, DOCX, TXT, or MD");
      return;
    }
    setFile(selected);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError("Please select a file to upload");
      return;
    }
    try {
      await onUpload(file, auditType, customPrompt);
      onClose();
      setFile(null);
      setCustomPrompt('');
    } catch (err) {
      setError(err.message || "Failed to upload document");
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
          <div>
            <h3 className="text-base font-semibold text-white">Upload Document for Audit</h3>
            <p className="text-xs text-slate-400">PDF, Word DOCX, TXT supported</p>
          </div>
          <button 
            onClick={onClose}
            className="text-slate-400 hover:text-white transition p-1.5 rounded-lg hover:bg-slate-800"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs px-3.5 py-2.5 rounded-lg flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Drag & drop dropzone */}
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-xl p-6 text-center transition cursor-pointer ${
              dragActive 
                ? "border-sky-500 bg-sky-500/5" 
                : file 
                  ? "border-emerald-500/50 bg-emerald-500/5"
                  : "border-slate-700 hover:border-slate-600 bg-slate-950/40"
            }`}
            onClick={() => document.getElementById("file-input").click()}
          >
            <input
              id="file-input"
              type="file"
              onChange={handleChange}
              accept=".pdf,.docx,.doc,.txt,.md"
              className="hidden"
            />
            {file ? (
              <div className="flex items-center justify-center space-x-3 text-emerald-400">
                <CheckCircle2 className="w-6 h-6 shrink-0" />
                <div className="text-left">
                  <p className="text-sm font-semibold text-white truncate max-w-xs">{file.name}</p>
                  <p className="text-xs text-slate-400">{(file.size / 1024).toFixed(1)} KB</p>
                </div>
              </div>
            ) : (
              <div className="space-y-2">
                <div className="w-12 h-12 mx-auto rounded-full bg-slate-800 flex items-center justify-center text-sky-400">
                  <UploadCloud className="w-6 h-6" />
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-200">
                    Click to select or drag and drop document
                  </p>
                  <p className="text-xs text-slate-500 mt-0.5">Maximum file size: 50MB</p>
                </div>
              </div>
            )}
          </div>

          {/* Audit Type Selection */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
              Audit Framework & Schema
            </label>
            <div className="grid grid-cols-3 gap-2.5">
              {[
                { id: 'legal', label: 'Legal Contract', desc: 'Jurisdiction, indemnity, terms' },
                { id: 'financial', label: 'Financial Report', desc: 'Revenue, margins, fiscal risks' },
                { id: 'custom', label: 'Custom Rules', desc: 'Custom criteria prompt' },
              ].map((t) => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => setAuditType(t.id)}
                  className={`p-3 rounded-xl border text-left transition ${
                    auditType === t.id
                      ? "border-sky-500 bg-sky-500/10 text-white"
                      : "border-slate-800 hover:border-slate-700 bg-slate-950/40 text-slate-400"
                  }`}
                >
                  <div className="text-xs font-semibold text-slate-200">{t.label}</div>
                  <div className="text-[10px] text-slate-500 mt-1 leading-tight">{t.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Custom prompt if custom rules chosen */}
          {auditType === 'custom' && (
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Custom Verification Rules
              </label>
              <textarea
                value={customPrompt}
                onChange={(e) => setCustomPrompt(e.target.value)}
                placeholder="Example: Verify compliance with GDPR Article 28 data processor clauses, sub-processor notification windows, and data breach liability caps..."
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-slate-200 focus:outline-none focus:border-sky-500 resize-none h-20"
              />
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="text-xs text-slate-400 hover:text-white px-4 py-2 font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!file || isUploading}
              className="text-xs bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white font-semibold px-5 py-2.5 rounded-lg shadow-sm shadow-sky-600/30 transition flex items-center space-x-2"
            >
              {isUploading ? "Processing..." : "Start Audit Pipeline"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
