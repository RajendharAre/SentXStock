/**
 * Home Page — SentXStock Indian Market Platform
 *
 * Sections:
 *   1. Hero
 *   2. How It Works (3-step)
 *   3. Platform Capabilities
 *   4. Strategy Explanation
 *   5. Performance Statistics
 *   6. Supported Sectors
 *   7. FAQ Accordion
 *   8. CTA footer strip
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  TrendingUp, BarChart2, ShieldCheck, Brain, Database,
  FileText, ChevronDown, ChevronRight, Activity,
  Search, Layers, LineChart, BookOpen, AlertCircle,
} from 'lucide-react';

// ── Reusable subsections ──────────────────────────────────────────────────────

function SectionLabel({ children }) {
  return (
    <span className="inline-block text-[11px] font-semibold tracking-widest uppercase text-indigo-400 mb-3">
      {children}
    </span>
  );
}

function SectionHeading({ children }) {
  return (
    <h2 className="text-2xl sm:text-3xl font-bold text-[var(--c-text)] leading-tight">
      {children}
    </h2>
  );
}

function SectionSub({ children }) {
  return (
    <p className="mt-3 text-[var(--c-muted)] text-sm sm:text-base max-w-2xl">
      {children}
    </p>
  );
}

// ── Step card (How It Works) ──────────────────────────────────────────────────

function StepCard({ number, icon: Icon, title, description }) {
  return (
    <div className="relative flex flex-col gap-4 rounded-xl border border-[var(--c-border)] bg-[var(--c-surface)] p-6">
      {/* step number */}
      <span className="absolute top-4 right-4 text-xs font-bold text-[var(--c-dimmer)]">
        0{number}
      </span>
      <div className="w-10 h-10 rounded-lg bg-indigo-600/10 border border-indigo-500/20 flex items-center justify-center">
        <Icon className="w-5 h-5 text-indigo-400" />
      </div>
      <div>
        <h3 className="text-[15px] font-semibold text-[var(--c-text)]">{title}</h3>
        <p className="mt-1.5 text-sm text-[var(--c-muted)] leading-relaxed">{description}</p>
      </div>
    </div>
  );
}

// ── Capability card ───────────────────────────────────────────────────────────

function CapabilityCard({ icon: Icon, title, description, accent }) {
  const accentMap = {
    indigo: 'text-indigo-400 bg-indigo-600/10 border-indigo-500/20',
    emerald:'text-emerald-400 bg-emerald-600/10 border-emerald-500/20',
    amber:  'text-amber-400  bg-amber-600/10  border-amber-500/20',
    rose:   'text-rose-400   bg-rose-600/10   border-rose-500/20',
    sky:    'text-sky-400    bg-sky-600/10    border-sky-500/20',
    violet: 'text-violet-400 bg-violet-600/10 border-violet-500/20',
  };
  const cls = accentMap[accent] || accentMap.indigo;
  return (
    <div className="flex gap-4 rounded-xl border border-[var(--c-border)] bg-[var(--c-surface)] p-5">
      <div className={`shrink-0 w-10 h-10 rounded-lg border flex items-center justify-center ${cls}`}>
        <Icon className="w-5 h-5" />
      </div>
      <div>
        <h3 className="text-[14px] font-semibold text-[var(--c-text)]">{title}</h3>
        <p className="mt-1 text-xs text-[var(--c-muted)] leading-relaxed">{description}</p>
      </div>
    </div>
  );
}

// ── Stat card ─────────────────────────────────────────────────────────────────

function StatCard({ value, label, note }) {
  return (
    <div className="flex flex-col gap-1 rounded-xl border border-[var(--c-border)] bg-[var(--c-surface)] p-5 text-center">
      <span className="text-2xl font-bold text-indigo-400 mono">{value}</span>
      <span className="text-[13px] font-medium text-[var(--c-text)]">{label}</span>
      {note && <span className="text-[11px] text-[var(--c-muted)]">{note}</span>}
    </div>
  );
}

