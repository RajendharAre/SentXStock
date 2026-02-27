import axios from 'axios';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
  timeout: 120000, // 2 min timeout for analysis
});

// ─── Health ──────────────────────────────────────────────────
export const checkHealth = () => api.get('/health');

// ─── Settings ────────────────────────────────────────────────
export const getSettings = () => api.get('/settings');
export const setTickers = (tickers) => api.post('/settings/tickers', { tickers });
export const setPortfolio = (cash, risk) => api.post('/settings/portfolio', { cash, risk });

// ─── Analysis ────────────────────────────────────────────────
export const runAnalysis = (mock = false) => api.post('/analyze', { mock });
export const analyzeStatus = () => api.get('/analyze/status');
export const analyzeTicker = (ticker) => api.post('/analyze/ticker', { ticker });
export const getLatestResult = () => api.get('/result');

// ─── Dashboard ───────────────────────────────────────────────
export const getDashboard = () => api.get('/dashboard');

// ─── Chatbot ─────────────────────────────────────────────────
export const sendChat = (question) => api.post('/chat', { question });
export const getChatHistory = () => api.get('/chat/history');
export const clearChat = () => api.post('/chat/clear');
// ─── Backtesting ──────────────────────────────────────────────────────────────
export const startBacktest          = (params) => api.post('/backtest/run', params);
export const backtestStatus         = ()        => api.get('/backtest/status');
export const backtestLatestResult   = ()        => api.get('/backtest/latest');
export const listBacktestResults    = ()        => api.get('/backtest/results');
export const loadBacktestResult     = (runId)   => api.get(`/backtest/result/${runId}`);
export const compareBacktestResults = (runIds)  => api.post('/backtest/compare', { run_ids: runIds });
export const deleteBacktestResult   = (runId)   => api.delete(`/backtest/result/${runId}`);
export default api;
