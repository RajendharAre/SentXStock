/**
 * Consult Expert — Real Human SEBI-registered Financial Advisor Booking
 *
 * Flow: Step 1 (Advisor) → Step 2 (Session & Time) → Step 3 (Your Details) → Step 4 (Payment)
 */

import { useState } from 'react';
import {
  User, Phone, Mail, MessageSquare, Calendar, Clock,
  ShieldCheck, Award, ChevronRight, Check, AlertCircle,
  BookOpen, TrendingUp, FileText, CreditCard, PartyPopper,
  BarChart2, Star, Zap,
} from 'lucide-react';

// ── Data ──────────────────────────────────────────────────────────────────────

const EXPERTS = [
  {
    id: 1,
    name: 'Priya Mehta',
    title: 'SEBI Registered Investment Advisor',
    regNo: 'INA000012876',
    experience: '14 years',
    specialisation: ['Equity Research', 'Portfolio Construction', 'NSE Large-Cap'],
    languages: ['English', 'Hindi', 'Gujarati'],
    availability: 'Mon – Fri, 10:00 – 17:00 IST',
    fee: '₹2,500 / session (45 min)',
    rating: 4.9,
    reviews: 213,
  },
  {
    id: 2,
    name: 'Arjun Nair',
    title: 'Certified Financial Planner (CFP)',
    regNo: 'INA000009341',
    experience: '11 years',
    specialisation: ['Mutual Funds', 'SIP Strategy', 'Mid-Cap Growth Stocks'],
    languages: ['English', 'Malayalam', 'Tamil'],
    availability: 'Mon – Sat, 09:00 – 18:00 IST',
    fee: '₹2,000 / session (45 min)',
    rating: 4.8,
    reviews: 174,
  },
  {
    id: 3,
    name: 'Sneha Joshi',
    title: 'Chartered Accountant & SEBI RIA',
    regNo: 'INA000015502',
    experience: '9 years',
    specialisation: ['Tax-Efficient Investing', 'Debt Instruments', 'FMCG & Healthcare Sectors'],
    languages: ['English', 'Marathi', 'Hindi'],
    availability: 'Tue – Sat, 11:00 – 19:00 IST',
    fee: '₹1,800 / session (45 min)',
    rating: 4.7,
    reviews: 98,
  },
];

const SESSION_TYPES = [
  {
    icon: TrendingUp,
    title: 'Portfolio Review',
    description: 'One-on-one review of your current holdings with actionable re-balancing advice.',
    duration: '45 min',
  },
  {
    icon: BookOpen,
    title: 'Investment Planning',
    description: 'Goal-based financial plan — retirement, education corpus, or wealth creation.',
    duration: '60 min',
  },
  {
    icon: FileText,
    title: 'Tax & Compliance',
    description: 'Tax-loss harvesting, LTCG/STCG optimisation, and ITR filing guidance.',
    duration: '45 min',
  },
];

const TIME_SLOTS = [
  '09:00 AM', '10:00 AM', '11:00 AM', '12:00 PM',
  '02:00 PM', '03:00 PM', '04:00 PM', '05:00 PM',
];

// ── Sub-components ────────────────────────────────────────────────────────────

function SectionLabel({ children }) {
  return (
    <span className="inline-block text-[11px] font-semibold tracking-widest uppercase text-indigo-400 mb-3">
      {children}
    </span>
  );
}