// ── FAQ item ──────────────────────────────────────────────────────────────────

function FAQItem({ question, answer }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border-b border-[var(--c-border)] last:border-0">
      <button
        onClick={() => setOpen(v => !v)}
        className="w-full flex items-center justify-between py-4 text-left gap-4 group"
      >
        <span className="text-[14px] font-medium text-[var(--c-text)] group-hover:text-indigo-400 transition-colors">
          {question}
        </span>
        <span className="shrink-0 text-[var(--c-muted)]">
          {open
            ? <ChevronDown className="w-4 h-4" />
            : <ChevronRight className="w-4 h-4" />}
        </span>
      </button>
      {open && (
        <p className="pb-4 text-sm text-[var(--c-muted)] leading-relaxed">
          {answer}
        </p>
      )}
    </div>
  );
}

// ── Sector badge ──────────────────────────────────────────────────────────────

function SectorBadge({ name, count }) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-[var(--c-border)] bg-[var(--c-surface)] px-4 py-2.5">
      <span className="text-[13px] text-[var(--c-text)]">{name}</span>
      <span className="text-xs font-mono text-[var(--c-muted)]">{count} co.</span>
    </div>
  );
}

// ── Data ──────────────────────────────────────────────────────────────────────

const HOW_IT_WORKS = [
  {
    icon: Search,
    title: 'Select a Company',
    description:
      'Choose from 500 NSE-listed Indian companies across 11 sectors, or search any ticker not in the list for live news-based analysis.',
  },
  {
    icon: Brain,
    title: 'Sentiment Analysis',
    description:
      'The platform fetches today\'s financial news and runs it through FinBERT — a finance-specific language model — to produce a sentiment score from -1 (bearish) to +1 (bullish).',
  },
  {
    icon: BarChart2,
    title: 'Backtesting (Automated)',
    description:
      'Simultaneously, the engine silently runs a 3-year walk-forward backtest on historical price data to validate whether the sentiment-driven strategy would have been profitable.',
  },
  {
    icon: ShieldCheck,
    title: 'Risk-Based Recommendation',
    description:
      'Your portfolio settings (capital, risk preference) are applied to the sentiment score and backtest result to generate a personalised Buy / Hold / Sell recommendation with a confidence percentage.',
  },
  {
    icon: FileText,
    title: 'PDF Report',
    description:
      'Download a full portfolio report including sentiment trend, backtest performance, allocation breakdown, and a timestamped disclaimer — ready for review or presentation.',
  },
];

const CAPABILITIES = [
  {
    icon: Database,
    title: '500 Indian NSE Companies',
    description: 'Curated list of NSE-listed companies covering all major sectors — from large-cap Nifty 50 constituents to mid-cap growth stocks.',
    accent: 'indigo',
  },
  {
    icon: Brain,
    title: 'FinBERT Sentiment Engine',
    description: 'Financial domain-specific BERT model trained on financial news, earnings calls, and analyst reports for high-accuracy sentiment extraction.',
    accent: 'violet',
  },
  {
    icon: LineChart,
    title: 'Hidden Walk-Forward Backtest',
    description: 'Automatically validates the strategy on 3 years of historical NSE data every time you select a company — no manual configuration required.',
    accent: 'emerald',
  },
  {
    icon: ShieldCheck,
    title: 'Risk-Adjusted Allocation',
    description: 'Portfolio allocations are dynamically calculated using your risk preference, confidence score, and position sizing rules — denominated in INR.',
    accent: 'amber',
  },
  {
    icon: Activity,
    title: 'Gemini AI Advisor Chat',
    description: 'Ask any company or market question in plain language. Gemini generates structured, formatted answers. If quota is exceeded, FinBERT metrics are shown instead.',
    accent: 'sky',
  },
  {
    icon: FileText,
    title: 'Downloadable PDF Report',
    description: 'One-click portfolio report generation including sentiment scores, risk metrics, backtest summary, and position recommendations.',
    accent: 'rose',
  },
];

