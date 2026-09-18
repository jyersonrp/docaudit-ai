const API_BASE = '/api/v1';

export const api = {
  async fetchHealth() {
    const res = await fetch('/health');
    return res.json();
  },

  async listDocuments() {
    const res = await fetch(`${API_BASE}/documents`);
    if (!res.ok) throw new Error('Failed to fetch documents');
    return res.json();
  },

  async getDocument(docId) {
    const res = await fetch(`${API_BASE}/documents/${docId}`);
    if (!res.ok) throw new Error(`Failed to fetch document ${docId}`);
    return res.json();
  },

  async uploadDocument(file, auditType = 'legal', provider = null, customPrompt = null) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('audit_type', auditType);
    if (provider) formData.append('provider', provider);
    if (customPrompt) formData.append('custom_prompt', customPrompt);

    const res = await fetch(`${API_BASE}/documents/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  },

  async loadSampleDocument(sampleType = 'legal', provider = null) {
    const query = new URLSearchParams({ sample_type: sampleType });
    if (provider) query.append('provider', provider);
    
    const res = await fetch(`${API_BASE}/documents/sample?${query.toString()}`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to create sample document');
    return res.json();
  },

  async deleteDocument(docId) {
    const res = await fetch(`${API_BASE}/documents/${docId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error(`Failed to delete document ${docId}`);
    return res.json();
  },

  async getAuditResult(docId) {
    const res = await fetch(`${API_BASE}/audit/${docId}/result`);
    if (res.status === 202) {
      return { in_progress: true };
    }
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to fetch audit result' }));
      throw new Error(err.detail || 'Failed to fetch audit result');
    }
    return res.json();
  },

  async listProviders() {
    const res = await fetch(`${API_BASE}/audit/providers`);
    if (!res.ok) throw new Error('Failed to fetch providers');
    return res.json();
  },

  async rerunAudit(docId, provider = null, auditType = null, customPrompt = null) {
    const params = new URLSearchParams();
    if (provider) params.append('provider', provider);
    if (auditType) params.append('audit_type', auditType);
    if (customPrompt) params.append('custom_prompt', customPrompt);
    const queryString = params.toString() ? `?${params.toString()}` : '';
    const res = await fetch(`${API_BASE}/audit/${docId}/rerun${queryString}`, {
      method: 'POST',
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Rerun failed' }));
      throw new Error(err.detail || 'Rerun failed');
    }
    return res.json();
  },

  async queryChat(docId, question, provider = null) {
    const res = await fetch(`${API_BASE}/chat/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ doc_id: docId, question, top_k: 4, provider }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Chat query failed' }));
      throw new Error(err.detail || 'Chat query failed');
    }
    return res.json();
  },

  getExportUrl(docId, format = 'pdf') {
    return `${API_BASE}/export/${docId}/${format}`;
  }
};
