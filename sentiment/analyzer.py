"""
Core Sentiment Analyzer — uses Gemini LLM with VADER fallback.
Supports multiple API keys with automatic rotation on rate limits.
"""

import json
import time
from google import genai
from config.config import GEMINI_API_KEYS, GEMINI_MODEL, LLM_TEMPERATURE
from sentiment.prompts import SENTIMENT_ANALYSIS_PROMPT, BATCH_SENTIMENT_PROMPT
from sentiment.scorer import SentimentScorer
from sentiment.finbert import get_finbert

MAX_RETRIES = 2
RETRY_BASE_DELAY = 5  # seconds
BATCH_CHUNK_SIZE = 5  # smaller chunks for thinking model


class GeminiKeyPool:
    """
    Manages a pool of Gemini API keys with automatic rotation.
    When one key hits a quota limit, it switches to the next.
    """

    def __init__(self, api_keys: list[str]):
        self.keys = api_keys
        self.clients = []
        self.current_index = 0
        self.exhausted_keys = set()  # Track daily-exhausted keys

        for key in self.keys:
            try:
                client = genai.Client(
                    api_key=key,
                    http_options={"api_version": "v1beta"},
                )
                self.clients.append(client)
            except Exception as e:
                print(f"[WARNING] Failed to init key ...{key[-4:]}: {e}")
                self.clients.append(None)

        active = sum(1 for c in self.clients if c is not None)
        print(f"[INFO] Gemini Key Pool: {active}/{len(self.keys)} keys active")

    @property
    def current_client(self):
        """Get the current active client."""
        if not self.clients:
            return None
        return self.clients[self.current_index]

    @property
    def current_key_label(self):
        """Get a safe label for the current key (last 4 chars)."""
        if not self.keys:
            return "none"
        return f"...{self.keys[self.current_index][-4:]}"

    def rotate(self) -> bool:
        """
        Rotate to the next available key.
        Returns True if a new key is available, False if all exhausted.
        """
        self.exhausted_keys.add(self.current_index)
        print(f"       [Key {self.current_key_label}] Quota hit — rotating...")

        # Find next non-exhausted key
        for _ in range(len(self.keys)):
            self.current_index = (self.current_index + 1) % len(self.keys)
            if self.current_index not in self.exhausted_keys and self.clients[self.current_index] is not None:
                print(f"       [Switched to key {self.current_key_label}]")
                return True

        print(f"       [ALL {len(self.keys)} KEYS EXHAUSTED] Falling back to VADER.")
        return False

    @property
    def has_available_keys(self) -> bool:
        """Check if any keys are still available."""
        return any(
            i not in self.exhausted_keys and c is not None
            for i, c in enumerate(self.clients)
        )


