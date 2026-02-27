/**
 * AI Advisor — Chat Enhancement (Module 7)
 *
 * Features:
 *  - Markdown rendering in AI bubbles (headings, bold, lists, tables, code, links)
 *  - Source badge: Gemini AI | Sentiment Engine | No Data
 *  - No-data fallback: curated NSE/Indian finance resource links
 *  - Indian market focused prompt chips
 *  - Smooth auto-scroll, keyboard shortcut (Enter to send, Shift+Enter = newline)
 *  - Clear history with confirmation
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Send, Bot, User, Trash2, Zap, BookOpen,
  ExternalLink, AlertCircle, Sparkles,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { sendChat, getChatHistory, clearChat } from '../services/api';

// ── NSE / Indian finance resource links ────────────────────────
const NSE_RESOURCES = [
  { label: 'NSE India — Live Market',       url: 'https://www.nseindia.com/' },
  { label: 'Economic Times Markets',        url: 'https://economictimes.indiatimes.com/markets' },
  { label: 'Moneycontrol — NSE/BSE',        url: 'https://www.moneycontrol.com/markets/' },
  { label: 'BSE India — Sensex',            url: 'https://www.bseindia.com/' },
  { label: 'SEBI Latest Circulars',         url: 'https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doListing=yes&sid=2&ssid=108&smid=0' },
  { label: 'Value Research — Mutual Funds', url: 'https://www.valueresearchonline.com/' },
];

// ── Prompt chips — Indian market focused ──────────────────────
const PROMPT_CHIPS = [
  { label: 'Nifty 50 sentiment today?',         icon: '📊' },
  { label: 'Should I buy TCS right now?',       icon: '💡' },
  { label: 'Explain my portfolio allocation',   icon: '🧾' },
  { label: 'Risks for Indian IT stocks?',       icon: '⚠️' },
  { label: 'Compare HDFC Bank vs ICICI Bank',   icon: '⚖️' },
  { label: 'Best sectors to invest in now?',   icon: '🏭' },
];

// ── Method badge ──────────────────────────────────────────────
function MethodBadge({ method }) {
  if (method === 'gemini') {
    return (
      <span className="inline-flex items-center gap-1 text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded border border-indigo-500/25 bg-indigo-500/10 text-indigo-400">
        <Sparkles className="w-2.5 h-2.5" /> Gemini AI
      </span>
    );
  }
  if (method === 'template') {
    return (
      <span className="inline-flex items-center gap-1 text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded border border-amber-500/25 bg-amber-500/10 text-amber-400">
        <Zap className="w-2.5 h-2.5" /> Sentiment Engine
      </span>
    );
  }
  if (method === 'no_data') {
    return (
      <span className="inline-flex items-center gap-1 text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded border border-[var(--c-border2)] bg-[var(--c-ghost)] text-[var(--c-dim)]">
        <BookOpen className="w-2.5 h-2.5" /> Resources
      </span>
    );
  }
  return null;
}

// ── No-data fallback card ─────────────────────────────────────
function NoDataResources() {
  return (
    <div className="mt-3 rounded-xl border border-[var(--c-border)] bg-[var(--c-bg)] p-3.5 space-y-2">
      <div className="flex items-center gap-1.5 text-[11px] font-semibold text-[var(--c-sub)]">
        <BookOpen className="w-3.5 h-3.5" />
        Suggested NSE & Indian Finance Resources
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
        {NSE_RESOURCES.map(({ label, url }) => (
          <a
            key={url}
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-[11px] text-indigo-400 hover:text-indigo-300 hover:underline transition-colors py-1 px-2 rounded hover:bg-indigo-500/10"
          >
            <ExternalLink className="w-3 h-3 flex-shrink-0" />
            {label}
          </a>
        ))}
      </div>
    </div>
  );
}

// ── Markdown renderer for AI bubbles ──────────────────────────
const PROSE_COMPONENTS = {
  // Headings
  h1: ({ children }) => <h1 className="text-[15px] font-bold text-[var(--c-text)] mt-3 mb-1 border-b border-[var(--c-border)] pb-1">{children}</h1>,
  h2: ({ children }) => <h2 className="text-[13px] font-bold text-[var(--c-text)] mt-2.5 mb-1">{children}</h2>,
  h3: ({ children }) => <h3 className="text-[12px] font-semibold text-[var(--c-sub)] mt-2 mb-0.5">{children}</h3>,
  // Paragraphs
  p: ({ children }) => <p className="text-[13px] text-[var(--c-text)] leading-relaxed mb-2 last:mb-0">{children}</p>,
  // Bold / italic
  strong: ({ children }) => <strong className="font-bold text-[var(--c-text)]">{children}</strong>,
  em: ({ children }) => <em className="italic text-[var(--c-sub)]">{children}</em>,
  // Lists
  ul: ({ children }) => <ul className="list-disc list-outside pl-4 space-y-0.5 mb-2 text-[13px]">{children}</ul>,
  ol: ({ children }) => <ol className="list-decimal list-outside pl-4 space-y-0.5 mb-2 text-[13px]">{children}</ol>,
  li: ({ children }) => <li className="text-[var(--c-text)] leading-relaxed">{children}</li>,
  // Code
  code: ({ inline, children }) =>
    inline
      ? <code className="mono text-[11px] bg-[var(--c-ghost)] text-amber-300 px-1 py-0.5 rounded">{children}</code>
      : <code className="block mono text-[11px] bg-[var(--c-bg)] text-emerald-300 p-3 rounded-lg overflow-x-auto border border-[var(--c-border)] my-2">{children}</code>,
  pre: ({ children }) => <>{children}</>,
  // Tables
  table: ({ children }) => (
    <div className="overflow-x-auto my-2 rounded-lg border border-[var(--c-border)]">
      <table className="w-full text-[12px]">{children}</table>
    </div>
  ),
  thead: ({ children }) => <thead className="bg-[var(--c-surface2)] border-b border-[var(--c-border)]">{children}</thead>,
  tbody: ({ children }) => <tbody>{children}</tbody>,
  tr: ({ children }) => <tr className="border-b border-[var(--c-border)] last:border-none hover:bg-[var(--c-ghost)] transition-colors">{children}</tr>,
  th: ({ children }) => <th className="text-left px-3 py-1.5 font-semibold uppercase tracking-wide text-[10px] text-[var(--c-dimmer)]">{children}</th>,
  td: ({ children }) => <td className="px-3 py-1.5 text-[var(--c-text)]">{children}</td>,
  // Links — always open external
  a: ({ href, children }) => (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="text-indigo-400 hover:text-indigo-300 underline underline-offset-2 inline-flex items-center gap-0.5"
    >
      {children}
      <ExternalLink className="w-2.5 h-2.5 inline flex-shrink-0" />
    </a>
  ),
  // Blockquote
  blockquote: ({ children }) => (
    <blockquote className="border-l-2 border-indigo-500/50 pl-3 my-2 text-[var(--c-sub)] italic text-[12px]">
      {children}
    </blockquote>
  ),
  // HR
  hr: () => <hr className="border-[var(--c-border)] my-3" />,
};

function AiMessageContent({ text, method, dataUsed }) {
  return (
    <div>
      {/* Markdown body */}
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={PROSE_COMPONENTS}>
        {text}
      </ReactMarkdown>

      {/* No-data resource links */}
      {!dataUsed && method !== 'gemini' && <NoDataResources />}

      {/* Source badge */}
      <div className="flex items-center gap-1.5 mt-2 pt-2 border-t border-[var(--c-border)]">
        <MethodBadge method={dataUsed === false && method !== 'gemini' ? 'no_data' : method} />
        <span className="text-[9px] text-[var(--c-dimmer)]">AI can make mistakes, please go through the real data currently.</span>
      </div>
    </div>
  );
}

