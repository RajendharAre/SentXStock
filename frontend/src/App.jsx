import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Dashboard from './pages/Dashboard';
import Portfolio from './pages/Portfolio';
import Chat from './pages/Chat';
import Consult from './pages/Consult';
import Settings from './pages/Settings';
import Backtest from './pages/Backtest';
import AdminLogin from './pages/AdminLogin';
import AdminPanel from './pages/AdminPanel';

// ── Main app layout (with Navbar) ─────────────────────────────────────────
function MainLayout() {
  const [dashboardData, setDashboardData] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [settingsChangedAt, setSettingsChangedAt] = useState(null);

  // Called by Settings page after a successful save — clears stale dashboard data
  const handleSettingsSaved = () => {
    setDashboardData(null);
    setSettingsChangedAt(new Date());
  };

  return (
    <div className="min-h-screen bg-[var(--c-bg)] flex flex-col transition-colors">
      <Navbar />
      <main className="flex-1 w-full max-w-[1360px] mx-auto px-5 sm:px-8 py-5">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route
            path="/dashboard"
            element={
              <Dashboard
                dashboardData={dashboardData}
                setDashboardData={setDashboardData}
                isAnalyzing={isAnalyzing}
                setIsAnalyzing={setIsAnalyzing}
                settingsChangedAt={settingsChangedAt}
              />
            }
          />
          <Route path="/portfolio" element={<Portfolio />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/consult" element={<Consult />} />
          <Route path="/settings" element={<Settings onSaved={handleSettingsSaved} />} />
          <Route path="/backtest" element={<Backtest />} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <Router>
        <Routes>
          {/* ── Admin routes — standalone, no Navbar ── */}
          <Route path="/admin/login" element={<AdminLogin />} />
          <Route path="/admin" element={<AdminPanel />} />

          {/* ── Main app routes — with Navbar ── */}
          <Route path="/*" element={<MainLayout />} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}
