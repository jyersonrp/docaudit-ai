import React, { useState, useRef, useEffect, memo } from 'react';
import { 
  Send, 
  Bot, 
  User, 
  Sparkles, 
  Bookmark, 
  ChevronDown, 
  ChevronUp, 
  FileText,
  Loader2,
  CornerDownLeft
} from 'lucide-react';
import { api } from '../services/api';

const RagChat = memo(function RagChat({ docId, documentMetadata, selectedProvider }) {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'bot',
      text: `Hello! I have indexed and audited "${documentMetadata?.filename || 'the document'}". Ask me anything regarding clauses, liability caps, governing law, revenue figures, or risk exposures.`,
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
    <div className="bg-zinc-900/60 border border-zinc-850 rounded-xl flex flex-col h-[650px] overflow-hidden backdrop-blur-md">
      {/* Chat Top Bar */}
      <div className="px-5 py-3 border-b border-zinc-850 flex items-center justify-between bg-zinc-950/40">
        <div className="flex items-center space-x-2.5">
          <div className="w-7 h-7 rounded-lg bg-zinc-900 border border-zinc-800 flex items-center justify-center text-sky-400">
            <Bot className="w-3.5 h-3.5" />
          </div>
          <div>
            <h4 className="text-xs font-medium text-zinc-200">
              Interactive Document Assistant
            </h4>
            <p className="text-[10px] text-zinc-500 font-mono">
              RAG hybrid retrieval &bull; grounded page citations
            </p>
          </div>
        </div>

        <div className="text-[10px] text-zinc-500 font-mono bg-zinc-900 border border-zinc-800 px-2 py-0.5 rounded">
          Top-K Vector Context
        </div>
      </div>

      {/* Suggested Prompt Chips */}
      <div className="px-5 py-2.5 bg-zinc-950/20 border-b border-zinc-850/60 flex items-center space-x-2 overflow-x-auto">
        <span className="text-[11px] text-zinc-500 flex items-center space-x-1 shrink-0 font-mono">
          <Sparkles className="w-3 h-3 text-amber-400" />
          <span>Suggestions:</span>
        </span>
        {suggestedQuestions.map((s, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(s)}
            className="text-[11px] text-zinc-400 hover:text-zinc-100 bg-zinc-900 hover:bg-zinc-850 border border-zinc-800 px-2.5 py-1 rounded-md whitespace-nowrap transition"
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
              <div className="w-6 h-6 rounded-md bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-400 shrink-0 mt-0.5">
                <Bot className="w-3.5 h-3.5" />
              </div>
            )}

            <div className={`max-w-2xl rounded-xl p-4 text-xs leading-relaxed ${
              m.sender === 'user'
                ? 'bg-zinc-100 text-zinc-950 font-medium'
                : 'bg-zinc-950/80 border border-zinc-850 text-zinc-200 space-y-3'
            }`}>
              <div className="whitespace-pre-wrap">{m.text}</div>

              {m.sender === 'bot' && m.provider && (
                <div className="text-[10px] text-zinc-500 font-mono flex items-center space-x-1 pt-1">
                  <span>Engine:</span>
                  <span className="text-zinc-400 font-medium">{m.provider}</span>
                </div>
              )}

              {/* Citations block */}
              {m.citations && m.citations.length > 0 && (
                <div className="pt-2.5 border-t border-zinc-850/80 space-y-2">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 flex items-center space-x-1">
                    <Bookmark className="w-3 h-3 text-sky-400" />
                    <span>Grounding Citations ({m.citations.length}):</span>
                  </span>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {m.citations.map((c, cIdx) => {
                      const isExpanded = expandedCitations[`${m.id}_${cIdx}`];
                      return (
                        <div 
                          key={cIdx}
                          className="bg-zinc-900/90 border border-zinc-800/80 rounded-lg p-2.5 text-[11px] space-y-1.5"
                        >
                          <div 
                            className="flex items-center justify-between cursor-pointer select-none"
                            onClick={() => toggleCitation(m.id, cIdx)}
                          >
                            <span className="font-medium text-zinc-300 flex items-center space-x-1 font-mono">
                              <FileText className="w-3 h-3 text-sky-400" />
                              <span>pg {c.page_number}</span>
                            </span>
                            <div className="flex items-center space-x-1.5 text-zinc-500 font-mono text-[10px]">
                              <span>Rel: {(c.relevance * 100).toFixed(0)}%</span>
                              {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                            </div>
                          </div>

                          <p className={`text-zinc-400 text-xs italic ${isExpanded ? '' : 'line-clamp-2'}`}>
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
              <div className="w-6 h-6 rounded-md bg-zinc-800 border border-zinc-700 flex items-center justify-center text-zinc-300 shrink-0 mt-0.5">
                <User className="w-3.5 h-3.5" />
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex items-center space-x-3">
            <div className="w-6 h-6 rounded-md bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-400 shrink-0">
              <Bot className="w-3.5 h-3.5" />
            </div>
            <div className="bg-zinc-950/80 border border-zinc-850 rounded-xl p-3 text-xs text-zinc-400 flex items-center space-x-2">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-sky-400" />
              <span>Analyzing document and synthesizing answer...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <form 
        onSubmit={(e) => { e.preventDefault(); handleSend(); }}
        className="p-3 border-t border-zinc-850 bg-zinc-950/60 flex items-center space-x-2"
      >
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question about this document..."
          className="flex-1 bg-zinc-900/90 border border-zinc-800 rounded-lg px-3.5 py-2 text-xs text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:border-zinc-700"
        />
        <button
          type="submit"
          disabled={!question.trim() || isLoading}
          className="bg-zinc-100 hover:bg-white disabled:opacity-40 text-zinc-950 px-3.5 py-2 rounded-lg font-medium transition flex items-center space-x-1 shadow-sm"
        >
          <CornerDownLeft className="w-3.5 h-3.5" />
          <span className="hidden sm:inline text-xs">Ask</span>
        </button>
      </form>
    </div>
  );
});

export default RagChat;
