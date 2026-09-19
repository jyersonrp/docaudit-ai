import React, { useState, useEffect, useMemo, useCallback } from 'react';
import Navbar from './components/Navbar';
import DocumentList from './components/DocumentList';
import ExecutiveOverview from './components/ExecutiveOverview';
import FindingsViewer from './components/FindingsViewer';
import RagChat from './components/RagChat';
import RawJsonViewer from './components/RawJsonViewer';
import ExportToolbar from './components/ExportToolbar';
import UploadModal from './components/UploadModal';
import { api } from './services/api';
import { 
  ShieldCheck, 
  Search, 
  MessageSquare, 
  Code, 
  FileText, 
  Sparkles, 
  BarChart3, 
  Loader2, 
  AlertCircle,
  RotateCw,
  AlertTriangle
} from 'lucide-react';

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [auditData, setAuditData] = useState(null);
  const [isLoadingAudit, setIsLoadingAudit] = useState(false);
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isLoadingSample, setIsLoadingSample] = useState(false);
  const [providers, setProviders] = useState([]);
  const [selectedProvider, setSelectedProvider] = useState('mock');
  const [systemHealth, setSystemHealth] = useState(null);

  // Initial data loading
  useEffect(() => {
    loadProviders();
    loadHealth();
    loadDocuments(true);
  }, []);

  const loadProviders = async () => {
    try {
      const data = await api.listProviders();
      setProviders(data);
      const defaultProv = data.find(p => p.is_default);
      if (defaultProv) setSelectedProvider(defaultProv.id);
    } catch (e) {
      console.error("Failed to load providers:", e);
    }
  };

  const loadHealth = async () => {
    try {
      const health = await api.fetchHealth();
      setSystemHealth(health);
    } catch (e) {
      console.error("Failed to load health:", e);
    }
  };

  const loadDocuments = async (selectFirst = false) => {
    try {
      const docs = await api.listDocuments();
      setDocuments(docs);
      if (selectFirst && docs.length > 0 && !selectedDocId) {
        setSelectedDocId(docs[0].id);
      }
    } catch (e) {
      console.error("Failed to load documents:", e);
    }
  };

  const loadAuditData = useCallback(async (docId) => {
    setIsLoadingAudit(true);
    try {
      const res = await api.getAuditResult(docId);
      if (res.in_progress) {
        setAuditData(null);
      } else {
        setAuditData(res);
      }
    } catch (e) {
      console.error("Error loading audit data:", e);
      setAuditData(null);
    } finally {
      setIsLoadingAudit(false);
    }
  }, []);

  // Poll active document when processing
  useEffect(() => {
    if (!selectedDocId) return;

    const currentDoc = documents.find(d => d.id === selectedDocId);
    if (!currentDoc) return;

    if (currentDoc.status !== 'COMPLETED' && currentDoc.status !== 'FAILED') {
      const interval = setInterval(async () => {
        try {
          const updated = await api.getDocument(selectedDocId);
          setDocuments(prev => prev.map(d => d.id === selectedDocId ? updated : d));
          if (updated.status === 'COMPLETED') {
            loadAuditData(selectedDocId);
          }
        } catch (e) {
          console.error("Polling error:", e);
        }
      }, 1200);
      return () => clearInterval(interval);
    } else if (currentDoc.status === 'COMPLETED' && (!auditData || auditData.doc_id !== selectedDocId)) {
      loadAuditData(selectedDocId);
    }
  }, [selectedDocId, documents, auditData, loadAuditData]);

  const handleUpload = async (file, auditType, customPrompt) => {
    setIsUploading(true);
    try {
      const res = await api.uploadDocument(file, auditType, selectedProvider, customPrompt);
      await loadDocuments();
      setAuditData(null);
      setSelectedDocId(res.doc_id);
      setActiveTab('overview');
    } finally {
      setIsUploading(false);
    }
  };

  const handleLoadSample = async (sampleType) => {
    setIsLoadingSample(true);
    try {
      const res = await api.loadSampleDocument(sampleType, selectedProvider);
      await loadDocuments();
      setAuditData(null);
      setSelectedDocId(res.doc_id);
      setActiveTab('overview');
    } finally {
      setIsLoadingSample(false);
    }
  };

  const handleRerun = async (docId, overrideProvider = null) => {
    try {
      setAuditData(null);
      const prov = overrideProvider || selectedProvider;
      await api.rerunAudit(docId, prov);
      const updated = await api.getDocument(docId);
      setDocuments(prev => prev.map(d => d.id === docId ? updated : d));
    } catch (e) {
      console.error("Failed to rerun audit:", e);
    }
  };

  const handleDeleteDoc = async (docId) => {
    if (!confirm("Are you sure you want to delete this document and its audit record?")) return;
    try {
      await api.deleteDocument(docId);
      const remaining = documents.filter(d => d.id !== docId);
      setDocuments(remaining);
      if (selectedDocId === docId) {
        const nextId = remaining.length > 0 ? remaining[0].id : null;
        setSelectedDocId(nextId);
        setAuditData(null);
        if (nextId) {
          loadAuditData(nextId);
        }
      }
    } catch (e) {
      console.error("Failed to delete document:", e);
    }
  };

  const currentDoc = useMemo(() => {
    return documents.find(d => d.id === selectedDocId);
  }, [documents, selectedDocId]);

  const selectedProviderObj = useMemo(() => {
    return providers.find(p => p.id === selectedProvider);
  }, [providers, selectedProvider]);

  // Tab definitions
  const tabs = useMemo(() => [
    { id: 'overview', label: 'Overview', icon: ShieldCheck },
    { id: 'findings', label: 'Findings', icon: Search },
    { id: 'chat', label: 'Chat & Citations', icon: MessageSquare },
    { id: 'raw', label: 'Schema JSON', icon: Code },
  ], []);

  return (
    <div className="min-h-screen flex flex-col bg-zinc-950 text-zinc-100 antialiased">
      {/* Navbar */}
      <Navbar
        providers={providers}
        selectedProvider={selectedProvider}
        onSelectProvider={setSelectedProvider}
        onOpenUpload={() => setIsUploadOpen(true)}
        onLoadSample={handleLoadSample}
        isLoadingSample={isLoadingSample}
        systemHealth={systemHealth}
      />

      {/* Provider Status Warning Banner if current selection is unavailable */}
      {selectedProviderObj && !selectedProviderObj.available && (
        <div className="bg-amber-500/10 border-b border-amber-500/20 px-6 py-2.5 text-xs text-amber-300 flex items-center justify-between">
          <div className="flex items-center space-x-2.5 max-w-4xl">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
            <span>
              <strong className="font-semibold text-amber-200">Engine Notice ({selectedProviderObj.name}):</strong>{" "}
              {selectedProviderObj.status_message}
            </span>
          </div>
          <button 
            onClick={() => setSelectedProvider('mock')}
            className="bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 border border-amber-500/30 px-3 py-1 rounded-md text-[11px] font-medium transition shrink-0 ml-4"
          >
            Switch to Offline Engine
          </button>
        </div>
      )}

      {/* Main Workspace Layout */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left Column: Document Repository Sidebar */}
        <div className="lg:col-span-1 h-[780px]">
          <DocumentList
            documents={documents}
            selectedDocId={selectedDocId}
            onSelectDoc={(id) => {
              setSelectedDocId(id);
              setAuditData(null);
              loadAuditData(id);
            }}
            onDeleteDoc={handleDeleteDoc}
          />
        </div>

        {/* Right Column: Active Document Dashboard */}
        <div className="lg:col-span-3 flex flex-col space-y-4">
          {currentDoc ? (
            <div className="bg-zinc-900/50 border border-zinc-850 rounded-xl p-6 flex flex-col space-y-6 backdrop-blur-md">
              {/* Document Header Bar */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-zinc-850">
                <div className="min-w-0">
                  <div className="flex items-center space-x-2.5">
                    <h2 className="text-base font-semibold text-zinc-100 tracking-tight truncate max-w-md">
                      {currentDoc.filename}
                    </h2>
                    <span className="bg-zinc-850 text-zinc-300 font-mono text-[10px] px-2 py-0.5 rounded border border-zinc-750 uppercase">
                      {currentDoc.audit_type || 'legal'}
                    </span>
                  </div>
                  <p className="text-xs text-zinc-500 font-mono mt-1">
                    {currentDoc.total_pages} {currentDoc.total_pages === 1 ? 'page' : 'pages'} &bull; {currentDoc.total_chunks} indexed chunks &bull; {(currentDoc.file_size / 1024).toFixed(1)} KB
                  </p>
                </div>

                {/* Header Action Buttons */}
                <div className="flex items-center space-x-2 shrink-0">
                  <button
                    onClick={() => handleRerun(currentDoc.id)}
                    className="bg-zinc-900 hover:bg-zinc-850 text-zinc-300 border border-zinc-800 hover:border-zinc-750 text-xs font-medium px-2.5 py-1.5 rounded-lg transition flex items-center space-x-1.5 shadow-sm"
                    title="Re-run audit with selected AI provider"
                  >
                    <RotateCw className="w-3.5 h-3.5 text-zinc-400" />
                    <span>Rerun</span>
                  </button>
                  {currentDoc.status === 'COMPLETED' && auditData && (
                    <ExportToolbar docId={currentDoc.id} filename={currentDoc.filename} />
                  )}
                </div>
              </div>

              {/* Failed State Banner */}
              {currentDoc.status === 'FAILED' && (
                <div className="p-5 rounded-xl border border-rose-500/25 bg-rose-500/5 flex flex-col space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                    <div className="flex items-start space-x-3">
                      <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
                      <div>
                        <h4 className="text-xs font-semibold text-rose-300 uppercase tracking-wider">Audit Failed</h4>
                        <p className="text-xs text-rose-200/90 mt-1 leading-relaxed whitespace-pre-wrap">
                          {currentDoc.error || currentDoc.status_message}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2 shrink-0 self-start sm:self-center">
                      <button
                        onClick={() => {
                          setSelectedProvider('mock');
                          handleRerun(currentDoc.id, 'mock');
                        }}
                        className="bg-zinc-900 hover:bg-zinc-850 text-zinc-200 border border-zinc-700 hover:border-zinc-600 text-xs font-medium px-3.5 py-1.5 rounded-lg transition flex items-center space-x-1.5 shadow-sm"
                        title="Audit with built-in heuristic engine without local server dependencies"
                      >
                        <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                        <span>Run Heuristic Engine (Offline)</span>
                      </button>
                      <button
                        onClick={() => handleRerun(currentDoc.id)}
                        className="bg-rose-600 hover:bg-rose-500 text-white text-xs font-medium px-3 py-1.5 rounded-lg transition flex items-center space-x-1.5 shadow-sm"
                        title="Retry audit with current provider"
                      >
                        <RotateCw className="w-3.5 h-3.5" />
                        <span>Retry</span>
                      </button>
                    </div>
                  </div>

                  {/* Diagnostic troubleshooting box if error is Ollama related */}
                  {(currentDoc.error?.toLowerCase().includes('ollama') || currentDoc.status_message?.toLowerCase().includes('ollama')) && (
                    <div className="p-3.5 bg-zinc-900/90 border border-zinc-800 rounded-lg text-xs space-y-2 text-zinc-300 font-mono">
                      <div className="font-semibold text-amber-400 text-[11px] uppercase tracking-wider flex items-center space-x-1.5 font-sans">
                        <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                        <span>Ollama Local Diagnostics & Quick Fix:</span>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] pt-1">
                        <div className="bg-zinc-950 p-2 rounded border border-zinc-800">
                          <span className="text-zinc-500 block text-[10px]">1. Start Ollama Server</span>
                          <code className="text-sky-300 select-all font-semibold">ollama serve</code>
                        </div>
                        <div className="bg-zinc-950 p-2 rounded border border-zinc-800">
                          <span className="text-zinc-500 block text-[10px]">2. Download Llama 3 Model</span>
                          <code className="text-emerald-300 select-all font-semibold">ollama run llama3</code>
                        </div>
                      </div>
                      <p className="text-[11px] text-zinc-400 pt-1 font-sans">
                        Tip: Click <strong>"Run Heuristic Engine (Offline)"</strong> to immediately audit this document without waiting for Ollama.
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Status Banner when processing */}
              {currentDoc.status !== 'COMPLETED' && currentDoc.status !== 'FAILED' && (
                <div className="p-4 rounded-xl border border-zinc-800 bg-zinc-950/60 flex items-center space-x-3">
                  <Loader2 className="w-4 h-4 text-sky-400 animate-spin shrink-0" />
                  <div className="flex-1">
                    <p className="text-xs font-medium text-zinc-300">
                      Processing Pipeline: {currentDoc.status_message}
                    </p>
                    <div className="w-full bg-zinc-800 h-1.5 rounded-full overflow-hidden mt-2">
                      <div 
                        className="bg-sky-500 h-full transition-all duration-300 rounded-full"
                        style={{ width: `${Math.max(currentDoc.progress, 5)}%` }}
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Navigation Tabs (Linear Segmented Control) */}
              {currentDoc.status === 'COMPLETED' && (
                <div>
                  <div className="flex items-center bg-zinc-900/90 border border-zinc-800/80 p-1 rounded-xl w-fit">
                    {tabs.map((tab) => {
                      const Icon = tab.icon;
                      const isActive = activeTab === tab.id;
                      return (
                        <button
                          key={tab.id}
                          onClick={() => setActiveTab(tab.id)}
                          className={`flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg text-xs font-medium transition select-none ${
                            isActive
                              ? "bg-zinc-800 text-zinc-100 shadow-sm border border-zinc-700/60"
                              : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-850/50"
                          }`}
                        >
                          <Icon className="w-3.5 h-3.5" />
                          <span>{tab.label}</span>
                        </button>
                      );
                    })}
                  </div>

                  {/* Tab Panels */}
                  <div className="pt-4">
                    {isLoadingAudit ? (
                      <div className="p-16 text-center text-zinc-500 flex flex-col items-center space-y-3">
                        <Loader2 className="w-5 h-5 animate-spin text-zinc-400" />
                        <span className="text-xs font-mono">Loading structured audit data...</span>
                      </div>
                    ) : (
                      <>
                        {activeTab === 'overview' && <ExecutiveOverview auditData={auditData} />}
                        {activeTab === 'findings' && <FindingsViewer auditData={auditData} />}
                        {activeTab === 'chat' && (
                          <RagChat 
                            docId={currentDoc.id} 
                            documentMetadata={currentDoc} 
                            selectedProvider={selectedProvider}
                          />
                        )}
                        {activeTab === 'raw' && <RawJsonViewer data={auditData} />}
                      </>
                    )}
                  </div>
                </div>
              )}
            </div>
          ) : (
            /* Empty State: No document selected */
            <div className="bg-zinc-900/40 border border-zinc-850 rounded-xl p-12 text-center flex flex-col items-center justify-center space-y-4 h-[550px] backdrop-blur-md">
              <div className="w-14 h-14 rounded-xl bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-400 shadow-inner">
                <FileText className="w-7 h-7" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-zinc-200">No Document Selected</h3>
                <p className="text-xs text-zinc-500 max-w-sm mt-1 leading-relaxed">
                  Upload an agreement or load a pre-packaged sample document to inspect covenants, liability, and risk scoring.
                </p>
              </div>
              <div className="flex items-center space-x-2 pt-2">
                <button
                  onClick={() => handleLoadSample('legal')}
                  className="bg-zinc-100 hover:bg-white text-zinc-950 text-xs font-medium px-3.5 py-2 rounded-lg transition flex items-center space-x-1.5 shadow-sm"
                >
                  <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                  <span>Sample Contract</span>
                </button>
                <button
                  onClick={() => handleLoadSample('financial')}
                  className="bg-zinc-900 hover:bg-zinc-850 text-zinc-300 border border-zinc-800 text-xs font-medium px-3.5 py-2 rounded-lg transition flex items-center space-x-1.5"
                >
                  <BarChart3 className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Sample Financials</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Upload Modal */}
      <UploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUpload={handleUpload}
        isUploading={isUploading}
        selectedProviderObj={selectedProviderObj}
        onSwitchToMock={() => setSelectedProvider('mock')}
      />
    </div>
  );
}
