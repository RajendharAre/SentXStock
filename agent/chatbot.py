"""
AI Chatbot — Interactive trading advisor powered by sentiment data.
Users can ask questions like "Should I buy Tesla?" and get
data-backed answers using real-time sentiment + FinBERT + Gemini.
"""

import json
from datetime import datetime
from google import genai
from config.config import GEMINI_API_KEYS, GEMINI_MODEL, LLM_TEMPERATURE


# ─── Chatbot Prompt ──────────────────────────────────────────

CHATBOT_SYSTEM_PROMPT = """You are an AI Trading Advisor inside a Sentiment Trading Platform.
You help users make investment decisions based on REAL sentiment data from news and social media.

CURRENT MARKET DATA (auto-updated):
{market_context}

RULES:
1. Always base answers on the provided sentiment data — don't make up numbers
2. Be specific — mention sentiment scores, sources, and data points
3. Give clear BUY / SELL / HOLD recommendations with reasoning
4. Mention the risk level and how it affects your advice
5. Keep responses concise (3-5 sentences) but informative
6. If asked about a ticker not in the data, say you don't have recent sentiment data for it
7. Always remind users this is a mock portfolio / educational tool — not real financial advice

Respond naturally and conversationally."""

CHATBOT_USER_PROMPT = """User Question: {question}

Provide a helpful, data-driven answer based on the current market sentiment data above."""