const PERFORMANCE_STATS = [
  { value: '500+',  label: 'Indian NSE Companies',   note: 'Across 11 GICS sectors' },
  { value: '3 Yr',  label: 'Backtest Window',         note: 'Up to January 2026' },
  { value: '11',    label: 'Sector Categories',       note: 'Technology to Metals' },
  { value: 'INR',   label: 'Base Currency',           note: 'Indian Rupees' },
  { value: 'Live',  label: 'News Sentiment',          note: 'Today\'s financial headlines' },
  { value: '95%',   label: 'Backtest Coverage',       note: 'Of Nifty 500 universe' },
];

const SECTORS = [
  { name: 'Technology', count: 45 },
  { name: 'Banking & Finance', count: 80 },
  { name: 'FMCG', count: 40 },
  { name: 'Healthcare', count: 45 },
  { name: 'Energy & Oil', count: 30 },
  { name: 'Infrastructure', count: 30 },
  { name: 'Automobile', count: 30 },
  { name: 'Metals & Mining', count: 29 },
  { name: 'Telecom & Media', count: 20 },
  { name: 'Consumer Discretionary', count: 30 },
  { name: 'Conglomerates', count: 20 },
];

const FAQS = [
  {
    question: 'What data sources does SentXStock use?',
    answer:
      'SentXStock uses financial news APIs for real-time headlines, yfinance for historical NSE price data (OHLCV), and FinBERT for offline sentiment inference. Gemini API is used for natural language chat responses. All pricing data is sourced from NSE via Yahoo Finance.',
  },
  {
    question: 'Are the recommendations actual trading signals?',
    answer:
      'No. SentXStock produces research-grade sentiment analysis and backtested strategy signals for educational and research purposes only. The platform does not execute real trades. Recommendations should not be treated as financial advice. Always consult a SEBI-registered financial advisor before making investment decisions.',
  },
  {
    question: 'What is the difference between Sentiment Score and Confidence Level?',
    answer:
      'The Sentiment Score (-1.0 to +1.0) reflects how bullish or bearish the current news climate is for a company. The Confidence Level (0–100%) represents how strongly the combined model — sentiment, backtest performance, and historical accuracy — agrees on the recommended direction.',
  },
  {
    question: 'Why is the backtest period fixed to January 2026?',
    answer:
      'The historical dataset is curated and validated through January 2026 to ensure data consistency and avoid look-ahead bias. Using a fixed, auditable end date makes backtest results reproducible and comparable across companies.',
  },
  {
    question: 'How does the hidden backtest work?',
    answer:
      'When you select a company, the platform automatically runs a walk-forward backtest in the background using 3 years of historical price and derived sentiment data. The backtest engine simulates trades, tracks portfolio value daily, and computes Sharpe ratio, max drawdown, and win rate — all without requiring any manual input from the user.',
  },
  {
    question: 'What happens if I search for a company not in the 500 list?',
    answer:
      'For companies outside the curated NSE 500 list, SentXStock performs live news sentiment analysis only. Historical backtesting is not available, and performance metrics are derived solely from today\'s news headlines. A basic Buy / Hold / Sell recommendation is still generated.',
  },
  {
    question: 'How is the portfolio allocation calculated?',
    answer:
      'Allocation is computed as: Confidence × Risk Multiplier × (1 / Number of Open Positions). The risk multiplier is 0.5× for Low risk, 1.0× for Medium, and 1.5× for High. No single position can exceed 20% of total capital. All amounts are in Indian Rupees (INR).',
  },
  {
    question: 'Is my data or portfolio information stored anywhere?',
    answer:
      'All portfolio settings are saved locally in your browser (localStorage) and are never transmitted to any external server. Analysis results are cached only for the current session. The platform does not collect any personal or financial data.',
  },
];