class SentimentAnalyzer:
    """
    3-Tier Sentiment Pipeline:
      1. FinBERT (primary) — local ML model, FREE, unlimited, handles all texts
      2. Gemini (premium) — only for ambiguous cases where FinBERT confidence < 0.6
      3. VADER (fallback) — if both FinBERT and Gemini unavailable
    """

    CONFIDENCE_THRESHOLD = 0.6  # Below this, escalate to Gemini

    def __init__(self):
        self.scorer = SentimentScorer()
        self.llm_available = False
        self.finbert_available = False
        self.key_pool = None

        # Tier 1: Load FinBERT (local ML model)
        try:
            self.finbert = get_finbert()
            self.finbert.load()
            self.finbert_available = True
        except Exception as e:
            print(f"[WARNING] FinBERT failed to load: {e}. Will use VADER/Gemini.")
            self.finbert = None

        # Tier 2: Initialize Gemini (for ambiguous cases)
        if GEMINI_API_KEYS:
            self.key_pool = GeminiKeyPool(GEMINI_API_KEYS)
            if self.key_pool.has_available_keys:
                self.model_name = GEMINI_MODEL
                self.llm_available = True
                print(f"[INFO] Gemini LLM initialized ({GEMINI_MODEL}) with {len(GEMINI_API_KEYS)} key(s)")
            else:
                print(f"[WARNING] No valid Gemini keys.")
        else:
            print("[INFO] No GEMINI_API_KEY(s) set.")

        # Summary
        tiers = []
        if self.finbert_available:
            tiers.append("FinBERT")
        if self.llm_available:
            tiers.append("Gemini")
        tiers.append("VADER")
        print(f"[INFO] Sentiment pipeline: {' → '.join(tiers)}")

    def analyze_single(self, text: str) -> dict:
        """
        Analyze sentiment of a single text using the 3-tier pipeline.
        FinBERT → Gemini (if ambiguous) → VADER (fallback)
        """
        # Tier 1: FinBERT
        if self.finbert_available:
            try:
                result = self.finbert.analyze(text)
                result["method"] = "finbert"
                # If confident enough, return directly
                if result.get("confidence", 0) >= self.CONFIDENCE_THRESHOLD:
                    return result
                # Ambiguous — escalate to Gemini
                if self.llm_available:
                    try:
                        return self._llm_analyze(text)
                    except Exception:
                        return result  # Return FinBERT result if Gemini fails
                return result
            except Exception as e:
                pass  # Fall through to next tier

        # Tier 2: Gemini directly (if FinBERT unavailable)
        if self.llm_available:
            try:
                return self._llm_analyze(text)
            except Exception as e:
                pass

        # Tier 3: VADER
        return self.scorer.vader_score(text)

    def analyze_batch(self, texts: list[str]) -> list[dict]:
        """
        Analyze multiple texts using the 3-tier pipeline.
        FinBERT handles all → ambiguous ones escalated to Gemini → VADER fallback.
        """
        if not texts:
            return []

        # Tier 1: FinBERT batch analysis (fast, local)
        if self.finbert_available:
            try:
                finbert_results = self.finbert.analyze_batch(texts)
                for r in finbert_results:
                    r["method"] = "finbert"

                # Find ambiguous items (low confidence)
                ambiguous_indices = [
                    i for i, r in enumerate(finbert_results)
                    if r.get("confidence", 0) < self.CONFIDENCE_THRESHOLD
                ]

                finbert_confident = len(texts) - len(ambiguous_indices)
                print(f"       [FinBERT] {finbert_confident}/{len(texts)} confident, {len(ambiguous_indices)} ambiguous")

                # Tier 2: Send ambiguous items to Gemini
                if ambiguous_indices and self.llm_available:
                    ambiguous_texts = [texts[i] for i in ambiguous_indices]
                    try:
                        llm_results = self._llm_batch_analyze(ambiguous_texts)
                        for idx, llm_result in zip(ambiguous_indices, llm_results):
                            llm_result["method"] = "gemini"
                            finbert_results[idx] = llm_result
                        print(f"       [Gemini] Refined {len(llm_results)} ambiguous items")
                    except Exception as e:
                        print(f"       [Gemini] Failed for ambiguous items: {type(e).__name__}. Keeping FinBERT results.")

                return finbert_results

            except Exception as e:
                print(f"       [FinBERT] Batch failed: {e}. Falling through...")

        # Tier 2: Gemini only (if FinBERT unavailable)
        if self.llm_available:
            try:
                return self._llm_batch_analyze(texts)
            except Exception as e:
                print(f"       [Gemini] Batch failed: {e}. Falling back to VADER.")

        # Tier 3: VADER fallback
        return [self.scorer.vader_score(t) for t in texts]

    def analyze_news(self, news_items: list[dict]) -> list[dict]:
        """
        Analyze sentiment of ALL news headlines using FinBERT (no limit needed).
        FinBERT is local — can process all 100+ headlines in seconds.
        """
        results = []
        all_texts = [item["headline"] for item in news_items if item.get("headline")]

        # FinBERT handles everything — no need to limit to top 15 anymore
        sentiments = self.analyze_batch(all_texts)

        text_idx = 0
        for item in news_items:
            if item.get("headline"):
                if text_idx < len(sentiments):
                    result = sentiments[text_idx]
                    text_idx += 1
                else:
                    result = self.scorer.vader_score(item["headline"])
                result["source"] = item.get("source", "Unknown")
                result["category"] = item.get("category", "general")
                result["type"] = "news"
                results.append(result)

        return results

    def analyze_social(self, social_posts: list[dict]) -> list[dict]:
        """
        Analyze sentiment of social media post dicts.
        
        Args:
            social_posts: List of social post dicts with 'post' key
        
        Returns:
            List of sentiment results with platform info preserved
        """
        results = []
        texts = [item["post"] for item in social_posts if item.get("post")]

        sentiments = self.analyze_batch(texts)

        for i, item in enumerate(social_posts):
            if i < len(sentiments):
                result = sentiments[i]
                result["platform"] = item.get("platform", "Unknown")
                result["ticker"] = item.get("ticker", "")
                result["user"] = item.get("user", "")
                result["type"] = "social"
                results.append(result)

        return results

    def get_aggregate(self, news_results: list[dict], social_results: list[dict]) -> dict:
        """
        Get the aggregate sentiment across news + social.
        
        Args:
            news_results: Analyzed news sentiment results
            social_results: Analyzed social sentiment results
        
        Returns:
            Aggregated sentiment dict
        """
        all_results = news_results + social_results
        return self.scorer.aggregate_scores(all_results)

    # ─── Private LLM Methods ──────────────────────────────────

    def _llm_call_with_retry(self, prompt: str, max_tokens: int = 256) -> str:
        """
        Make an LLM call with retry + key rotation on quota limits.
        If current key is exhausted, rotates to next key and retries.
        """
        while self.key_pool and self.key_pool.has_available_keys:
            client = self.key_pool.current_client
            if client is None:
                if not self.key_pool.rotate():
                    break
                continue

            for attempt in range(MAX_RETRIES):
                try:
                    response = client.models.generate_content(
                        model=self.model_name,
                        contents=prompt,
                        config={
                            "temperature": LLM_TEMPERATURE,
                            "max_output_tokens": max_tokens,
                        },
                    )
                    # gemini-2.5-flash (thinking model) may have text in candidates
                    text = response.text
                    if text is None and response.candidates:
                        for part in response.candidates[0].content.parts:
                            if part.text:
                                text = part.text
                                break
                    if text is None:
                        raise ValueError("Empty response from Gemini")
                    return text
                except Exception as e:
                    error_str = str(e)
                    # Quota exhausted on this key → rotate to next
                    if "RESOURCE_EXHAUSTED" in error_str or ("429" in error_str and "PerDay" in error_str):
                        if self.key_pool.rotate():
                            break  # Break inner retry loop, restart with new key
                        else:
                            raise RuntimeError("ALL_KEYS_EXHAUSTED")
                    # Transient rate limit (per-minute) → wait and retry same key
                    elif "429" in error_str:
                        delay = RETRY_BASE_DELAY * (attempt + 1)
                        print(f"       [Rate limited key {self.key_pool.current_key_label}] Waiting {delay}s (retry {attempt + 1}/{MAX_RETRIES})...")
                        time.sleep(delay)
                    else:
                        raise e
            else:
                # All retries exhausted on this key → rotate
                if not self.key_pool.rotate():
                    raise RuntimeError("ALL_KEYS_EXHAUSTED")

        raise RuntimeError("ALL_KEYS_EXHAUSTED")

    def _llm_analyze(self, text: str) -> dict:
        """Single text LLM analysis."""
        prompt = SENTIMENT_ANALYSIS_PROMPT.format(text=text)
        response_text = self._llm_call_with_retry(prompt, max_tokens=256)
        result = self._parse_llm_response(response_text)
        result["text"] = text
        result["method"] = "Gemini"
        return result

    def _llm_batch_analyze(self, texts: list[str]) -> list[dict]:
        """Batch LLM analysis — chunks texts and makes multiple calls if needed."""
        all_results = []
        llm_failed_permanently = False

        # Process in chunks to avoid token limits
        for i in range(0, len(texts), BATCH_CHUNK_SIZE):
            chunk = texts[i:i + BATCH_CHUNK_SIZE]
            chunk_num = (i // BATCH_CHUNK_SIZE) + 1
            total_chunks = (len(texts) + BATCH_CHUNK_SIZE - 1) // BATCH_CHUNK_SIZE

            # If LLM already failed (daily limit), skip straight to VADER
            if llm_failed_permanently:
                all_results.extend([self.scorer.vader_score(t) for t in chunk])
                continue

            print(f"       [LLM] Processing chunk {chunk_num}/{total_chunks} ({len(chunk)} items)...")

            numbered_texts = "\n".join([f"{j+1}. \"{t}\"" for j, t in enumerate(chunk)])
            prompt = BATCH_SENTIMENT_PROMPT.format(texts=numbered_texts)

            try:
                response_text = self._llm_call_with_retry(prompt, max_tokens=4096)
                results = self._parse_llm_batch_response(response_text)

                if len(results) >= len(chunk):
                    for r in results[:len(chunk)]:
                        r["method"] = "Gemini"
                    all_results.extend(results[:len(chunk)])
                else:
                    for r in results:
                        r["method"] = "Gemini"
                    all_results.extend(results)
                    # Pad with VADER for any missing
                    for j in range(len(results), len(chunk)):
                        all_results.append(self.scorer.vader_score(chunk[j]))

                # Small delay between chunks to avoid rate limits
                if i + BATCH_CHUNK_SIZE < len(texts):
                    time.sleep(2)

            except Exception as e:
                error_str = str(e)
                if "ALL_KEYS_EXHAUSTED" in error_str or "DAILY_QUOTA_EXHAUSTED" in error_str:
                    llm_failed_permanently = True
                    print(f"       [All Gemini keys exhausted] Switching to VADER for all remaining.")
                else:
                    print(f"       [WARNING] Chunk {chunk_num} LLM failed: {type(e).__name__}: {error_str[:200]}. Using VADER.")
                all_results.extend([self.scorer.vader_score(t) for t in chunk])

        return all_results

    def _clean_llm_json(self, response_text: str) -> str:
        """Clean LLM response to extract valid JSON."""
        import re
        cleaned = response_text.strip()
        
        # Remove markdown code blocks (```json ... ``` or ``` ... ```)
        match = re.search(r'```(?:json)?\s*\n?(.*?)```', cleaned, re.DOTALL)
        if match:
            cleaned = match.group(1).strip()
        
        # Remove any trailing commas before } or ]
        cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)
        
        # Fix common issues: single quotes -> double quotes
        # Only if it won't break valid JSON
        try:
            json.loads(cleaned)
            return cleaned
        except json.JSONDecodeError:
            pass
        
        # Try to find JSON array or object in the text
        for pattern in [r'(\[.*\])', r'(\{.*\})']:
            match = re.search(pattern, cleaned, re.DOTALL)
            if match:
                try:
                    json.loads(match.group(1))
                    return match.group(1)
                except json.JSONDecodeError:
                    continue
        
        return cleaned

    def _parse_llm_response(self, response_text: str) -> dict:
        """Parse a single JSON response from LLM."""
        cleaned = self._clean_llm_json(response_text)

        try:
            data = json.loads(cleaned)
            return {
                "sentiment": data.get("sentiment", "Neutral"),
                "score": float(data.get("score", 0.0)),
                "reasoning": data.get("reasoning", ""),
            }
        except (json.JSONDecodeError, ValueError):
            return {"sentiment": "Neutral", "score": 0.0, "reasoning": "Parse error"}

    def _parse_llm_batch_response(self, response_text: str) -> list[dict]:
        """Parse a batch JSON array response from LLM."""
        cleaned = self._clean_llm_json(response_text)

        data = json.loads(cleaned)
        if not isinstance(data, list):
            raise ValueError("Expected JSON array")

        results = []
        for item in data:
            results.append({
                "text": item.get("text", ""),
                "sentiment": item.get("sentiment", "Neutral"),
                "score": float(item.get("score", 0.0)),
            })
        return results
