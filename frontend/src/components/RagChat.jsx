import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Bot, 
  User, 
  Sparkles, 
  Bookmark, 
  ChevronDown, 
  ChevronUp, 
  FileText,
  Loader2
} from 'lucide-react';
import { api } from '../services/api';

export default function RagChat({ docId, documentMetadata, selectedProvider }) {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'bot',
      text: `Hello! I have indexed and audited "${documentMetadata?.filename || 'the document'}". Ask me anything regarding clauses, liability, revenue figures, risk exposures, or governing terms.`,
      citations: []
    }
  ]);
  const [question, setQuestion] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [expandedCitations, setExpandedCitations] = useState({});
  const messagesEndRef = useRef(null);

  const suggestedQuestions = [
    "What is the liability cap under this contract?",
    "What are the notice requirements for termination?",
    "Are there any indemnification obligations?",
    "What are the major fiscal risks or debt covenants?"
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSend = async (qText = null) => {
    const q = qText || question;
    if (!q.trim() || isLoading) return;

    const userMsgId = Date.now().toString();
    const newMessages = [
      ...messages,
      { id: userMsgId, sender: 'user', text: q }
    ];
    setMessages(newMessages);
    setQuestion('');
    setIsLoading(true);

    try {
      const response = await api.queryChat(docId, q, selectedProvider);
      setMessages([
        ...newMessages,
        {
          id: (Date.now() + 1).toString(),
          sender: 'bot',
          text: response.answer,
          citations: response.citations || [],
          provider: response.provider_used
        }
      ]);
    } catch (err) {
      setMessages([
        ...newMessages,
        {
          id: (Date.now() + 1).toString(),
          sender: 'bot',
          text: `Error retrieving answer: ${err.message || 'Please try again.'}`,
          citations: []
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleCitation = (msgId, citIdx) => {
    const key = `${msgId}_${citIdx}`;
    setExpandedCitations(prev => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl flex flex-col h-[650px] overflow-hidden">
      {/* Chat Header */}
      <div className="px-5 py-3.5 border-b border-slate-800 flex items-center justify-between bg-slate-950/40">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-xs font-bold text-white uppercase tracking-wider">
              Interactive RAG Document Chat
            </h4>
            <p className="text-[11px] text-slate-400">
              Retrieves answers grounded with exact page citations
            </p>
          </div>
        </div>

        <div className="text-[11px] text-slate-500 font-mono">
          Top-K Hybrid Retrieval Active
        </div>
      </div>

      {/* Suggested Prompt Chips */}
      <div className="px-5 py-2.5 bg-slate-950/20 border-b border-slate-800/60 flex items-center space-x-2 overflow-x-auto">
        <span className="text-[11px] font-semibold text-slate-400 flex items-center space-x-1 shrink-0">
          <Sparkles className="w-3 h-3 text-amber-400" />
          <span>Suggestions:</span>
        </span>
        {suggestedQuestions.map((s, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(s)}
            className="text-[11px] text-slate-300 hover:text-white bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 px-2.5 py-1 rounded-full whitespace-nowrap transition"
          >
            {s}
          </button>
        ))}
      </div>

      {/* Message Stream */}
      <div className="flex-1 p-5 overflow-y-auto space-y-4">
        {messages.map((m) => (
          <div 
            key={m.id}
            className={`flex items-start space-x-3 ${m.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {m.sender === 'bot' && (
              <div className="w-7 h-7 rounded-lg bg-sky-600/20 border border-sky-500/30 flex items-center justify-center text-sky-400 shrink-0 mt-0.5">
                <Bot className="w-3.5 h-3.5" />
              </div>
            )}

            <div className={`max-w-2xl rounded-2xl p-4 text-xs leading-relaxed ${
              m.sender === 'user'
                ? 'bg-sky-600 text-white rounded-br-none'
                : 'bg-slate-950/70 border border-slate-800 text-slate-200 rounded-bl-none space-y-3'
            }`}>
              <div className="whitespace-pre-wrap">{m.text}</div>

              {m.sender === 'bot' && m.provider && (
                <div className="text-[10px] text-slate-500 font-mono flex items-center space-x-1 pt-1">
                  <span>Engine:</span>
                  <span className="text-sky-400 font-semibold">{m.provider}</span>
                </div>
              )}

              {/* Citations block */}
              {m.citations && m.citations.length > 0 && (
                <div className="pt-2 border-t border-slate-800/80 space-y-1.5">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1">
                    <Bookmark className="w-3 h-3 text-sky-400" />
                    <span>Grounding Citations ({m.citations.length}):</span>
                  </span>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                    {m.citations.map((c, cIdx) => {
                      const isExpanded = expandedCitations[`${m.id}_${cIdx}`];
                      return (
                        <div 
                          key={cIdx}
                          className="bg-slate-900 border border-slate-800 rounded-lg p-2 text-[11px] space-y-1"
                        >
                          <div 
                            className="flex items-center justify-between cursor-pointer"
                            onClick={() => toggleCitation(m.id, cIdx)}
                          >
                            <span className="font-semibold text-sky-400 flex items-center space-x-1">
                              <FileText className="w-3 h-3" />
                              <span>Page {c.page_number}</span>
                            </span>
                            <div className="flex items-center space-x-1 text-slate-400">
                              <span className="text-[10px]">Rel: {(c.relevance * 100).toFixed(0)}%</span>
                              {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                            </div>
                          </div>

                          <p className={`text-slate-400 italic ${isExpanded ? '' : 'line-clamp-2'}`}>
                            "{c.snippet}"
                          </p>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>

            {m.sender === 'user' && (
              <div className="w-7 h-7 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 shrink-0 mt-0.5">
                <User className="w-3.5 h-3.5" />
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex items-center space-x-3">
            <div className="w-7 h-7 rounded-lg bg-sky-600/20 border border-sky-500/30 flex items-center justify-center text-sky-400 shrink-0">
              <Bot className="w-3.5 h-3.5" />
            </div>
            <div className="bg-slate-950/70 border border-slate-800 rounded-2xl rounded-bl-none p-3.5 text-xs text-slate-400 flex items-center space-x-2">
              <Loader2 className="w-4 h-4 animate-spin text-sky-400" />
              <span>Analyzing document and synthesizing answer...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <form 
        onSubmit={(e) => { e.preventDefault(); handleSend(); }}
        className="p-3.5 border-t border-slate-800 bg-slate-950/50 flex items-center space-x-2"
      >
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask any question about this document (e.g. termination, liability cap, revenue)..."
          className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-slate-100 focus:outline-none focus:border-sky-500 placeholder:text-slate-500"
        />
        <button
          type="submit"
          disabled={!question.trim() || isLoading}
          className="bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white px-4 py-2.5 rounded-xl font-semibold transition flex items-center space-x-1.5 shadow-sm shadow-sky-600/30"
        >
          <Send className="w-3.5 h-3.5" />
          <span className="hidden sm:inline text-xs">Query</span>
        </button>
      </form>
    </div>
  );
}