function ExpertCard({ expert, selected, onSelect }) {
  return (
    <div
      onClick={() => onSelect(expert)}
      className={`relative rounded-xl border p-5 cursor-pointer transition-all ${
        selected
          ? 'border-indigo-500 bg-indigo-600/5 ring-1 ring-indigo-500/30'
          : 'border-[var(--c-border)] bg-[var(--c-surface)] hover:border-[var(--c-border2)]'
      }`}
    >
      {selected && (
        <span className="absolute top-3 right-3 w-5 h-5 rounded-full bg-indigo-600 flex items-center justify-center">
          <Check className="w-3 h-3 text-white" />
        </span>
      )}

      {/* Avatar placeholder */}
      <div className="w-12 h-12 rounded-full bg-indigo-600/10 border border-indigo-500/20 flex items-center justify-center mb-3">
        <User className="w-6 h-6 text-indigo-400" />
      </div>

      <h3 className="text-[15px] font-bold text-[var(--c-text)]">{expert.name}</h3>
      <p className="text-[12px] text-indigo-400 font-medium mt-0.5">{expert.title}</p>
      <p className="text-[11px] text-[var(--c-muted)] mt-0.5">Reg: {expert.regNo}</p>

      <div className="mt-3 flex flex-wrap gap-1.5">
        {expert.specialisation.map((s) => (
          <span key={s} className="text-[10px] px-2 py-0.5 rounded-full border border-[var(--c-border)] text-[var(--c-muted)] bg-[var(--c-surface2)]">
            {s}
          </span>
        ))}
      </div>

      <div className="mt-4 space-y-1.5 text-[12px]">
        <div className="flex justify-between text-[var(--c-muted)]">
          <span>Experience</span>
          <span className="font-medium text-[var(--c-text)]">{expert.experience}</span>
        </div>
        <div className="flex justify-between text-[var(--c-muted)]">
          <span>Languages</span>
          <span className="font-medium text-[var(--c-text)]">{expert.languages.join(', ')}</span>
        </div>
        <div className="flex justify-between text-[var(--c-muted)]">
          <span>Availability</span>
          <span className="font-medium text-[var(--c-text)]">{expert.availability}</span>
        </div>
        <div className="flex justify-between text-[var(--c-muted)]">
          <span>Fee</span>
          <span className="font-semibold text-emerald-400">{expert.fee}</span>
        </div>
      </div>

      <div className="mt-3 flex items-center gap-1.5">
        <span className="text-[12px] font-bold text-amber-400">{expert.rating}</span>
        <div className="flex gap-0.5">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className={`w-2.5 h-2.5 rounded-sm ${i <= Math.round(expert.rating) ? 'bg-amber-400' : 'bg-[var(--c-border2)]'}`} />
          ))}
        </div>
        <span className="text-[11px] text-[var(--c-muted)]">({expert.reviews} reviews)</span>
      </div>
    </div>
  );
}

