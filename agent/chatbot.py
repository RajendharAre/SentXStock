"""
AI Chatbot — Interactive trading advisor powered by sentiment data.
Users can ask questions like "Should I buy Tesla?" and get
data-backed answers using real-time sentiment + FinBERT + Gemini.
"""

import json
import re
import yfinance as yf
from datetime import datetime
from google import genai
from config.config import GEMINI_API_KEYS, GEMINI_MODEL, LLM_TEMPERATURE


# ─── Chatbot Prompt ──────────────────────────────────────────

CHATBOT_SYSTEM_PROMPT = """You are SentX, an AI trading advisor inside a Sentiment Trading Platform for Indian & US markets.
You help users make investment decisions based on REAL sentiment data from news and social media.

CURRENT MARKET DATA (auto-updated):
{market_context}

DASHBOARD ANALYSIS CACHE (stocks the user has recently analysed):
{ticker_context}

RULES:
1. Always use the provided sentiment data — prefer cached Dashboard data over general knowledge
2. Be specific — mention sentiment scores, confidence levels, news counts, and signals
3. Give clear BUY / SELL / HOLD recommendations with concise reasoning
4. Mention risk level where relevant
5. Keep responses to 3-6 sentences — informative but not overwhelming
6. For stocks NOT in the cache, use general market knowledge but clearly state it's not based on live data
7. AI can make mistakes — always recommend going through real data

Respond naturally and conversationally. Use **bold** for key values."""

CHATBOT_USER_PROMPT = """User Question: {question}

Provide a helpful, data-driven answer using the market sentiment data and stock cache above."""