// ── Page component ────────────────────────────────────────────────────────────

export default function Home() {
  return (
    <div className="space-y-20 pb-20">

      {/* ── 1. Hero ─────────────────────────────────────────────────────────── */}
      <section className="pt-12 sm:pt-20 lg:pt-24">
        <div className="flex flex-col items-center text-center max-w-3xl mx-auto">

          {/* badges */}
          <div className="flex items-center flex-wrap justify-center gap-2 mb-6">
            <span className="inline-block px-2.5 py-1 rounded-full text-[11px] font-semibold border border-indigo-500/30 bg-indigo-600/10 text-indigo-400 tracking-wide">
              NSE Indian Markets
            </span>
            <span className="inline-block px-2.5 py-1 rounded-full text-[11px] font-semibold border border-[var(--c-border)] text-[var(--c-muted)] tracking-wide">
              500 Companies
            </span>
            <span className="inline-block px-2.5 py-1 rounded-full text-[11px] font-semibold border border-[var(--c-border)] text-[var(--c-muted)] tracking-wide">
              FinBERT Powered
            </span>
          </div>

          {/* headline */}
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-[var(--c-text)] leading-tight tracking-tight">
            Sentiment-Driven
            <br />
            <span className="text-indigo-400">Trading Research</span>
            <br />
            for Indian Markets
          </h1>

          {/* description */}
          <p className="mt-6 text-base sm:text-lg text-[var(--c-muted)] leading-relaxed max-w-2xl">
            SentXStock analyses today&apos;s financial news using FinBERT, runs an automated
            3-year backtest on NSE historical data, and generates risk-adjusted portfolio
            recommendations — all from a single company search.
          </p>

          {/* CTAs */}
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Link
              to="/dashboard"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm transition-colors"
            >
              Open Dashboard
              <ChevronRight className="w-4 h-4" />
            </Link>
            <Link
              to="/settings"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-lg border border-[var(--c-border)] bg-[var(--c-surface)] hover:border-[var(--c-border2)] text-[var(--c-sub)] font-semibold text-sm transition-colors"
            >
              Configure Portfolio
            </Link>
          </div>

          {/* disclaimer ribbon */}
          <div className="mt-8 w-full flex items-start gap-2.5 rounded-lg border border-amber-500/20 bg-amber-500/5 p-3.5 text-left">
            <AlertCircle className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" />
            <p className="text-xs text-amber-300/80 leading-relaxed">
              AI can make mistakes, please go through the real data currently.
            </p>
          </div>

        </div>
      </section>

      {/* ── 2. How It Works ─────────────────────────────────────────────────── */}
      <section>
        <SectionLabel>Process</SectionLabel>
        <SectionHeading>How SentXStock Works</SectionHeading>
        <SectionSub>
          From company selection to a downloadable portfolio report — five automated steps
          that run in under two minutes.
        </SectionSub>

        <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
          {HOW_IT_WORKS.map((step, i) => (
            <StepCard key={i} number={i + 1} {...step} />
          ))}
        </div>
      </section>

      {/* ── 3. Platform Capabilities ────────────────────────────────────────── */}
      <section>
        <SectionLabel>Capabilities</SectionLabel>
        <SectionHeading>What the Platform Provides</SectionHeading>
        <SectionSub>
          Each component of the platform is independently modular and designed to operate
          with or without an active internet connection.
        </SectionSub>

        <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {CAPABILITIES.map((cap, i) => (
            <CapabilityCard key={i} {...cap} />
          ))}
        </div>
      </section>

      {/* ── 4. Strategy Explanation ────────────────────────────────────────── */}
      <section>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
          <div>
            <SectionLabel>Strategy</SectionLabel>
            <SectionHeading>Sentiment-Momentum Blend</SectionHeading>
            <SectionSub>
              The core strategy combines real-time news sentiment with price-based
              technical signals to produce a composite signal used for both live
              recommendations and historical backtesting.
            </SectionSub>

            <div className="mt-6 space-y-4">
              {[
                {
                  label: 'News Sentiment (FinBERT)',
                  weight: '40%',
                  description:
                    'Financial news headlines are scored by FinBERT in the range [-1, +1]. Scores are aggregated and weighted by recency.',
                },
                {
                  label: 'Price Momentum (RSI + ROC)',
                  weight: '30%',
                  description:
                    '14-day relative strength index and 5-day rate-of-change are combined to capture short-term price trend direction.',
                },
                {
                  label: 'Moving Average Crossover',
                  weight: '20%',
                  description:
                    'The 5-day / 20-day MA crossover ratio signals trend reversals and confirms directional bias.',
                },
                {
                  label: 'Volume Anomaly',
                  weight: '10%',
                  description:
                    'Abnormal volume relative to the 20-day average, weighted by price direction, captures institutional activity.',
                },
              ].map((item, i) => (
                <div key={i} className="flex gap-4 rounded-lg border border-[var(--c-border)] bg-[var(--c-surface)] p-4">
                  <div className="shrink-0 w-14 text-center">
                    <span className="text-xs font-bold text-indigo-400 mono">{item.weight}</span>
                  </div>
                  <div>
                    <p className="text-[13px] font-semibold text-[var(--c-text)]">{item.label}</p>
                    <p className="mt-0.5 text-xs text-[var(--c-muted)] leading-relaxed">{item.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Signal thresholds panel */}
          <div className="rounded-xl border border-[var(--c-border)] bg-[var(--c-surface)] p-6 space-y-5">
            <div>
              <h3 className="text-[13px] font-semibold text-[var(--c-sub)] uppercase tracking-wider mb-3">
                Signal Thresholds
              </h3>
              <div className="space-y-2.5">
                {[
                  { label: 'Strong Buy',  range: '> +0.30',  color: 'text-emerald-400', bar: 'bg-emerald-500', w: 'w-full' },
                  { label: 'Buy',         range: '+0.10 to +0.30', color: 'text-green-400',  bar: 'bg-green-500',  w: 'w-3/4' },
                  { label: 'Hold',        range: '-0.10 to +0.10', color: 'text-amber-400',  bar: 'bg-amber-500',  w: 'w-1/2' },
                  { label: 'Sell',        range: '-0.30 to -0.10', color: 'text-orange-400', bar: 'bg-orange-500', w: 'w-1/4' },
                  { label: 'Strong Sell', range: '< -0.30',  color: 'text-rose-400',   bar: 'bg-rose-500',   w: 'w-1/6' },
                ].map((row, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <span className={`w-20 shrink-0 text-xs font-semibold ${row.color}`}>{row.label}</span>
                    <div className="flex-1 h-1.5 rounded-full bg-[var(--c-border2)]">
                      <div className={`h-1.5 rounded-full ${row.bar} ${row.w}`} />
                    </div>
                    <span className="w-28 shrink-0 text-right text-xs mono text-[var(--c-muted)]">{row.range}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="border-t border-[var(--c-border)] pt-5">
              <h3 className="text-[13px] font-semibold text-[var(--c-sub)] uppercase tracking-wider mb-3">
                Risk Multipliers
              </h3>
              <div className="space-y-2">
                {[
                  { risk: 'Low',    mult: '0.5×', desc: 'Smaller positions, wider hold range' },
                  { risk: 'Medium', mult: '1.0×', desc: 'Standard thresholds' },
                  { risk: 'High',   mult: '1.5×', desc: 'Larger positions, tighter triggers' },
                ].map((r, i) => (
                  <div key={i} className="flex items-center gap-3 text-xs">
                    <span className="w-14 font-medium text-[var(--c-text)]">{r.risk}</span>
                    <span className="w-8 font-bold mono text-indigo-400">{r.mult}</span>
                    <span className="text-[var(--c-muted)]">{r.desc}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="border-t border-[var(--c-border)] pt-5">
              <h3 className="text-[13px] font-semibold text-[var(--c-sub)] uppercase tracking-wider mb-3">
                Backtest Parameters
              </h3>
              <div className="space-y-2 text-xs">
                {[
                  ['Window',           '3 years ending Jan 2026'],
                  ['Slippage',         '5 basis points per trade'],
                  ['Max Position',     '20% of portfolio (per stock)'],
                  ['Max Open Positions','20 concurrent'],
                  ['Benchmark',        'Nifty 50 (^NSEI)'],
                  ['Currency',         'Indian Rupees (INR)'],
                ].map(([k, v], i) => (
                  <div key={i} className="flex justify-between">
                    <span className="text-[var(--c-muted)]">{k}</span>
                    <span className="text-[var(--c-text)] font-medium">{v}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── 5. Performance Statistics ───────────────────────────────────────── */}
      <section>
        <SectionLabel>Coverage</SectionLabel>
        <SectionHeading>Platform Statistics</SectionHeading>
        <SectionSub>
          Key numbers that define the scope of this research platform.
        </SectionSub>

        <div className="mt-8 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
          {PERFORMANCE_STATS.map((s, i) => (
            <StatCard key={i} {...s} />
          ))}
        </div>
      </section>

      {/* ── 6. Sectors ─────────────────────────────────────────────────────── */}
      <section>
        <SectionLabel>Universe</SectionLabel>
        <SectionHeading>Supported Sectors</SectionHeading>
        <SectionSub>
          Covers all major NSE market segments — from large-cap IT services to
          mid-cap energy and metals.
        </SectionSub>

        <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
          {SECTORS.map((s, i) => (
            <SectorBadge key={i} {...s} />
          ))}
        </div>
      </section>

      {/* ── 7. FAQ ──────────────────────────────────────────────────────────── */}
      <section>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
          <div className="lg:col-span-1">
            <SectionLabel>FAQ</SectionLabel>
            <SectionHeading>Frequently Asked Questions</SectionHeading>
            <SectionSub>
              Common questions about data sources, methodology, and platform behaviour.
            </SectionSub>
            <Link
              to="/dashboard"
              className="mt-6 inline-flex items-center gap-2 text-sm text-indigo-400 hover:text-indigo-300 transition-colors font-medium"
            >
              Go to Dashboard
              <ChevronRight className="w-4 h-4" />
            </Link>
          </div>
          <div className="lg:col-span-2 rounded-xl border border-[var(--c-border)] bg-[var(--c-surface)] px-6 divide-y divide-[var(--c-border)]">
            {FAQS.map((faq, i) => (
              <FAQItem key={i} {...faq} />
            ))}
          </div>
        </div>
      </section>

      {/* ── 8. CTA strip ────────────────────────────────────────────────────── */}
      <section>
        <div className="rounded-2xl border border-indigo-500/20 bg-indigo-600/5 p-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
          <div>
            <h3 className="text-lg font-bold text-[var(--c-text)]">
              Start analysing Indian stocks
            </h3>
            <p className="mt-1 text-sm text-[var(--c-muted)]">
              Search any NSE company, get today&apos;s sentiment and a 3-year backtest — in under
              60 seconds.
            </p>
          </div>
          <div className="flex gap-3 shrink-0">
            <Link
              to="/dashboard"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm transition-colors"
            >
              Open Dashboard
              <ChevronRight className="w-4 h-4" />
            </Link>
            <Link
              to="/settings"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg border border-[var(--c-border)] bg-[var(--c-surface)] hover:border-[var(--c-border2)] text-[var(--c-sub)] font-semibold text-sm transition-colors"
            >
              Settings
            </Link>
          </div>
        </div>
      </section>

    </div>
  );
}
