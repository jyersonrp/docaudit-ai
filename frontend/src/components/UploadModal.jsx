import React, { useState, memo } from 'react';
import { X, UploadCloud, FileText, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';

const UploadModal = memo(function UploadModal({ isOpen, onClose, onUpload, isUploading }) {
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
      setError("Please select a supported document: PDF, DOCX, TXT, or MD");
      return;
    }
    setFile(selected);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError("Please select a document to upload");
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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-zinc-950/80 backdrop-blur-md p-4">
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl w-full max-w-lg shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-800">
          <div>
            <h3 className="text-sm font-semibold text-zinc-100">Upload Document</h3>
            <p className="text-xs text-zinc-500 font-mono">PDF, DOCX, TXT, MD supported &bull; Magic bytes verified</p>
          </div>
          <button 
            onClick={onClose}
            className="text-zinc-500 hover:text-zinc-200 transition p-1.5 rounded-lg hover:bg-zinc-800"
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

          {/* Drag & Drop Zone */}
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            className={`border border-dashed rounded-xl p-6 text-center transition cursor-pointer ${
              dragActive 
                ? "border-sky-500 bg-sky-500/5 shadow-glow-sm" 
                : file 
                  ? "border-emerald-500/50 bg-emerald-500/5"
                  : "border-zinc-800 hover:border-zinc-700 bg-zinc-950/40"
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
                <CheckCircle2 className="w-5 h-5 shrink-0" />
                <div className="text-left">
                  <p className="text-xs font-medium text-zinc-100 truncate max-w-xs">{file.name}</p>
                  <p className="text-[10px] text-zinc-500 font-mono">{(file.size / 1024).toFixed(1)} KB</p>
                </div>
              </div>
            ) : (
              <div className="space-y-2">
                <div className="w-10 h-10 mx-auto rounded-lg bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-400">
                  <UploadCloud className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-xs font-medium text-zinc-200">
                    Click to select or drag and drop document
                  </p>
                  <p className="text-[10px] text-zinc-500 font-mono mt-0.5">Maximum file size: 50MB</p>
                </div>
              </div>
            )}
          </div>

          {/* Audit Framework Selection */}
          <div>
            <label className="block text-[11px] font-mono uppercase tracking-wider text-zinc-500 mb-2">
              Select Audit Type
            </label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { id: 'legal', label: 'Legal Contract', desc: 'Indemnity & covenants' },
                { id: 'financial', label: 'Financial Report', desc: 'Margins & fiscal ratios' },
                { id: 'custom', label: 'Custom Rules', desc: 'Custom rules prompt' },
              ].map((t) => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => setAuditType(t.id)}
                  className={`p-3 rounded-lg border text-left transition ${
                    auditType === t.id
                      ? "border-zinc-500 bg-zinc-800 text-zinc-100"
                      : "border-zinc-850 hover:border-zinc-800 bg-zinc-950/40 text-zinc-400"
                  }`}
                >
                  <div className="text-xs font-medium text-zinc-200">{t.label}</div>
                  <div className="text-[10px] text-zinc-500 mt-0.5 leading-tight">{t.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Custom prompt if custom rules chosen */}
          {auditType === 'custom' && (
            <div>
              <label className="block text-xs font-medium text-zinc-300 mb-1">
                Custom Verification Criteria
              </label>
              <textarea
                value={customPrompt}
                onChange={(e) => setCustomPrompt(e.target.value)}
                placeholder="Specify regulatory benchmarks, GDPR clauses, or security mandates..."
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-3 text-xs text-zinc-200 placeholder:text-zinc-600 focus:outline-none focus:border-zinc-700 resize-none h-20 font-mono"
              />
            </div>
          )}

          {/* Footer Actions */}
          <div className="flex items-center justify-end space-x-2.5 pt-3 border-t border-zinc-800">
            <button
              type="button"
              onClick={onClose}
              className="text-xs text-zinc-400 hover:text-zinc-200 px-3 py-1.5 font-medium transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!file || isUploading}
              className="text-xs bg-zinc-100 hover:bg-white disabled:opacity-50 text-zinc-950 font-medium px-4 py-2 rounded-lg shadow-sm transition flex items-center space-x-2"
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Processing...</span>
                </>
              ) : (
                <span>Start Audit Pipeline</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
});

export default UploadModal;