// ── Typing indicator ──────────────────────────────────────────
function TypingDots() {
  return (
    <div className="flex gap-2.5">
      <div className="w-6 h-6 rounded-md bg-[var(--c-border)] flex items-center justify-center shrink-0">
        <Bot className="w-3 h-3 text-[#2563eb]" />
      </div>
      <div className="bg-[var(--c-surface)] border border-[var(--c-border)] rounded-xl rounded-bl-sm px-4 py-3">
        <div className="flex gap-1 items-center">
          <span className="w-1.5 h-1.5 rounded-full bg-[var(--c-border2)] animate-bounce" style={{ animationDelay: '0ms' }} />
          <span className="w-1.5 h-1.5 rounded-full bg-[var(--c-border2)] animate-bounce" style={{ animationDelay: '150ms' }} />
          <span className="w-1.5 h-1.5 rounded-full bg-[var(--c-border2)] animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
      </div>
    </div>
  );
}

// ── Main Chat component ───────────────────────────────────────
export default function Chat() {
  const [msgs, setMsgs]   = useState([]);   // { role, text, method, dataUsed }
  const [input, setInput] = useState('');
  const [busy, setBusy]   = useState(false);
  const [error, setError] = useState(null);
  const endRef  = useRef(null);
  const textRef = useRef(null);

  // Load history on mount
  useEffect(() => {
    (async () => {
      try {
        const r = await getChatHistory();
        // history is a plain array: [{question, answer, timestamp}]
        const hist = Array.isArray(r.data) ? r.data : (r.data?.history || []);
        if (hist.length) {
          const rebuilt = hist.flatMap(m => [
            { role: 'user',      text: m.question  || m.content || '' },
            { role: 'assistant', text: m.answer    || m.content || '', method: 'gemini', dataUsed: true },
          ]);
          setMsgs(rebuilt);
        }
      } catch {}
    })();
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [msgs, busy]);

  const send = useCallback(async () => {
    const t = input.trim();
    if (!t || busy) return;
    setInput('');
    setError(null);
    setMsgs(p => [...p, { role: 'user', text: t }]);
    setBusy(true);
    // focus textarea back
    setTimeout(() => textRef.current?.focus(), 50);
    try {
      const r = await sendChat(t);
      const d = r.data;
      // server returns { answer, method, data_used, timestamp }
      const text     = d?.answer || d?.response || 'No response received.';
      const method   = d?.method   || 'template';
      const dataUsed = d?.data_used ?? true;
      setMsgs(p => [...p, { role: 'assistant', text, method, dataUsed }]);
    } catch (e) {
      const msg = e.response?.data?.error || e.response?.data?.message || 'The AI advisor couldn\'t respond. Please ensure the backend is running.';
      setError(msg);
      setMsgs(p => [...p, { role: 'assistant', text: `**Error:** ${msg}`, method: 'error', dataUsed: false }]);
    } finally {
      setBusy(false);
    }
  }, [input, busy]);

  const nuke = async () => {
    try { await clearChat(); } catch {}
    setMsgs([]);
    setError(null);
  };

  const onKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
  };

  // Auto-resize textarea
  const handleInputChange = (e) => {
    setInput(e.target.value);
    const el = e.target;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 112) + 'px';
  };

  return (
    <div className="flex flex-col h-[calc(100vh-7.5rem)]">

      {/* ── Header ── */}
      <div className="flex items-center justify-between mb-3 flex-shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-[#2563eb]/20 border border-[#2563eb]/30 flex items-center justify-center">
            <Bot className="w-3.5 h-3.5 text-[#60a5fa]" />
          </div>
          <div>
            <h1 className="text-[15px] font-bold text-[var(--c-text)] leading-none">AI Advisor</h1>
            <p className="text-[10px] text-[var(--c-dim)] mt-0.5">Gemini AI · NSE Sentiment Engine · Indian Markets</p>
          </div>
        </div>
        {msgs.length > 0 && (
          <button
            onClick={nuke}
            className="flex items-center gap-1 text-[11px] text-[var(--c-dimmer)] hover:text-rose-400 transition-colors px-2 py-1 rounded hover:bg-rose-500/10"
          >
            <Trash2 className="w-3 h-3" /> Clear chat
          </button>
        )}
      </div>

      {/* ── Messages area ── */}
      <div className="flex-1 overflow-y-auto card p-4 space-y-4 mb-3">

        {/* Empty state */}
        {msgs.length === 0 && !busy && (
          <div className="flex flex-col items-center justify-center h-full gap-6 py-8">
            <div className="flex flex-col items-center gap-3">
              <div className="w-12 h-12 rounded-2xl bg-[#2563eb]/15 border border-[#2563eb]/25 flex items-center justify-center">
                <Bot className="w-6 h-6 text-[#60a5fa]" />
              </div>
              <div className="text-center">
                <p className="text-[14px] font-semibold text-[var(--c-text)]">AI Market Advisor</p>
                <p className="text-[12px] text-[var(--c-dim)] mt-1 max-w-xs leading-relaxed">
                  Ask me anything about NSE stocks, portfolio strategy,
                  sentiment analysis, or Indian market trends.
                </p>
              </div>
            </div>

            {/* Prompt chips */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-lg">
              {PROMPT_CHIPS.map(({ label, icon }) => (
                <button
                  key={label}
                  onClick={() => { setInput(label); textRef.current?.focus(); }}
                  className="flex items-center gap-2 text-left text-[11px] text-[var(--c-dim)] p-2.5 rounded-xl border border-[var(--c-border)] hover:border-[#2563eb]/40 hover:bg-[#2563eb]/5 hover:text-[var(--c-sub)] transition-all"
                >
                  <span className="text-[13px] flex-shrink-0">{icon}</span>
                  {label}
                </button>
              ))}
            </div>

            <div className="flex items-start gap-2 px-4 py-3 rounded-xl border border-amber-500/20 bg-amber-500/5 max-w-lg">
              <AlertCircle className="w-3.5 h-3.5 text-amber-400 flex-shrink-0 mt-0.5" />
              <p className="text-[10px] text-amber-300/80 leading-relaxed">
                AI can make mistakes, please go through the real data currently.
              </p>
            </div>
          </div>
        )}

        {/* Messages */}
        {msgs.map((m, i) => (
          <div key={i} className={`flex gap-2.5 ${m.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
            {/* Avatar */}
            <div className={`w-6 h-6 rounded-md flex items-center justify-center shrink-0 mt-1 ${
              m.role === 'user'
                ? 'bg-[#2563eb]/20 border border-[#2563eb]/30'
                : 'bg-[var(--c-border)] border border-[var(--c-border2)]'
            }`}>
              {m.role === 'user'
                ? <User className="w-3 h-3 text-[#60a5fa]" />
                : <Bot className="w-3 h-3 text-[#2563eb]" />}
            </div>

            {/* Bubble */}
            <div className={`max-w-[76%] ${
              m.role === 'user'
                ? 'bg-[#2563eb] text-white rounded-xl rounded-tr-sm px-4 py-2.5 text-[13px] leading-relaxed'
                : 'bg-[var(--c-surface)] border border-[var(--c-border)] rounded-xl rounded-tl-sm px-4 py-3'
            }`}>
              {m.role === 'user' ? (
                <span className="whitespace-pre-wrap">{m.text}</span>
              ) : (
                <AiMessageContent
                  text={m.text}
                  method={m.method}
                  dataUsed={m.dataUsed}
                />
              )}
            </div>
          </div>
        ))}

        {/* Typing indicator */}
        {busy && <TypingDots />}

        {/* Error notice */}
        {error && !busy && (
          <div className="flex items-center gap-2 text-[11px] text-rose-400 px-2">
            <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
            {error}
          </div>
        )}

        <div ref={endRef} />
      </div>

      {/* ── Input bar ── */}
      <div className="card flex items-end gap-2 p-2.5 flex-shrink-0">
        <textarea
          ref={textRef}
          value={input}
          onChange={handleInputChange}
          onKeyDown={onKey}
          placeholder="Ask about NSE sentiment, stocks, portfolio strategy… (Enter to send)"
          rows={1}
          style={{ height: 'auto' }}
          className="flex-1 bg-transparent text-[13px] text-[var(--c-text)] placeholder-[var(--c-placeholder)] resize-none outline-none py-1.5 px-2 max-h-28 leading-relaxed"
        />
        <button
          onClick={send}
          disabled={!input.trim() || busy}
          className="w-8 h-8 rounded-lg bg-[#2563eb] hover:bg-[#1d4ed8] text-white flex items-center justify-center disabled:opacity-25 disabled:cursor-default transition-colors shrink-0 mb-0.5"
          title="Send (Enter)"
        >
          <Send className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Footer hint */}
      <p className="text-center text-[10px] text-[var(--c-dimmer)] mt-1.5 flex-shrink-0">
        Enter to send · Shift+Enter for new line · Powered by Gemini AI + NSE Sentiment Engine
      </p>
    </div>
  );
}

