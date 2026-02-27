import { Link, useLocation } from 'react-router-dom';
import { Home, LayoutDashboard, Bot, Users, Settings, Sun, Moon, PieChart } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

export default function Navbar() {
  const { pathname } = useLocation();
  const { theme, toggle } = useTheme();

  const links = [
    { to: '/',           label: 'Home',           icon: Home },
    { to: '/dashboard',  label: 'Dashboard',      icon: LayoutDashboard },
    { to: '/portfolio',  label: 'Portfolio',      icon: PieChart },
    { to: '/chat',       label: 'AI Advisor',     icon: Bot },
    { to: '/consult',    label: 'Consult Expert', icon: Users },
    { to: '/settings',   label: 'Settings',       icon: Settings },
  ];

  return (
    <header className="sticky top-0 z-50 border-b border-[var(--c-border)] bg-[var(--c-bg)] backdrop-blur-sm transition-colors">
      <div className="max-w-[1360px] mx-auto px-5 sm:px-8 h-14 flex items-center justify-between">
        {/* Brand */}
        <Link to="/" className="flex items-center gap-2" aria-label="Home">
          <img src="/logo.png" alt="SentXStock" className="w-8 h-8 object-contain" />
          <span className="text-[15px] font-semibold text-[var(--c-text)] tracking-tight hidden sm:block">
            SentXStock
          </span>
        </Link>

        {/* Nav */}
        <nav className="flex items-center gap-0.5">
          {links.map(({ to, label, icon: Icon }) => {
            const active = pathname === to;
            return (
              <Link
                key={to}
                to={to}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[13px] font-medium transition-colors ${
                  active
                    ? 'text-[var(--c-text)] bg-[var(--c-border)]'
                    : 'text-[var(--c-muted)] hover:text-[var(--c-sub)]'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">{label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Right side */}
        <div className="flex items-center gap-3">
          {/* Theme toggle */}
          <button
            onClick={toggle}
            title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            className="w-8 h-8 flex items-center justify-center rounded-md border border-[var(--c-border)]
              text-[var(--c-muted)] hover:text-[var(--c-text)] hover:border-[var(--c-border2)]
              transition-colors"
          >
            {theme === 'dark'
              ? <Sun className="w-3.5 h-3.5" />
              : <Moon className="w-3.5 h-3.5" />}
          </button>

          {/* Live dot */}
          <div className="flex items-center gap-2">
            <div className="live-dot" />
            <span className="text-[11px] text-[var(--c-dim)] font-medium">LIVE</span>
          </div>
        </div>
      </div>
    </header>
  );
}
