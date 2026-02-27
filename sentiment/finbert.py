"""
FinBERT-based financial sentiment analysis.
Uses ProsusAI/finbert — a BERT model fine-tuned on financial text.
Loads ONCE into memory and serves unlimited requests (no API limits).

3-Tier Pipeline:
  1. FinBERT (primary) — handles all headlines locally
  2. Gemini (premium) — only called for ambiguous cases
  3. VADER (fallback) — if both FinBERT and Gemini unavailable
"""

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np


class FinBERTAnalyzer:
    """
    Financial sentiment analyzer using FinBERT.
    Loads the model once and caches it in memory.
    """

    # Label mapping from FinBERT output
    LABEL_MAP = {0: "Positive", 1: "Negative", 2: "Neutral"}

    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._loaded = False

    def load(self):
        """Load FinBERT model and tokenizer. Call once at startup."""
        if self._loaded:
            return

        print("[INFO] Loading FinBERT model (first time may download ~400MB)...")
        model_name = "ProsusAI/finbert"

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        # Prefer pytorch_model.bin (already cached) over safetensors to avoid re-download
        try:
            self.model = AutoModelForSequenceClassification.from_pretrained(
                model_name, use_safetensors=False
            )
        except Exception:
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()  # Set to inference mode (no training)
        self._loaded = True

        device_label = "GPU" if self.device == "cuda" else "CPU"
        print(f"[INFO] FinBERT loaded on {device_label}")

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def analyze(self, text: str) -> dict:
        """
        Analyze a single text for sentiment.

        Returns:
            dict with keys: sentiment, score, confidence
            - sentiment: 'Bullish', 'Bearish', or 'Neutral'
            - score: float from -1.0 to 1.0
            - confidence: float from 0.0 to 1.0 (how sure the model is)
        """
        if not self._loaded:
            self.load()

        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True,
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)
            probabilities = torch.softmax(outputs.logits, dim=1).cpu().numpy()[0]

        # probabilities: [positive, negative, neutral]
        pos_prob = float(probabilities[0])
        neg_prob = float(probabilities[1])
        neu_prob = float(probabilities[2])

        # Determine sentiment label
        max_idx = int(np.argmax(probabilities))
        confidence = float(probabilities[max_idx])

        # Convert to our standard format
        # Score: positive contributes +, negative contributes -, neutral stays near 0
        score = pos_prob - neg_prob  # Range: -1.0 to +1.0

        if max_idx == 0:  # Positive
            sentiment = "Bullish"
        elif max_idx == 1:  # Negative
            sentiment = "Bearish"
        else:  # Neutral
            sentiment = "Neutral"

        return {
            "sentiment": sentiment,
            "score": round(score, 4),
            "confidence": round(confidence, 4),
        }

    def analyze_batch(self, texts: list[str], batch_size: int = 16) -> list[dict]:
        """
        Analyze multiple texts in batches (much faster than one-by-one).

        Args:
            texts: List of headlines/posts to analyze
            batch_size: How many texts to process at once (16 is good for CPU)

        Returns:
            List of dicts with sentiment, score, confidence for each text
        """
        if not self._loaded:
            self.load()

        results = []

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]

            inputs = self.tokenizer(
                batch_texts,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True,
            ).to(self.device)

            with torch.no_grad():
                outputs = self.model(**inputs)
                all_probs = torch.softmax(outputs.logits, dim=1).cpu().numpy()

            for probs in all_probs:
                pos_prob = float(probs[0])
                neg_prob = float(probs[1])

                max_idx = int(np.argmax(probs))
                confidence = float(probs[max_idx])
                score = pos_prob - neg_prob

                if max_idx == 0:
                    sentiment = "Bullish"
                elif max_idx == 1:
                    sentiment = "Bearish"
                else:
                    sentiment = "Neutral"

                results.append({
                    "sentiment": sentiment,
                    "score": round(score, 4),
                    "confidence": round(confidence, 4),
                })

        return results


# ─── Singleton instance (load once, use everywhere) ──────────
_finbert_instance = None


def get_finbert() -> FinBERTAnalyzer:
    """Get or create the singleton FinBERT instance."""
    global _finbert_instance
    if _finbert_instance is None:
        _finbert_instance = FinBERTAnalyzer()
    return _finbert_instance
