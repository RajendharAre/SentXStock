/**
 * Admin Login Page — /admin/login
 * Validates credentials via POST /api/admin/login
 * Saves token to localStorage and redirects to /admin
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldCheck, Eye, EyeOff, LogIn, AlertCircle, Lock, User } from 'lucide-react';
import { adminLogin } from '../services/adminApi';

export default function AdminLogin() {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPw,   setShowPw]   = useState(false);
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await adminLogin(username.trim(), password);
      navigate('/admin');
    } catch (err) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--c-bg)] flex items-center justify-center px-4">
      <div className="w-full max-w-sm space-y-6">

        {/* Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex w-14 h-14 rounded-2xl bg-indigo-600/10 border border-indigo-500/30 items-center justify-center mx-auto">
            <ShieldCheck className="w-7 h-7 text-indigo-400" />
          </div>
          <h1 className="text-2xl font-extrabold text-[var(--c-text)]">Admin Portal</h1>
          <p className="text-sm text-[var(--c-muted)]">SentXStock · Dataset Management</p>
        </div>

        {/* Card */}
        <div className="rounded-2xl border border-[var(--c-border)] bg-[var(--c-surface)] p-7 shadow-lg space-y-5">
          {error && (
            <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/5 px-3 py-2.5">
              <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
              <p className="text-[12px] text-red-400">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Username */}
            <div className="space-y-1.5">
              <label className="text-[12px] font-medium text-[var(--c-sub)]">Username</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--c-dimmer)]" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="admin"
                  autoComplete="username"
                  required
                  className="w-full h-10 pl-9 pr-3 rounded-lg border border-[var(--c-border)] bg-[var(--c-bg)] text-[var(--c-text)] text-sm placeholder:text-[var(--c-placeholder)] focus:outline-none focus:border-indigo-500 transition-colors"
                />
              </div>
            </div>

            {/* Password */}
            <div className="space-y-1.5">
              <label className="text-[12px] font-medium text-[var(--c-sub)]">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--c-dimmer)]" />
                <input
                  type={showPw ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  autoComplete="current-password"
                  required
                  className="w-full h-10 pl-9 pr-10 rounded-lg border border-[var(--c-border)] bg-[var(--c-bg)] text-[var(--c-text)] text-sm placeholder:text-[var(--c-placeholder)] focus:outline-none focus:border-indigo-500 transition-colors"
                />
                <button
                  type="button"
                  onClick={() => setShowPw(!showPw)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--c-dimmer)] hover:text-[var(--c-sub)] transition-colors"
                >
                  {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || !username || !password}
              className="w-full h-10 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm flex items-center justify-center gap-2 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {loading ? (
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <LogIn className="w-4 h-4" />
              )}
              {loading ? 'Signing in…' : 'Sign In'}
            </button>
          </form>
        </div>

        <p className="text-center text-[11px] text-[var(--c-dimmer)]">
          Credentials are set via <code className="bg-[var(--c-border)] px-1 rounded">.env</code> →{' '}
          <code className="bg-[var(--c-border)] px-1 rounded">ADMIN_USERNAME</code> /{' '}
          <code className="bg-[var(--c-border)] px-1 rounded">ADMIN_PASSWORD</code>
        </p>

        <p className="text-center">
          <a href="/" className="text-[12px] text-indigo-400 hover:text-indigo-300 transition-colors">
            ← Back to SentXStock
          </a>
        </p>
      </div>
    </div>
  );
}