class TradingChatbot:
    """
    Interactive AI chatbot that answers user questions using live sentiment data.
    Uses Gemini for conversational responses, with full context injected.
    Falls back to rich template responses when Gemini quota is exhausted.
    """

    def __init__(self):
        self.clients = []
        self.client_index = 0
        self.exhausted = set()
        self.model_name = GEMINI_MODEL
        self.conversation_history = []
        self._init_clients()

    def _init_clients(self):
        for key in GEMINI_API_KEYS:
            try:
                client = genai.Client(api_key=key, http_options={"api_version": "v1beta"})
                self.clients.append(client)
            except Exception:
                self.clients.append(None)
        active = sum(1 for c in self.clients if c is not None)
        if active:
            print(f"[INFO] Chatbot: {active} Gemini key(s) ready")
        else:
            print("[WARNING] Chatbot: No Gemini keys. Using template responses.")

    @property
    def client(self):
        return self.clients[self.client_index] if self.clients else None

    def _rotate_key(self) -> bool:
        self.exhausted.add(self.client_index)
        for _ in range(len(self.clients)):
            self.client_index = (self.client_index + 1) % len(self.clients)
            if self.client_index not in self.exhausted and self.clients[self.client_index] is not None:
                return True
        return False

    def ask(self, question: str, market_data: dict = None,
            ticker_cache: dict = None, recently_viewed: list = None) -> dict:
        """Answer a trading question using all available context."""
        ticker_cache    = ticker_cache or {}
        recently_viewed = recently_viewed or []

        market_context = self._build_market_context(market_data)
        ticker_context = self._build_ticker_context(ticker_cache, recently_viewed)

        # Try Gemini with key rotation
        if self.clients:
            for _ in range(len(self.clients)):
                current = self.client
                if current is None or self.client_index in self.exhausted:
                    if not self._rotate_key():
                        break
                    continue
                try:
                    answer = self._gemini_response(question, market_context, ticker_context, current)
                    self.conversation_history.append({
                        "question": question, "answer": answer,
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                    })
                    return {
                        "answer": answer,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "method": "gemini",
                        "data_used": bool(market_data or ticker_cache),
                    }
                except Exception as e:
                    if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
                        print(f"[Chatbot] Key {self.client_index} quota exhausted — rotating...")
                        if not self._rotate_key():
                            break
                    else:
                        print(f"[Chatbot] Gemini error: {str(e)[:80]}")
                        break

        # Rich template fallback
        answer = self._template_response(question, market_data, ticker_cache, recently_viewed)
        self.conversation_history.append({
            "question": question, "answer": answer,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        })
        return {
            "answer": answer,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "method": "template",
            "data_used": bool(market_data or ticker_cache),
        }

    def _gemini_response(self, question: str, market_context: str, ticker_context: str, client) -> str:
        system_prompt = CHATBOT_SYSTEM_PROMPT.format(
            market_context=market_context,
            ticker_context=ticker_context,
        )
        full_prompt = f"{system_prompt}\n\n{CHATBOT_USER_PROMPT.format(question=question)}"
        response = client.models.generate_content(
            model=self.model_name,
            contents=full_prompt,
            config={"temperature": 0.3, "max_output_tokens": 512},
        )
        text = response.text
        if text is None and response.candidates:
            for part in response.candidates[0].content.parts:
                if part.text:
                    text = part.text
                    break
        if not text:
            raise ValueError("Empty Gemini response")
        return text

    # ─── Context Builders ────────────────────────────────────

    def _build_market_context(self, market_data: dict) -> str:
        if not market_data:
            return "No global market scan run yet."
        details   = market_data.get("analysis_details", {})
        portfolio = market_data.get("portfolio_snapshot", {})
        orders    = market_data.get("orders", [])
        return (
            f"Timestamp: {market_data.get('timestamp', 'N/A')}\n"
            f"Overall Sentiment: {market_data.get('overall_sentiment', 'N/A')} "
            f"(score: {market_data.get('sentiment_score', 0):.4f})\n"
            f"Risk Level: {market_data.get('new_risk_level', 'N/A')}\n"
            f"Sources analysed: {details.get('total_items_analyzed', 0)} "
            f"({details.get('bullish_count', 0)} bullish, "
            f"{details.get('bearish_count', 0)} bearish, "
            f"{details.get('neutral_count', 0)} neutral)\n"
            f"Portfolio: {portfolio.get('equity_pct', 0):.1f}% equity, "
            f"{portfolio.get('bonds_pct', 0):.1f}% bonds, "
            f"{portfolio.get('cash_pct', 0):.1f}% cash\n"
            f"Active signals: {json.dumps(orders)}"
        )

    def _build_ticker_context(self, ticker_cache: dict, recently_viewed: list) -> str:
        if not ticker_cache:
            return "No stocks analysed yet. User hasn't clicked any stock on Dashboard."
        lines = [f"Recently viewed order: {recently_viewed}"]
        for ticker, d in ticker_cache.items():
            lines.append(
                f"{ticker} ({d.get('name','')}) | Sentiment: {d.get('sentiment','?')} "
                f"| Score: {d.get('score', 0):+.3f} | Confidence: {d.get('confidence', 0):.1f}% "
                f"| Rec: {d.get('recommendation','?')} "
                f"| {d.get('bull',0)}↑ {d.get('bear',0)}↓ {d.get('neutral',0)}→ "
                f"out of {d.get('total',0)} headlines | Sector: {d.get('sector','?')} "
                f"| Analysed: {d.get('timestamp','?')}"
            )
        return "\n".join(lines)

    # ─── Ticker Detection ────────────────────────────────────

    def _detect_ticker(self, question: str, ticker_cache: dict) -> tuple[str | None, dict | None]:
        """
        Detect a stock ticker mentioned in the question.
        Priority:
          1. Cache full-name match (case-insensitive)
          2. Cache first-word-of-name match (e.g. 'Reliance' for 'Reliance Industries Ltd')
          3. Cache ticker-base whole-word match (e.g. 'TCS' in 'Tell me about TCS')
          4. Regex on ORIGINAL question for already-all-caps tokens (avoids false
             positives from normal English words like 'Should', 'Is', 'Me', 'Today')
        Returns (ticker_base, cache_entry_or_None)
        """
        q_lower = question.lower()

        # Step 1 & 2: Company name / first-word-of-name match from cache
        for ticker, data in ticker_cache.items():
            name = data.get("name", "")
            if len(name) > 3 and name.lower() in q_lower:
                return ticker, data
            # Match first meaningful word of company name (len > 3 to avoid 'The', 'Ltd')
            words = [w for w in name.split() if len(w) > 3]
            if words and words[0].lower() in q_lower:
                return ticker, data

        # Step 3: Ticker-base whole-word match in original question (case-insensitive)
        for ticker, data in ticker_cache.items():
            base = ticker.split(".")[0]
            if re.search(r'\b' + re.escape(base) + r'\b', question, re.IGNORECASE):
                return ticker, data

        # Step 4: Regex on ORIGINAL question (not uppercased!) for already-all-caps tokens.
        # This ONLY fires when the user actually typed the symbol in caps (e.g. "AAPL", "RELIANCE").
        # Normal words like "Should", "Is", "Me", "Today" stay title/lower-case and won't match.
        _SKIP = {
            # Articles / prepositions / conjunctions
            "THE", "AND", "FOR", "BUT", "NOT", "YET", "NOR", "SO", "OR",
            # Pronouns / short words
            "IS", "IT", "IN", "AT", "BE", "BY", "DO", "AN", "IF", "OF",
            "ON", "TO", "UP", "AS", "AM", "WE", "US", "MY", "HE", "HI",
            "ME", "GO", "NO",
            # Common question / action words
            "CAN", "DID", "GET", "GOT", "HAS", "HAD", "LET", "MAY", "PUT",
            "SET", "RUN", "SAY", "SEE", "USE", "WIN", "ADD", "ASK", "TRY",
            "END", "NEW", "OLD", "OWN", "TOO", "TWO", "WAY", "DAY", "TOP",
            "BIG", "LOT", "OFF", "OUT", "OUR", "WHO", "ALL", "ANY",
            "NOW", "NOT", "ITS",
            # Finance / market jargon (not tickers)
            "BUY", "SELL", "HIGH", "HOLD", "RISK", "STOP", "LOSS",
            "NSE", "BSE", "IPO", "ETF", "NAV", "SIP", "EMI",
            "USD", "INR", "GDP", "RBI", "SEBI", "CEO", "CFO", "CTO",
            "USA", "NSE",
            # Common English filler words (uppercased by users rarely, but just in case)
            "TELL", "SHOW", "GIVE", "WHAT", "WHEN", "WHERE", "WHY", "HOW",
            "GOOD", "BEST", "LAST", "NEXT", "HELP", "WILL", "DOES", "HAVE",
            "FROM", "WITH", "THAT", "THIS", "NEWS", "MARKET", "ABOUT",
            "STOCK", "STOCKS", "TODAY", "LIKE", "SOME", "MANY", "MUCH",
            "MORE", "LESS", "OVER", "INTO", "ALSO", "JUST", "EVEN",
            "STILL", "WELL", "MAKE", "TAKE", "COME", "KNOW", "WANT",
            "NEED", "SEEM", "LOOK", "THINK", "MEAN", "SHOULD", "WOULD",
            "COULD", "MIGHT", "MUST", "SHALL",
        }
        # NOTE: using `question` (original case), NOT q_upper
        matches = re.findall(r'\b([A-Z]{2,6}(?:\.NS|\.BO)?)\b', question)
        candidates = [m for m in matches if m.split(".")[0] not in _SKIP]
        if candidates:
            best = max(candidates, key=lambda m: len(m.split(".")[0]))
            return best.split(".")[0], None

        return None, None

    def _fetch_live_stock_info(self, ticker: str) -> dict:
        """Fetch basic live info from yfinance for any ticker."""
        try:
            # Append .NS for Indian tickers without exchange suffix
            yf_ticker = ticker
            if not ("." in ticker):
                # Try NSE first, then raw
                info_ns = yf.Ticker(ticker + ".NS").info
                if info_ns.get("regularMarketPrice") or info_ns.get("currentPrice"):
                    yf_ticker = ticker + ".NS"

            stock = yf.Ticker(yf_ticker)
            info  = stock.info
            hist  = stock.history(period="5d")

            price     = info.get("currentPrice") or info.get("regularMarketPrice") or (
                round(float(hist["Close"].iloc[-1]), 2) if not hist.empty else None
            )
            prev      = info.get("previousClose")
            change_pct = round(((price - prev) / prev) * 100, 2) if price and prev else None
            return {
                "name":        info.get("longName") or info.get("shortName") or ticker,
                "price":       price,
                "change_pct":  change_pct,
                "sector":      info.get("sector", "Unknown"),
                "industry":    info.get("industry", "Unknown"),
                "market_cap":  info.get("marketCap"),
                "52w_high":    info.get("fiftyTwoWeekHigh"),
                "52w_low":     info.get("fiftyTwoWeekLow"),
                "pe_ratio":    info.get("trailingPE"),
                "description": (info.get("longBusinessSummary") or "")[:300],
            }
        except Exception as e:
            return {}

    # ─── Rich Template Response ──────────────────────────────

    def _template_response(self, question: str, market_data: dict,
                           ticker_cache: dict, recently_viewed: list) -> str:

        q = question.lower()

        # Global values
        sentiment = (market_data or {}).get("overall_sentiment", "Unknown")
        score     = (market_data or {}).get("sentiment_score", 0)
        risk      = (market_data or {}).get("new_risk_level", "Medium")
        orders    = (market_data or {}).get("orders", [])
        details   = (market_data or {}).get("analysis_details", {})
        total     = details.get("total_items_analyzed", 0)
        bullish   = details.get("bullish_count", 0)
        bearish   = details.get("bearish_count", 0)
        neutral_c = details.get("neutral_count", 0)
        portfolio = (market_data or {}).get("portfolio_snapshot", {})
        has_market = bool(market_data)

        # ── Detect ticker mention FIRST (even with no market data) ─────────
        ticker, cached = self._detect_ticker(question, ticker_cache)

        if not has_market and not ticker_cache and not ticker:
            return (
                "I don't have any market data yet.\n\n"
                "👉 Go to the **Dashboard**, search for any stock, and click **Analyse** — I'll immediately be able to give you data-backed advice!\n\n"
                "You can also ask me things like: 'Should I buy TCS?' · 'How is the market?' · 'Show me recommendations'"
            )

        if ticker:
            if cached:
                # ── We have real Dashboard analysis data ────────────────
                rec   = cached.get("recommendation", "HOLD")
                cscore = cached.get("score", 0)
                conf  = cached.get("confidence", 50)
                sent  = cached.get("sentiment", "Neutral")
                name  = cached.get("name", ticker)
                bull  = cached.get("bull", 0)
                bear  = cached.get("bear", 0)
                tot   = cached.get("total", 0)
                sec   = cached.get("sector", "")
                ts    = cached.get("timestamp", "")
                emoji = "📈" if rec == "BUY" else "📉" if rec == "SELL" else "➡️"

                action_line = (
                    f"Based on **{tot}** live headlines, **{bull}** bullish and **{bear}** bearish signals — "
                    f"recommendation is **{rec}** with **{conf:.1f}%** confidence."
                )
                if any(w in q for w in ["buy", "should i", "invest", "worth", "good time"]):
                    return (
                        f"{emoji} **{name} ({ticker})** — Sentiment: **{sent}** (score: {cscore:+.3f})\n\n"
                        f"{action_line}\n"
                        f"Sector: {sec} · Analysed at: {ts}\n\n"
                        f"{'✅ Conditions support buying.' if rec == 'BUY' else '⚠️ Suggest holding off — bearish signals dominate.' if rec == 'SELL' else '↔️ Mixed signals — consider waiting for a clearer trend.'}"
                    )
                if any(w in q for w in ["sell", "exit", "get out"]):
                    return (
                        f"{emoji} **{name} ({ticker})** — Sentiment: **{sent}** (score: {cscore:+.3f})\n\n"
                        f"{action_line}\n\n"
                        f"{'⚠️ Bearish signals — exiting or reducing exposure is reasonable.' if rec == 'SELL' else '📈 Sentiment is positive — selling now may mean leaving gains on the table.' if rec == 'BUY' else '↔️ No strong sell signal yet. Monitor for further deterioration.'}"
                    )
                # Generic ticker question
                return (
                    f"{emoji} **{name} ({ticker})**\n\n"
                    f"Sentiment: **{sent}** · Score: **{cscore:+.3f}** · Confidence: **{conf:.1f}%**\n"
                    f"Headlines: {tot} analysed · {bull} bullish · {bear} bearish\n"
                    f"Recommendation: **{rec}** · Sector: {sec}\n"
                    f"Last analysed: {ts}\n\n"
                    f"{'Go to Dashboard and re-analyse for the latest data.' if tot == 0 else ''}"
                )
            else:
                # ── Ticker not in cache — fetch live from yfinance ───────
                live = self._fetch_live_stock_info(ticker)
                if live.get("price"):
                    direction = "▲" if (live.get("change_pct") or 0) >= 0 else "▼"
                    chg = live.get("change_pct")
                    chg_str = f"{direction} {abs(chg):.2f}%" if chg is not None else ""
                    pe = live.get("pe_ratio")
                    pe_str = f" · P/E: {pe:.1f}" if pe else ""
                    cap = live.get("market_cap")
                    cap_str = f" · MCap: ₹{cap/1e9:.1f}B" if cap else ""
                    return (
                        f"**{live['name']} ({ticker})** — ₹{live['price']:,.2f} {chg_str}\n"
                        f"Sector: {live['sector']} · {live['industry']}{pe_str}{cap_str}\n"
                        f"52W High: {live.get('52w_high','?')} · Low: {live.get('52w_low','?')}\n\n"
                        f"⚠️ I don't have **live sentiment data** for {ticker} yet — the price above is from market data.\n"
                        f"👉 Go to **Dashboard → search '{ticker}' → click Analyse** to get a full sentiment-based recommendation."
                    )
                else:
                    mkt_context = f"Overall market is **{sentiment}** (score: {score:+.2f}) with **{risk}** risk." if has_market else ""
                    return (
                        f"I don't have sentiment data for **{ticker}** yet. {mkt_context}\n\n"
                        f"👉 Go to **Dashboard → search '{ticker}' → click Analyse** to get a full BUY/SELL/HOLD signal with live news sentiment."
                    )

        # ── Recently viewed summary ──────────────────────────────────────
        if any(w in q for w in ["recently", "last analysed", "what did i", "what have i", "my stocks", "my analysis"]):
            if not recently_viewed:
                return "You haven't analysed any stocks yet. Head to the Dashboard and search for any stock to get started."
            lines = []
            for t in recently_viewed:
                d = ticker_cache.get(t, {})
                rec = d.get("recommendation", "?")
                sc  = d.get("score", 0)
                emoji = "📈" if rec == "BUY" else "📉" if rec == "SELL" else "➡️"
                lines.append(f"{emoji} **{t}** ({d.get('name','')}) — {rec} · score {sc:+.3f}")
            return "Your recently analysed stocks:\n\n" + "\n".join(lines)

        # ── Buy intent ──────────────────────────────────────────────────
        if any(w in q for w in ["buy", "invest", "purchase", "should i", "worth", "good time to"]) and "sell" not in q:
            if ticker_cache:
                buy_picks = [t for t, d in ticker_cache.items() if d.get("recommendation") == "BUY"]
                if buy_picks:
                    picks_str = ", ".join(f"**{t}**" for t in buy_picks[:4])
                    return (
                        f"Based on your Dashboard analyses, the stocks with a **BUY** signal right now are: {picks_str}\n\n"
                        f"Market sentiment: **{sentiment}** (score: {score:+.2f}) · Risk: **{risk}**\n"
                        f"Analyse more stocks on the Dashboard to expand your watchlist signals."
                    )
            if has_market:
                return (
                    f"Market is **{sentiment}** (score: {score:+.2f}) with **{risk}** risk.\n\n"
                    f"{'Conditions lean bullish — selective buying in quality names could work.' if score > 0.15 else 'Bearish signals present — exercise caution before entering new positions.' if score < -0.15 else 'Mixed signals — no strong directional bias. Consider waiting or DCA.'}\n\n"
                    f"💡 Analyse specific stocks on the Dashboard to get individual BUY/SELL/HOLD signals."
                )
            return "Analyse stocks on the Dashboard first — I'll give you specific BUY/SELL/HOLD recommendations based on live sentiment."

        # ── Sell intent ─────────────────────────────────────────────────
        if any(w in q for w in ["sell", "exit", "close position", "get out"]):
            if ticker_cache:
                sell_picks = [t for t, d in ticker_cache.items() if d.get("recommendation") == "SELL"]
                if sell_picks:
                    picks_str = ", ".join(f"**{t}**" for t in sell_picks[:4])
                    return (
                        f"Stocks with a **SELL** signal in your recent analyses: {picks_str}\n\n"
                        f"Market: **{sentiment}** (score: {score:+.2f}) · Risk: **{risk}**"
                    )
            return (
                f"Market is **{sentiment}** (score: {score:+.2f}).\n"
                f"{'Bearish signals present — trimming weak positions is prudent.' if score < -0.2 else 'No strong sell signal in current data. Check individual stocks on Dashboard.'}"
            )

        # ── Portfolio / allocation ───────────────────────────────────────
        if any(w in q for w in ["portfolio", "allocat", "diversif", "holdings", "my portfolio"]):
            eq  = portfolio.get("equity_pct", 0)
            bnd = portfolio.get("bonds_pct", 0)
            csh = portfolio.get("cash_pct", 0)
            cached_count = len(ticker_cache)
            cache_summary = ""
            if ticker_cache:
                all_recs = [d.get("recommendation","?") for d in ticker_cache.values()]
                buys  = all_recs.count("BUY")
                sells = all_recs.count("SELL")
                holds = all_recs.count("HOLD")
                cache_summary = f"\n\nYour {cached_count} analysed stocks: **{buys} BUY · {sells} SELL · {holds} HOLD**"
            return (
                f"Portfolio allocation: **{eq:.1f}% equity · {bnd:.1f}% bonds · {csh:.1f}% cash**\n"
                f"Market: **{sentiment}** (score: {score:+.2f}) · Risk: **{risk}**"
                + cache_summary +
                f"\n\n{'Shift more to bonds/cash given bearish signals.' if score < -0.2 else 'Allocation looks appropriate.' if abs(score) < 0.2 else 'Positive sentiment supports higher equity weight.'}"
            )

        # ── Risk ─────────────────────────────────────────────────────────
        if any(w in q for w in ["risk", "safe", "conservative", "aggressive", "volatile"]):
            return (
                f"Current risk level: **{risk}**\n\n"
                f"Market score: **{score:+.2f}** · {bullish} bullish · {bearish} bearish · {neutral_c} neutral out of {total} sources.\n"
                f"{'⚠️ High bearish pressure — reduce exposure, increase cash.' if score < -0.3 else '✅ Stable conditions — balanced approach.' if abs(score) < 0.3 else '📈 Positive momentum — can accept moderate equity risk.'}"
            )

        # ── Recommendations / orders ─────────────────────────────────────
        if any(w in q for w in ["recommend", "signal", "order", "suggestion", "advice", "tip", "pick"]):
            lines = []
            if ticker_cache:
                for t, d in list(ticker_cache.items())[:6]:
                    rec  = d.get("recommendation","?")
                    sc   = d.get("score", 0)
                    conf = d.get("confidence", 0)
                    emoji = "📈" if rec == "BUY" else "📉" if rec == "SELL" else "➡️"
                    lines.append(f"{emoji} **{t}** — {rec} · score {sc:+.3f} · conf {conf:.1f}%")
            if not lines:
                if orders:
                    lines = [f"• **{o['action']}** {o['asset']} — {o.get('reason','')}" for o in orders[:5]]
                else:
                    return (
                        "No signals yet. Analyse stocks on the Dashboard — each analysis generates a BUY/SELL/HOLD recommendation.\n\n"
                        "💡 Try searching for TCS, INFY, RELIANCE, WIPRO, or any US stock like AAPL, TSLA."
                    )
            return (
                f"Current signals from your Dashboard analyses:\n\n" + "\n".join(lines) +
                f"\n\nMarket: **{sentiment}** (score: {score:+.2f}) · Risk: **{risk}**"
            )

        # ── Market overview ──────────────────────────────────────────────
        if any(w in q for w in ["market", "sentiment", "overall", "today", "trend", "mood", "news", "outlook", "how is", "how are"]):
            direction = "upward" if score > 0.1 else "downward" if score < -0.1 else "sideways"
            cached_summary = ""
            if ticker_cache:
                buys  = sum(1 for d in ticker_cache.values() if d.get("recommendation") == "BUY")
                sells = sum(1 for d in ticker_cache.values() if d.get("recommendation") == "SELL")
                cached_summary = f"\n\nYour analysed stocks: **{buys} BUY · {sells} SELL** signals."
            return (
                f"**Market overview:**\n\n"
                f"Sentiment: **{sentiment}** · Score: **{score:+.2f}** · Risk: **{risk}**\n"
                f"{total} sources — {bullish} bullish · {bearish} bearish · {neutral_c} neutral\n"
                f"Trend: {direction}"
                + cached_summary +
                f"\n\n{'⚠️ Defensive positioning recommended.' if score < -0.2 else '✅ Stable — monitor for breakouts.' if abs(score) < 0.2 else '📈 Positive momentum — growth names may outperform.'}"
            )

        # ── Help ─────────────────────────────────────────────────────────
        if any(w in q for w in ["help", "what can", "capabilit", "feature", "do you", "how do"]):
            return (
                "I can help you with:\n\n"
                "• **Any stock** — e.g. 'Tell me about TCS' or 'Should I buy AAPL?'\n"
                "• **Market overview** — e.g. 'How is the market today?'\n"
                "• **Your signals** — e.g. 'Show me my recommendations'\n"
                "• **Buy/Sell advice** — e.g. 'Is it a good time to invest?'\n"
                "• **Portfolio** — e.g. 'How is my portfolio allocated?'\n"
                "• **Risk** — e.g. 'What is the current risk level?'\n\n"
                "For the best results, analyse stocks on the **Dashboard** first — I'll use that live sentiment data in my answers."
            )

        # ── Smart default ────────────────────────────────────────────────
        if not has_market and not ticker_cache:
            return (
                "I don't have any market data yet.\n\n"
                "👉 Go to the **Dashboard**, search for any stock, and click **Analyse** — I'll immediately be able to give you data-backed advice!\n\n"
                "You can also ask me things like: 'Should I buy TCS?' · 'How is the market?' · 'Show me recommendations'"
            )

        direction = "bullish" if score > 0.1 else "bearish" if score < -0.1 else "neutral"
        cached_count = len(ticker_cache)
        return (
            f"Market is **{sentiment}** (score: {score:+.2f}, {direction}) · Risk: **{risk}**\n"
            f"{total} sources analysed — {bullish} bullish · {bearish} bearish · {neutral_c} neutral\n"
            + (f"You have **{cached_count} stock(s)** analysed on the Dashboard.\n" if cached_count else "") +
            f"\nTry asking:\n"
            f"• 'Should I buy TCS?' · 'Tell me about INFY'\n"
            f"• 'Show me my recommendations' · 'How is the market?'\n"
            f"• Any stock name or ticker — even ones outside your watchlist!"
        )

    def _build_market_context(self, market_data: dict) -> str:
        if not market_data:
            return "No global market scan run yet."
        details   = market_data.get("analysis_details", {})
        portfolio = market_data.get("portfolio_snapshot", {})
        orders    = market_data.get("orders", [])
        return (
            f"Timestamp: {market_data.get('timestamp', 'N/A')}\n"
            f"Overall Sentiment: {market_data.get('overall_sentiment', 'N/A')} "
            f"(score: {market_data.get('sentiment_score', 0):.4f})\n"
            f"Risk Level: {market_data.get('new_risk_level', 'N/A')}\n"
            f"Sources analysed: {details.get('total_items_analyzed', 0)} "
            f"({details.get('bullish_count', 0)} bullish, "
            f"{details.get('bearish_count', 0)} bearish, "
            f"{details.get('neutral_count', 0)} neutral)\n"
            f"Portfolio: {portfolio.get('equity_pct', 0):.1f}% equity, "
            f"{portfolio.get('bonds_pct', 0):.1f}% bonds, "
            f"{portfolio.get('cash_pct', 0):.1f}% cash\n"
            f"Active signals: {json.dumps(orders)}"
        )

    def _build_ticker_context(self, ticker_cache: dict, recently_viewed: list) -> str:
        if not ticker_cache:
            return "No stocks analysed yet."
        lines = [f"Recently viewed: {recently_viewed}"]
        for ticker, d in ticker_cache.items():
            lines.append(
                f"{ticker} ({d.get('name','')}) | {d.get('sentiment','?')} "
                f"| score {d.get('score', 0):+.3f} | conf {d.get('confidence', 0):.1f}% "
                f"| {d.get('recommendation','?')} "
                f"| {d.get('bull',0)}↑ {d.get('bear',0)}↓ {d.get('neutral',0)}→ / {d.get('total',0)} "
                f"| sector: {d.get('sector','?')}"
            )
        return "\n".join(lines)

    # ─────────────────────────────────────────────────────────

    def clear_history(self):
        self.conversation_history = []
