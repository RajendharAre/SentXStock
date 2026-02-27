"""
Sentiment Scorer — aggregates individual sentiment scores into an overall market score.
Also provides a VADER-based fallback for offline / no-API scenarios.
"""

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


class SentimentScorer:
    """Handles scoring and aggregation of sentiment results."""

    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()

    def vader_score(self, text: str) -> dict:
        """
        Fallback sentiment analysis using VADER (no API needed).
        
        Args:
            text: Text to analyze
        
        Returns:
            Dict with sentiment label and score
        """
        scores = self.vader.polarity_scores(text)
        compound = scores["compound"]  # Range: -1 to +1

        if compound >= 0.3:
            sentiment = "Bullish"
        elif compound <= -0.3:
            sentiment = "Bearish"
        else:
            sentiment = "Neutral"

        return {
            "text": text,
            "sentiment": sentiment,
            "score": round(compound, 4),
            "method": "VADER",
        }

    def aggregate_scores(self, results: list[dict]) -> dict:
        """
        Aggregate a list of sentiment results into an overall score.
        
        Args:
            results: List of dicts with 'score' key
        
        Returns:
            Dict with overall sentiment, avg score, and breakdown
        """
        if not results:
            return {
                "overall_sentiment": "Neutral",
                "sentiment_score": 0.0,
                "total_analyzed": 0,
                "bullish_count": 0,
                "bearish_count": 0,
                "neutral_count": 0,
            }

        scores = [r.get("score", 0.0) for r in results]
        avg_score = round(sum(scores) / len(scores), 4)

        bullish = sum(1 for r in results if r.get("sentiment") == "Bullish")
        bearish = sum(1 for r in results if r.get("sentiment") == "Bearish")
        neutral = sum(1 for r in results if r.get("sentiment") == "Neutral")

        if avg_score >= 0.3:
            overall = "Bullish"
        elif avg_score <= -0.3:
            overall = "Bearish"
        else:
            overall = "Neutral"

        return {
            "overall_sentiment": overall,
            "sentiment_score": avg_score,
            "total_analyzed": len(results),
            "bullish_count": bullish,
            "bearish_count": bearish,
            "neutral_count": neutral,
            "individual_results": results,
        }