class TradingChatbot:
    """
    Interactive AI chatbot that answers user questions using live sentiment data.
    Uses Gemini for conversational responses, with sentiment context injected.
    """

    def __init__(self):
        self.client = None
        self.model_name = GEMINI_MODEL
        self.conversation_history = []
        self._init_client()

    def _init_client(self):
        """Initialize Gemini client with first available key."""
        for key in GEMINI_API_KEYS:
            try:
                self.client = genai.Client(
                    api_key=key,
                    http_options={"api_version": "v1beta"},
                )
                return
            except Exception:
                continue
        print("[WARNING] Chatbot: No Gemini keys available. Chat will use templated responses.")

    def ask(self, question: str, market_data: dict = None) -> dict:
        """
        Answer a user's trading question using current market data.

        Args:
            question: User's question (e.g., "Should I buy TSLA?")
            market_data: Latest agent output dict (from TradingAgent.run())

        Returns:
            dict with 'answer', 'timestamp', 'data_used'
        """
        context = self._build_context(market_data)

        # Try Gemini-powered response
        if self.client:
            try:
                answer = self._gemini_response(question, context)
                return {
                    "answer": answer,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "method": "gemini",
                    "data_used": bool(market_data),
                }
            except Exception as e:
                print(f"[Chatbot] Gemini failed: {e}. Using template response.")

        # Fallback: template-based response
        answer = self._template_response(question, market_data)
        return {
            "answer": answer,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "method": "template",
            "data_used": bool(market_data),
        }

    def _gemini_response(self, question: str, context: str) -> str:
        """Get a response from Gemini with market context."""
        system_prompt = CHATBOT_SYSTEM_PROMPT.format(market_context=context)
        user_prompt = CHATBOT_USER_PROMPT.format(question=question)

        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=full_prompt,
            config={
                "temperature": 0.3,  # Slightly creative but still factual
                "max_output_tokens": 512,
            },
        )

        text = response.text
        if text is None and response.candidates:
            for part in response.candidates[0].content.parts:
                if part.text:
                    text = part.text
                    break

        if not text:
            raise ValueError("Empty response from Gemini")

        # Track conversation
        self.conversation_history.append({
            "question": question,
            "answer": text,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        })

        return text

    def _template_response(self, question: str, market_data: dict) -> str:
        """Generate a template-based response when Gemini is unavailable."""
        if not market_data:
            return "I don't have current market data yet. Please run the sentiment analysis first, then ask me again."

        sentiment = market_data.get("overall_sentiment", "Unknown")
        score = market_data.get("sentiment_score", 0)
        risk = market_data.get("new_risk_level", "Medium")
        orders = market_data.get("orders", [])

        q_lower = question.lower()

        # Check if asking about a specific ticker
        from config.config import EQUITY_ASSETS, BOND_ASSETS
        all_tickers = EQUITY_ASSETS + BOND_ASSETS
        mentioned_ticker = None
        for ticker in all_tickers:
            if ticker.lower() in q_lower:
                mentioned_ticker = ticker
                break

        # Ticker-specific question
        if mentioned_ticker:
            # Check if we have an order for this ticker
            for order in orders:
                if order.get("asset", "").upper() == mentioned_ticker:
                    return (
                        f"Based on current sentiment analysis, our system recommends to "
                        f"**{order['action']}** {mentioned_ticker}. "
                        f"Reason: {order.get('reason', 'Sentiment-driven decision')}. "
                        f"Current market mood is {sentiment} (score: {score:.2f}), "
                        f"risk level: {risk}."
                    )
            return (
                f"Currently, {mentioned_ticker} doesn't have a specific buy/sell signal. "
                f"The overall market sentiment is {sentiment} (score: {score:.2f}) with {risk} risk level. "
                f"I'd suggest a HOLD position until clearer signals emerge."
            )

        # General market question
        if any(word in q_lower for word in ["market", "overall", "sentiment", "mood", "how"]):
            total = market_data.get("analysis_details", {}).get("total_items_analyzed", 0)
            bullish = market_data.get("analysis_details", {}).get("bullish_count", 0)
            bearish = market_data.get("analysis_details", {}).get("bearish_count", 0)
            return (
                f"The current market sentiment is **{sentiment}** with a score of {score:.2f}. "
                f"Based on {total} analyzed sources: {bullish} bullish, {bearish} bearish. "
                f"Risk level is set to {risk}. "
                f"{'Consider protective positions.' if score < -0.2 else 'Market looks stable for balanced investing.' if abs(score) < 0.3 else 'Positive signals — growth-oriented positions may work well.'}"
            )

        # Risk question
        if any(word in q_lower for word in ["risk", "safe", "conservative", "aggressive"]):
            portfolio = market_data.get("portfolio_snapshot", {})
            return (
                f"Current risk level: **{risk}**. "
                f"Portfolio allocation: {portfolio.get('equity_pct', 0):.1f}% equity, "
                f"{portfolio.get('bonds_pct', 0):.1f}% bonds, {portfolio.get('cash_pct', 0):.1f}% cash. "
                f"Market sentiment score: {score:.2f}. "
                f"{'Consider reducing equity and increasing bonds/cash.' if score < -0.3 else 'Current allocation aligns with market conditions.'}"
            )

        # Default
        return (
            f"Market is currently {sentiment} (score: {score:.2f}) with {risk} risk. "
            f"We have {len(orders)} active order recommendation(s). "
            f"Ask me about specific stocks (e.g., 'Should I buy AAPL?') or about market conditions."
        )

    def _build_context(self, market_data: dict) -> str:
        """Build market context string for the LLM prompt."""
        if not market_data:
            return "No market data available yet. Analysis has not been run."

        details = market_data.get("analysis_details", {})
        portfolio = market_data.get("portfolio_snapshot", {})
        orders = market_data.get("orders", [])

        context = f"""
Timestamp: {market_data.get('timestamp', 'N/A')}
Overall Sentiment: {market_data.get('overall_sentiment', 'N/A')}
Sentiment Score: {market_data.get('sentiment_score', 0):.4f} (range: -1.0 bearish to +1.0 bullish)
Risk Level: {market_data.get('new_risk_level', 'N/A')}
Risk Adjustment: {market_data.get('risk_adjustment', 'N/A')}

Analysis: {details.get('total_items_analyzed', 0)} items analyzed
- Bullish signals: {details.get('bullish_count', 0)}
- Bearish signals: {details.get('bearish_count', 0)}
- Neutral signals: {details.get('neutral_count', 0)}

Portfolio: ${portfolio.get('total_value', 0):,.2f}
- Equity: {portfolio.get('equity_pct', 0):.1f}%
- Bonds: {portfolio.get('bonds_pct', 0):.1f}%
- Cash: {portfolio.get('cash_pct', 0):.1f}%

Recommended Orders: {json.dumps(orders, indent=2)}
Rebalance Actions: {json.dumps(details.get('rebalance_actions', []))}
"""
        return context.strip()

    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
