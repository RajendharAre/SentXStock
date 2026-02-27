import { useState, useEffect, useRef } from 'react';
import { Send, Loader2, Bot, User, Trash2 } from 'lucide-react';
import { sendChat, getChatHistory, clearChat } from '../services/api';

export default function Chat() {
  const [msgs, setMsgs] = useState([]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    (async () => {
      try {
        const r = await getChatHistory();
        if (r.data?.history?.length)
          setMsgs(r.data.history.map((m) => ({ role: m.role, text: m.content })));
      } catch {}
    })();
  }, []);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [msgs]);

  const send = async () => {
    const t = input.trim();
    if (!t || busy) return;
    setMsgs((p) => [...p, { role: 'user', text: t }]);
    setInput('');
    setBusy(true);
    try {
      const r = await sendChat(t);
      setMsgs((p) => [...p, { role: 'assistant', text: r.data?.response || 'No response.' }]);
    } catch (e) {
      setMsgs((p) => [...p, { role: 'assistant', text: e.response?.data?.message || 'Error.' }]);
    } finally { setBusy(false); }
  };

  const nuke = async () => { try { await clearChat(); } catch {} setMsgs([]); };
  const onKey = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } };

  const prompts = [
    'What is the overall market sentiment?',
    'Should I buy AAPL right now?',
    'Explain my portfolio allocation',
    'What are the biggest risks today?',
  ];

  return (
    <div className="flex flex-col h-[calc(100vh-7.5rem)]">
      {/* Header strip */}
      <div className="flex items-center justify-between mb-3">
        <h1 className="text-[18px] font-semibold text-[var(--c-text)]">Chat</h1>
        {msgs.length > 0 && (
          <button onClick={nuke} className="flex items-center gap-1 text-[11px] text-[var(--c-dimmer)] hover:text-[#ef4444] transition-colors">
            <Trash2 className="w-3 h-3" /> Clear
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto card p-4 space-y-3 mb-3">
        {/* empty */}
        {msgs.length === 0 && !busy && (
          <div className="flex flex-col items-center justify-center h-full gap-5">
            <div className="w-10 h-10 rounded-lg bg-[var(--c-border)] flex items-center justify-center">
              <Bot className="w-5 h-5 text-[#2563eb]" />
            </div>
            <p className="text-[13px] text-[var(--c-dim)]">Ask anything about the market.</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-md">
              {prompts.map((p, i) => (
                <button
                  key={i}
                  onClick={() => setInput(p)}
                  className="text-left text-[11px] text-[var(--c-dim)] p-2.5 rounded-md border border-[var(--c-border)] hover:border-[var(--c-border2)] hover:text-[var(--c-muted)] transition-colors"
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
        )}

        {msgs.map((m, i) => (
          <div key={i} className={`flex gap-2.5 ${m.role === 'user' ? 'justify-end' : ''}`}>
            {m.role === 'assistant' && (
              <div className="w-6 h-6 rounded-md bg-[var(--c-border)] flex items-center justify-center shrink-0 mt-0.5">
                <Bot className="w-3 h-3 text-[#2563eb]" />
              </div>
            )}
            <div
              className={`max-w-[72%] px-3.5 py-2.5 text-[13px] leading-relaxed whitespace-pre-wrap ${
                m.role === 'user'
                  ? 'bg-[#2563eb] text-white rounded-xl rounded-br-sm'
                  : 'bg-[var(--c-surface)] text-[var(--c-text)] border border-[var(--c-border)] rounded-xl rounded-bl-sm'
              }`}
            >
              {m.text}
            </div>
            {m.role === 'user' && (
              <div className="w-6 h-6 rounded-md bg-[var(--c-border)] flex items-center justify-center shrink-0 mt-0.5">
                <User className="w-3 h-3 text-[var(--c-muted)]" />
              </div>
            )}
          </div>
        ))}

        {busy && (
          <div className="flex gap-2.5">
            <div className="w-6 h-6 rounded-md bg-[var(--c-border)] flex items-center justify-center shrink-0">
              <Bot className="w-3 h-3 text-[#2563eb]" />
            </div>
            <div className="bg-[#0d1320] border border-[#151d2e] rounded-xl rounded-bl-sm px-3.5 py-2.5">
              <div className="flex gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-[#374151] animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-1.5 h-1.5 rounded-full bg-[#374151] animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-1.5 h-1.5 rounded-full bg-[#374151] animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      {/* Input bar */}
      <div className="card flex items-end gap-2 p-2.5">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKey}
          placeholder="Ask about sentiment, tickers, strategy…"
          rows={1}
          className="flex-1 bg-transparent text-[13px] text-[var(--c-text)] placeholder-[var(--c-dimmer)] resize-none outline-none py-1.5 px-2 max-h-28"
        />
        <button
          onClick={send}
          disabled={!input.trim() || busy}
          className="w-8 h-8 rounded-md bg-[#2563eb] hover:bg-[#1d4ed8] text-white flex items-center justify-center
            disabled:opacity-25 disabled:cursor-default transition-colors shrink-0"
        >
          <Send className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}
