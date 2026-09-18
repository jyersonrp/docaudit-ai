import React, { useState, useEffect } from 'react';
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
  RotateCw
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

  // Initial load
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
      }, 1500);
      return () => clearInterval(interval);
    } else if (currentDoc.status === 'COMPLETED') {
      loadAuditData(selectedDocId);
    }
  }, [selectedDocId, documents]);

  const loadAuditData = async (docId) => {
    setIsLoadingAudit(true);
    try {
      const res = await api.getAuditResult(docId);
      if (!res.in_progress) {
        setAuditData(res);
      }
    } catch (e) {
      console.error("Error loading audit data:", e);
      setAuditData(null);
    } finally {
      setIsLoadingAudit(false);
    }
  };

  const handleUpload = async (file, auditType, customPrompt) => {
    setIsUploading(true);
    try {
      const res = await api.uploadDocument(file, auditType, selectedProvider, customPrompt);
      await loadDocuments();
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
      setSelectedDocId(res.doc_id);
      setActiveTab('overview');
    } finally {
      setIsLoadingSample(false);
    }
  };

  const handleRerun = async (docId) => {
    try {
      await api.rerunAudit(docId, selectedProvider);
      const updated = await api.getDocument(docId);
      setDocuments(prev => prev.map(d => d.id === docId ? updated : d));
      setAuditData(null);
    } catch (e) {
      console.error("Failed to rerun audit:", e);
    }
  };

  const handleDeleteDoc = async (docId) => {
    if (!confirm("Are you sure you want to delete this document and its audit findings?")) return;
    try {
      await api.deleteDocument(docId);
      const remaining = documents.filter(d => d.id !== docId);
      setDocuments(remaining);
      if (selectedDocId === docId) {
        setSelectedDocId(remaining.length > 0 ? remaining[0].id : null);
        setAuditData(null);
      }
    } catch (e) {
      console.error("Failed to delete document:", e);
    }
  };

  const currentDoc = documents.find(d => d.id === selectedDocId);

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100">
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

      {/* Main Workspace Layout */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left Column: Document Repository Sidebar */}
        <div className="lg:col-span-1 h-[750px]">
          <DocumentList
            documents={documents}
            selectedDocId={selectedDocId}
            onSelectDoc={(id) => {
              setSelectedDocId(id);
              loadAuditData(id);
            }}
            onDeleteDoc={handleDeleteDoc}
          />
        </div>

        {/* Right Column: Active Document Dashboard */}
        <div className="lg:col-span-3 flex flex-col space-y-4">
          {currentDoc ? (
            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 flex flex-col space-y-6">
              {/* Document Header Bar */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-800">
                <div>
                  <div className="flex items-center space-x-2.5">
                    <h2 className="text-lg font-bold text-white tracking-tight truncate max-w-md">
                      {currentDoc.filename}
                    </h2>
                    <span className="bg-slate-800 text-sky-400 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-slate-700 uppercase">
                      {currentDoc.audit_type || 'legal'}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">
                    {currentDoc.total_pages} {currentDoc.total_pages === 1 ? 'page' : 'pages'} &bull; {currentDoc.total_chunks} indexed chunks &bull; {(currentDoc.file_size / 1024).toFixed(1)} KB
                  </p>
                </div>

                {/* Header Action Buttons */}
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleRerun(currentDoc.id)}
                    className="bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-xs font-semibold px-3 py-1.5 rounded-lg transition flex items-center space-x-1.5 shadow-sm"
                    title="Re-run audit with currently selected AI provider"
                  >
                    <RotateCw className="w-3.5 h-3.5 text-sky-400" />
                    <span>Rerun Audit</span>
                  </button>
                  {currentDoc.status === 'COMPLETED' && auditData && (
                    <ExportToolbar docId={currentDoc.id} filename={currentDoc.filename} />
                  )}
                </div>
              </div>

              {/* Failed State Banner */}
              {currentDoc.status === 'FAILED' && (
                <div className="p-5 rounded-xl border border-rose-500/30 bg-rose-500/10 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-start space-x-3">
                    <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
                    <div>
                      <h4 className="text-xs font-bold text-rose-300 uppercase tracking-wide">Audit Failed</h4>
                      <p className="text-xs text-rose-200/90 mt-0.5">{currentDoc.error || currentDoc.status_message}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => handleRerun(currentDoc.id)}
                    className="bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold px-4 py-2 rounded-lg transition flex items-center space-x-1.5 self-start sm:self-center shrink-0 shadow-sm"
                  >
                    <RotateCw className="w-3.5 h-3.5" />
                    <span>Retry Pipeline</span>
                  </button>
                </div>
              )}

              {/* Status Banner when processing */}
              {currentDoc.status !== 'COMPLETED' && currentDoc.status !== 'FAILED' && (
                <div className="p-5 rounded-xl border border-sky-500/20 bg-sky-500/5 flex items-center space-x-3">
                  <Loader2 className="w-5 h-5 text-sky-400 animate-spin shrink-0" />
                  <div className="flex-1">
                    <p className="text-xs font-semibold text-slate-200">
                      Processing Pipeline: {currentDoc.status_message}
                    </p>
                    <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden mt-2">
                      <div 
                        className="bg-sky-500 h-full transition-all duration-300 rounded-full"
                        style={{ width: `${Math.max(currentDoc.progress, 5)}%` }}
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Navigation Tabs */}
              {currentDoc.status === 'COMPLETED' && (
                <div>
                  <div className="flex items-center space-x-2 border-b border-slate-800 pb-3">
                    {[
                      { id: 'overview', label: 'Executive Overview', icon: ShieldCheck },
                      { id: 'findings', label: 'Findings & Clauses', icon: Search },
                      { id: 'chat', label: 'RAG Chat & Citations', icon: MessageSquare },
                      { id: 'raw', label: 'Pydantic JSON Schema', icon: Code },
                    ].map((tab) => {
                      const Icon = tab.icon;
                      const isActive = activeTab === tab.id;
                      return (
                        <button
                          key={tab.id}
                          onClick={() => setActiveTab(tab.id)}
                          className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold transition ${
                            isActive
                              ? "bg-sky-600 text-white shadow-sm shadow-sky-600/30"
                              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                          }`}
                        >
                          <Icon className="w-4 h-4" />
                          <span>{tab.label}</span>
                        </button>
                      );
                    })}
                  </div>

                  {/* Tab Panels */}
                  <div className="pt-4">
                    {isLoadingAudit ? (
                      <div className="p-12 text-center text-slate-400 flex flex-col items-center space-y-3">
                        <Loader2 className="w-6 h-6 animate-spin text-sky-400" />
                        <span className="text-xs">Loading structured audit data...</span>
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
            <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-12 text-center flex flex-col items-center justify-center space-y-4 h-[550px]">
              <div className="w-16 h-16 rounded-2xl bg-slate-800/80 border border-slate-700/60 flex items-center justify-center text-sky-400 shadow-xl">
                <FileText className="w-8 h-8" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">No Document Selected</h3>
                <p className="text-xs text-slate-400 max-w-sm mt-1">
                  Upload an enterprise agreement or click below to load an instant pre-packaged sample for testing.
                </p>
              </div>
              <div className="flex items-center space-x-3 pt-2">
                <button
                  onClick={() => handleLoadSample('legal')}
                  className="bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold px-4 py-2.5 rounded-xl transition flex items-center space-x-2"
                >
                  <Sparkles className="w-4 h-4 text-amber-400" />
                  <span>Load Sample Contract</span>
                </button>
                <button
                  onClick={() => handleLoadSample('financial')}
                  className="bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold px-4 py-2.5 rounded-xl transition flex items-center space-x-2"
                >
                  <BarChart3 className="w-4 h-4 text-emerald-400" />
                  <span>Load Sample Financials</span>
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
      />
    </div>
  );
}
