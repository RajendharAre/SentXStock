import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import Chat from './pages/Chat';
import Settings from './pages/Settings';

export default function App() {
  const [dashboardData, setDashboardData] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [settingsChangedAt, setSettingsChangedAt] = useState(null);

  // Called by Settings page after a successful save — clears stale dashboard data
  const handleSettingsSaved = () => {
    setDashboardData(null);
    setSettingsChangedAt(new Date());
  };

  return (
    <ThemeProvider>
      <Router>
        <div className="min-h-screen bg-[var(--c-bg)] flex flex-col transition-colors">
          <Navbar />
          <main className="flex-1 w-full max-w-[1360px] mx-auto px-5 sm:px-8 py-5">
            <Routes>
              <Route
                path="/"
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
              <Route path="/chat" element={<Chat />} />
              <Route path="/settings" element={<Settings onSaved={handleSettingsSaved} />} />
            </Routes>
          </main>
        </div>
      </Router>
    </ThemeProvider>
  );
}