function SessionTypeCard({ session, selected, onSelect }) {
  const Icon = session.icon;
  return (
    <div
      onClick={() => onSelect(session)}
      className={`flex gap-4 rounded-xl border p-4 cursor-pointer transition-all ${
        selected
          ? 'border-indigo-500 bg-indigo-600/5 ring-1 ring-indigo-500/30'
          : 'border-[var(--c-border)] bg-[var(--c-surface)] hover:border-[var(--c-border2)]'
      }`}
    >
      <div className={`shrink-0 w-10 h-10 rounded-lg border flex items-center justify-center ${
        selected ? 'bg-indigo-600/10 border-indigo-500/20 text-indigo-400' : 'bg-[var(--c-surface2)] border-[var(--c-border)] text-[var(--c-muted)]'
      }`}>
        <Icon className="w-5 h-5" />
      </div>
      <div className="flex-1">
        <div className="flex items-center justify-between">
          <h3 className="text-[14px] font-semibold text-[var(--c-text)]">{session.title}</h3>
          <div className="flex items-center gap-1 text-[11px] text-[var(--c-muted)]">
            <Clock className="w-3 h-3" />
            {session.duration}
          </div>
        </div>
        <p className="mt-1 text-[12px] text-[var(--c-muted)] leading-relaxed">{session.description}</p>
      </div>
      {selected && (
        <div className="shrink-0 w-5 h-5 rounded-full bg-indigo-600 flex items-center justify-center">
          <Check className="w-3 h-3 text-white" />
        </div>
      )}
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function Consult() {
  const [selectedExpert,  setSelectedExpert]  = useState(null);
  const [selectedSession, setSelectedSession] = useState(null);
  const [selectedDate,    setSelectedDate]    = useState('');
  const [selectedSlot,    setSelectedSlot]    = useState('');
  const [form, setForm] = useState({
    name: '', email: '', phone: '', notes: '', experience: '',
  });
  const [step, setStep] = useState(1); // 1=Expert 2=Session+Time 3=Details 4=Payment

  const canProceed1 = !!selectedExpert;
  const canProceed2 = !!selectedSession && !!selectedDate && !!selectedSlot;
  const canSubmit   = form.name.trim() && form.email.trim() && form.phone.trim() && form.experience;

  // ── Derived fee number for payment ──────────────────────────────────────────
  // Extract just the numeric amount before the first '/' e.g. "₹2,500 / session (45 min)" → "2,500"
  const feeAmount = selectedExpert?.fee?.match(/[\d,]+/)?.[0] ?? '0';

  // ── Reset everything ─────────────────────────────────────────────────────────
  const resetAll = () => {
    setSelectedExpert(null);
    setSelectedSession(null);
    setSelectedDate('');
    setSelectedSlot('');
    setForm({ name: '', email: '', phone: '', notes: '', experience: '' });
    setStep(1);
  };

  // ── Step 4: Payment confirmation (static) ────────────────────────────────────
  if (step === 4) {
    const expLabel = { beginner: 'Beginner', intermediate: 'Intermediate', expert: 'Expert (Advanced)' };
    return (
      <div className="max-w-xl mx-auto pt-10 pb-20 space-y-7">

        {/* ── Success header ── */}
        <div className="text-center space-y-3">
          <div className="relative inline-flex">
            <div className="w-20 h-20 rounded-full bg-emerald-600/10 border-2 border-emerald-500/30 flex items-center justify-center mx-auto">
              <Check className="w-10 h-10 text-emerald-400" />
            </div>
            <span className="absolute -top-1 -right-1 w-7 h-7 rounded-full bg-amber-400 flex items-center justify-center">
              <PartyPopper className="w-4 h-4 text-white" />
            </span>
          </div>
          <h2 className="text-2xl font-extrabold text-[var(--c-text)]">Payment Successful!</h2>
          <p className="text-sm text-[var(--c-muted)] leading-relaxed max-w-sm mx-auto">
            Your session has been booked and payment has been processed. Your assigned SEBI expert will
            send the <strong className="text-emerald-400">meeting link &amp; details</strong> to your
            email address within <strong className="text-[var(--c-sub)]">2 business hours</strong>.
          </p>
        </div>

        {/* ── Payment receipt card ── */}
        <div className="rounded-2xl border border-[var(--c-border)] bg-[var(--c-surface)] overflow-hidden">
          {/* Card header */}
          <div className="flex items-center justify-between px-5 py-4 border-b border-[var(--c-border)] bg-emerald-600/5">
            <div className="flex items-center gap-2">
              <CreditCard className="w-4 h-4 text-emerald-400" />
              <span className="text-[13px] font-semibold text-emerald-400">Payment Receipt</span>
            </div>
            <span className="text-[11px] px-2.5 py-1 rounded-full bg-emerald-600/15 border border-emerald-500/30 text-emerald-400 font-semibold">
              PAID
            </span>
          </div>

          {/* Booking details */}
          <div className="px-5 py-4 space-y-2.5 text-[13px]">
            {[
              ['Advisor',         selectedExpert?.name],
              ['Reg. No.',        selectedExpert?.regNo],
              ['Session Type',    selectedSession?.title],
              ['Duration',        selectedSession?.duration],
              ['Date',            selectedDate],
              ['Time',            `${selectedSlot} IST`],
              ['Your Name',       form.name],
              ['Email',           form.email],
              ['Mobile',          form.phone],
              ['Experience',      expLabel[form.experience] || form.experience],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between gap-4">
                <span className="text-[var(--c-muted)] shrink-0">{k}</span>
                <span className="font-medium text-[var(--c-text)] text-right break-all">{v}</span>
              </div>
            ))}
          </div>

          {/* Fee row */}
          <div className="flex items-center justify-between px-5 py-4 border-t border-[var(--c-border)] bg-[var(--c-surface2)]">
            <span className="text-[13px] font-semibold text-[var(--c-sub)]">Amount Paid</span>
            <span className="text-[18px] font-extrabold text-emerald-400">₹{feeAmount}</span>
          </div>
        </div>

        {/* ── What's next ── */}
        <div className="rounded-xl border border-indigo-500/20 bg-indigo-600/5 p-5 space-y-3">
          <p className="text-[13px] font-semibold text-indigo-400">What happens next?</p>
          <div className="space-y-2.5 text-[12px] text-[var(--c-muted)]">
            {[
              { icon: Mail,     text: `A confirmation email has been sent to ${form.email}` },
              { icon: Clock,    text: 'Your SEBI advisor will send the meeting link within 2 business hours' },
              { icon: Phone,    text: `If you need immediate help, we'll reach you at ${form.phone}` },
              { icon: ShieldCheck, text: 'Session is private, confidential, and conducted over a secure video call' },
            ].map(({ icon: Icon, text }) => (
              <div key={text} className="flex items-start gap-2.5">
                <Icon className="w-3.5 h-3.5 text-indigo-400 mt-0.5 shrink-0" />
                <span>{text}</span>
              </div>
            ))}
          </div>
        </div>

        {/* ── Actions ── */}
        <div className="flex gap-3 pt-1">
          <button
            onClick={resetAll}
            className="flex-1 px-5 py-2.5 rounded-lg border border-[var(--c-border)] text-sm font-semibold text-[var(--c-sub)] hover:border-indigo-500 hover:text-indigo-400 transition-colors"
          >
            Book Another Session
          </button>
          <a
            href="/"
            className="flex-1 text-center px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm transition-colors"
          >
            Back to Home
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-10 pb-16">

      {/* ── Header ── */}
      <div className="pt-2">
        <SectionLabel>Human Advisory</SectionLabel>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-[var(--c-text)] leading-tight">
          Consult a SEBI-Registered Expert
        </h1>
        <p className="mt-3 text-sm text-[var(--c-muted)] max-w-2xl leading-relaxed">
          Speak directly with a verified human financial advisor — not an AI. Get personalised
          guidance on portfolio construction, tax-efficient investing, and NSE market strategy
          from a certified professional.
        </p>

        {/* AI vs Human notice */}
        <div className="mt-5 flex items-start gap-3 rounded-lg border border-emerald-500/20 bg-emerald-600/5 p-4 max-w-2xl">
          <ShieldCheck className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />
          <div>
            <p className="text-[13px] font-semibold text-emerald-400">Verified Human Advisors</p>
            <p className="text-[12px] text-[var(--c-muted)] mt-0.5 leading-relaxed">
              All advisors on this platform hold valid SEBI Registration certificates.
              Sessions are conducted over video call or phone. Looking for the AI assistant?
              Use <strong className="text-[var(--c-sub)]">AI Advisor</strong> in the navigation bar.
            </p>
          </div>
        </div>
      </div>

      {/* ── Step indicator (4 steps) ── */}
      <div className="flex flex-wrap items-center gap-2 text-[12px] font-medium">
        {[
          { n: 1, label: 'Select Advisor' },
          { n: 2, label: 'Session & Time' },
          { n: 3, label: 'Your Details' },
          { n: 4, label: 'Payment' },
        ].map((s, i) => (
          <div key={s.n} className="flex items-center gap-2">
            <button
              onClick={() => {
                if (s.n === 1) setStep(1);
                if (s.n === 2 && canProceed1) setStep(2);
                if (s.n === 3 && canProceed2) setStep(3);
              }}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border transition-colors ${
                step === s.n
                  ? 'border-indigo-500 bg-indigo-600/10 text-indigo-400'
                  : step > s.n
                  ? 'border-emerald-500/30 bg-emerald-600/5 text-emerald-400'
                  : 'border-[var(--c-border)] text-[var(--c-muted)] cursor-default'
              }`}
            >
              {step > s.n ? <Check className="w-3.5 h-3.5" /> : <span>{s.n}</span>}
              {s.label}
            </button>
            {i < 3 && <ChevronRight className="w-3.5 h-3.5 text-[var(--c-dimmer)]" />}
          </div>
        ))}
      </div>

      {/* ══════════ Step 1: Select Expert ══════════ */}
      {step === 1 && (
        <div className="space-y-5">
          <h2 className="text-[16px] font-semibold text-[var(--c-text)]">Choose Your Advisor</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {EXPERTS.map((expert) => (
              <ExpertCard
                key={expert.id}
                expert={expert}
                selected={selectedExpert?.id === expert.id}
                onSelect={setSelectedExpert}
              />
            ))}
          </div>
          <div className="flex justify-end pt-2">
            <button
              disabled={!canProceed1}
              onClick={() => setStep(2)}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Continue — Session Type
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* ══════════ Step 2: Session + Date + Slot ══════════ */}
      {step === 2 && (
        <div className="space-y-7">
          <div>
            <h2 className="text-[16px] font-semibold text-[var(--c-text)] mb-1">
              Session with {selectedExpert?.name}
            </h2>
            <p className="text-[12px] text-[var(--c-muted)]">
              Availability: {selectedExpert?.availability}
            </p>
          </div>

          {/* Session type */}
          <div className="space-y-3">
            <p className="text-[13px] font-semibold text-[var(--c-sub)]">Session Type</p>
            <div className="space-y-3">
              {SESSION_TYPES.map((s) => (
                <SessionTypeCard
                  key={s.title}
                  session={s}
                  selected={selectedSession?.title === s.title}
                  onSelect={setSelectedSession}
                />
              ))}
            </div>
          </div>

          {/* Date picker */}
          <div className="space-y-2">
            <p className="text-[13px] font-semibold text-[var(--c-sub)]">Preferred Date</p>
            <input
              type="date"
              value={selectedDate}
              min={new Date().toISOString().split('T')[0]}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="h-9 rounded-lg border border-[var(--c-border)] bg-[var(--c-surface)] text-[var(--c-text)] text-sm px-3 focus:outline-none focus:border-indigo-500 transition-colors"
            />
          </div>

          {/* Time slots */}
          <div className="space-y-2">
            <p className="text-[13px] font-semibold text-[var(--c-sub)]">Preferred Time Slot (IST)</p>
            <div className="flex flex-wrap gap-2">
              {TIME_SLOTS.map((slot) => (
                <button
                  key={slot}
                  onClick={() => setSelectedSlot(slot)}
                  className={`px-3 py-1.5 rounded-lg border text-[12px] font-medium transition-colors ${
                    selectedSlot === slot
                      ? 'border-indigo-500 bg-indigo-600/10 text-indigo-400'
                      : 'border-[var(--c-border)] text-[var(--c-muted)] hover:border-[var(--c-border2)]'
                  }`}
                >
                  {slot}
                </button>
              ))}
            </div>
          </div>

          <div className="flex justify-between pt-2">
            <button onClick={() => setStep(1)} className="px-4 py-2 rounded-lg border border-[var(--c-border)] text-sm text-[var(--c-muted)] hover:text-[var(--c-sub)] transition-colors">
              Back
            </button>
            <button
              disabled={!canProceed2}
              onClick={() => setStep(3)}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Continue — Your Details
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* ══════════ Step 3: User Details ══════════ */}
      {step === 3 && (
        <form
          onSubmit={(e) => { e.preventDefault(); setStep(4); }}
          className="space-y-7 max-w-xl"
        >
          {/* Booking summary */}
          <div className="rounded-xl border border-[var(--c-border)] bg-[var(--c-surface)] p-5 space-y-2 text-sm">
            <p className="text-[12px] font-semibold text-[var(--c-sub)] uppercase tracking-wide mb-3">Booking Summary</p>
            {[
              ['Advisor',    selectedExpert?.name],
              ['Reg. No.',   selectedExpert?.regNo],
              ['Session',    selectedSession?.title],
              ['Duration',   selectedSession?.duration],
              ['Date',       selectedDate],
              ['Time',       `${selectedSlot} IST`],
              ['Fee',        selectedExpert?.fee],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between">
                <span className="text-[var(--c-muted)]">{k}</span>
                <span className="font-medium text-[var(--c-text)]">{v}</span>
              </div>
            ))}
          </div>

          <div className="space-y-5">
            <h2 className="text-[16px] font-semibold text-[var(--c-text)]">Your Details</h2>

            {/* Name + Phone */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-[12px] font-medium text-[var(--c-sub)]">Full Name *</label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[var(--c-dimmer)]" />
                  <input
                    type="text"
                    placeholder="Rahul Sharma"
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    required
                    className="w-full h-9 pl-8 pr-3 rounded-lg border border-[var(--c-border)] bg-[var(--c-surface)] text-[var(--c-text)] text-sm placeholder:text-[var(--c-placeholder)] focus:outline-none focus:border-indigo-500 transition-colors"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-[12px] font-medium text-[var(--c-sub)]">Mobile Number *</label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[var(--c-dimmer)]" />
                  <input
                    type="tel"
                    placeholder="+91 98765 43210"
                    value={form.phone}
                    onChange={(e) => setForm({ ...form, phone: e.target.value })}
                    required
                    className="w-full h-9 pl-8 pr-3 rounded-lg border border-[var(--c-border)] bg-[var(--c-surface)] text-[var(--c-text)] text-sm placeholder:text-[var(--c-placeholder)] focus:outline-none focus:border-indigo-500 transition-colors"
                  />
                </div>
              </div>
            </div>

            {/* Email */}
            <div className="space-y-1">
              <label className="text-[12px] font-medium text-[var(--c-sub)]">Email Address *</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[var(--c-dimmer)]" />
                <input
                  type="email"
                  placeholder="rahul@example.com"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  required
                  className="w-full h-9 pl-8 pr-3 rounded-lg border border-[var(--c-border)] bg-[var(--c-surface)] text-[var(--c-text)] text-sm placeholder:text-[var(--c-placeholder)] focus:outline-none focus:border-indigo-500 transition-colors"
                />
              </div>
              <p className="text-[11px] text-[var(--c-dimmer)] pt-0.5">
                Meeting link &amp; confirmation will be sent to this address by your SEBI advisor.
              </p>
            </div>

            {/* Experience level */}
            <div className="space-y-2">
              <label className="text-[12px] font-medium text-[var(--c-sub)]">Your Experience Level *</label>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { value: 'beginner',     label: 'Beginner',     icon: BookOpen,  desc: '< 1 year investing' },
                  { value: 'intermediate', label: 'Intermediate', icon: BarChart2, desc: '1–5 years' },
                  { value: 'expert',       label: 'Expert',       icon: Zap,       desc: '5+ years' },
                ].map(({ value, label, icon: Icon, desc }) => (
                  <button
                    key={value}
                    type="button"
                    onClick={() => setForm({ ...form, experience: value })}
                    className={`flex flex-col items-center gap-1.5 p-3 rounded-xl border text-center transition-all ${
                      form.experience === value
                        ? 'border-indigo-500 bg-indigo-600/10 text-indigo-400 ring-1 ring-indigo-500/30'
                        : 'border-[var(--c-border)] bg-[var(--c-surface)] text-[var(--c-muted)] hover:border-[var(--c-border2)]'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    <span className="text-[12px] font-semibold">{label}</span>
                    <span className="text-[10px] opacity-70">{desc}</span>
                    {form.experience === value && (
                      <span className="w-4 h-4 rounded-full bg-indigo-600 flex items-center justify-center mt-0.5">
                        <Check className="w-2.5 h-2.5 text-white" />
                      </span>
                    )}
                  </button>
                ))}
              </div>
            </div>

            {/* Notes */}
            <div className="space-y-1">
              <label className="text-[12px] font-medium text-[var(--c-sub)]">
                Notes for Advisor <span className="text-[var(--c-dimmer)]">(optional)</span>
              </label>
              <div className="relative">
                <MessageSquare className="absolute left-3 top-2.5 w-3.5 h-3.5 text-[var(--c-dimmer)]" />
                <textarea
                  rows={3}
                  placeholder="Describe your portfolio, goals, or specific questions..."
                  value={form.notes}
                  onChange={(e) => setForm({ ...form, notes: e.target.value })}
                  className="w-full pl-8 pr-3 pt-2 rounded-lg border border-[var(--c-border)] bg-[var(--c-surface)] text-[var(--c-text)] text-sm placeholder:text-[var(--c-placeholder)] focus:outline-none focus:border-indigo-500 transition-colors resize-none"
                />
              </div>
            </div>
          </div>

          {/* Disclaimer */}
          <div className="flex items-start gap-2.5 rounded-lg border border-amber-500/20 bg-amber-500/5 p-3.5">
            <AlertCircle className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" />
            <p className="text-[11px] text-amber-300/80 leading-relaxed">
              By proceeding to payment you confirm that all details above are accurate. Your SEBI-registered
              advisor will send a meeting invite to your email before the session. This platform does not act
              as an intermediary or investment manager.
            </p>
          </div>

          <div className="flex justify-between pt-1">
            <button
              type="button"
              onClick={() => setStep(2)}
              className="px-4 py-2 rounded-lg border border-[var(--c-border)] text-sm text-[var(--c-muted)] hover:text-[var(--c-sub)] transition-colors"
            >
              Back
            </button>
            <button
              type="submit"
              disabled={!canSubmit}
              className="inline-flex items-center gap-2 px-6 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <CreditCard className="w-4 h-4" />
              Proceed to Payment
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </form>
      )}

      {/* ── What to expect section ── */}
      {step < 4 && (
        <div className="border-t border-[var(--c-border)] pt-10">
          <SectionLabel>Process</SectionLabel>
          <h2 className="text-[18px] font-bold text-[var(--c-text)] mb-5">What Happens After You Book</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { n: '01', icon: Check,       label: 'Request Received',  desc: 'You receive an immediate confirmation email with your booking reference.' },
              { n: '02', icon: Phone,       label: 'Advisor Confirms',  desc: 'The advisor confirms or proposes an alternative slot within 2 business hours.' },
              { n: '03', icon: Award,       label: 'Pre-Session Prep',  desc: 'Optional: share your portfolio statement or questions beforehand for a productive session.' },
              { n: '04', icon: Calendar,    label: 'Session Conducted', desc: 'Video call or phone. Session is private, confidential, and not recorded.' },
            ].map((item) => {
              const Icon = item.icon;
              return (
                <div key={item.n} className="rounded-xl border border-[var(--c-border)] bg-[var(--c-surface)] p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-[11px] font-bold mono text-indigo-400">{item.n}</span>
                    <Icon className="w-4 h-4 text-[var(--c-muted)]" />
                  </div>
                  <p className="text-[13px] font-semibold text-[var(--c-text)]">{item.label}</p>
                  <p className="mt-1 text-[12px] text-[var(--c-muted)] leading-relaxed">{item.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      )}

    </div>
  );
}
