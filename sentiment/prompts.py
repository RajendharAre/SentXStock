"""
Prompt templates for LLM-based sentiment analysis.
"""

SENTIMENT_ANALYSIS_PROMPT = """You are a quantitative financial analyst specializing in market sentiment analysis.

Analyze the following text and determine its market sentiment.

Text: "{text}"

Respond with ONLY a JSON object (no markdown, no code blocks, no explanation):
{{"sentiment": "Bullish" or "Bearish" or "Neutral", "score": <float between -1.0 and 1.0>, "reasoning": "<one sentence explanation>"}}

Scoring guide:
- Strong Bullish: +0.7 to +1.0 (very positive outlook, strong buy signals)
- Bullish: +0.3 to +0.7 (positive outlook, growth expected)
- Neutral: -0.3 to +0.3 (no clear direction, mixed signals)
- Bearish: -0.7 to -0.3 (negative outlook, decline expected)
- Strong Bearish: -1.0 to -0.7 (very negative, crash/crisis signals)

Be precise and financially logical. Base your analysis only on the given text."""


BATCH_SENTIMENT_PROMPT = """You are a quantitative financial analyst specializing in market sentiment analysis.

Analyze the following list of market texts (news headlines and social media posts) and determine the sentiment of EACH one.

Texts:
{texts}

Respond with ONLY a JSON array (no markdown, no code blocks, no explanation). Each element should be:
{{"text": "<original text>", "sentiment": "Bullish" or "Bearish" or "Neutral", "score": <float between -1.0 and 1.0>}}

Scoring guide:
- Strong Bullish: +0.7 to +1.0
- Bullish: +0.3 to +0.7
- Neutral: -0.3 to +0.3
- Bearish: -0.7 to -0.3
- Strong Bearish: -1.0 to -0.7

Be precise, deterministic, and financially logical."""


OVERALL_MARKET_MOOD_PROMPT = """You are a quantitative financial analyst.

Given the following individual sentiment analyses, determine the OVERALL market mood.

Individual sentiments:
{sentiments}

Average sentiment score: {avg_score}

Respond with ONLY a JSON object (no markdown, no code blocks):
{{"overall_sentiment": "Bullish" or "Bearish" or "Neutral", "sentiment_score": <float -1.0 to 1.0>, "market_mood_summary": "<2-3 sentence summary of market mood>"}}"""
