import os
import re
import requests
from datetime import datetime, timedelta
from collections import Counter
from typing import Any

import numpy as np
from dotenv import load_dotenv

load_dotenv()

# ── Sentiment lexicon ─────────────────────────────────────────────────────────

POSITIVE_WORDS = {
    "surge", "soar", "rally", "gain", "profit", "beat", "growth", "record",
    "strong", "positive", "bullish", "upgrade", "buy", "outperform", "rise",
    "climb", "jump", "boost", "exceed", "optimistic", "recovery", "robust",
    "breakthrough", "innovative", "expand", "partnership", "win", "success",
    "revenue", "dividend", "acquisition", "launch", "approval", "milestone",
    "increase", "improvement", "efficient", "leading", "advanced", "award",
    "hire", "invest", "opportunity", "demand", "upside", "accelerate",
}

NEGATIVE_WORDS = {
    "crash", "plunge", "fall", "loss", "miss", "decline", "bearish", "sell",
    "downgrade", "underperform", "drop", "slump", "risk", "concern", "weak",
    "negative", "layoff", "cut", "recession", "debt", "fraud", "lawsuit",
    "investigation", "recall", "ban", "penalty", "fine", "warning", "fear",
    "volatile", "uncertainty", "default", "bankruptcy", "crisis", "scandal",
    "delay", "fail", "failure", "problem", "issue", "shortage", "dispute",
    "conflict", "tariff", "sanction", "downside", "decelerate", "miss",
}

INTENSIFIERS = {"very", "extremely", "highly", "significantly", "massively", "sharply"}
NEGATORS = {"not", "no", "never", "neither", "nor", "hardly", "barely"}

# Common stopwords to exclude from keyword extraction
_STOPWORDS = {
    "about", "their", "which", "would", "could", "should", "there",
    "these", "those", "being", "after", "while", "since", "where",
    "with", "from", "that", "this", "have", "were", "been", "they",
    "will", "when", "what", "said", "also", "more", "than", "into",
    "over", "some", "such", "most", "other", "than", "then", "just",
    "like", "time", "year", "said", "each", "make", "does", "going",
    "company", "market", "year", "says", "report", "share", "shares",
    "quarter", "percent", "billion", "million", "news", "according",
}


def clean_text(text: str) -> str:
    """Remove URLs, non-alpha characters, and lowercase."""
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^a-zA-Z\s]", " ", text)
    return text.lower()


def score_sentence(sentence: str) -> float:
    """
    Score a single sentence using the lexicon.
    Handles negation (not, never) and intensity boosting (very, extremely).
    Returns a raw score; positive values indicate positive sentiment.
    """
    words = sentence.split()
    score = 0.0
    negate = False
    boost = 1.0

    for w in words:
        if w in NEGATORS:
            negate = True
            continue
        if w in INTENSIFIERS:
            boost = 1.5
            continue
        if w in POSITIVE_WORDS:
            score += (1.0 * boost) * (-1 if negate else 1)
        elif w in NEGATIVE_WORDS:
            score -= (1.0 * boost) * (-1 if negate else 1)
        negate = False
        boost = 1.0

    return score


def analyse_text(text: str) -> dict[str, Any]:
    """
    Run the full sentiment pipeline on a piece of text.

    Returns a dict with keys: score, label, confidence, keywords, sentences.
    Score is normalised to [-1, +1]. Label is one of: positive, neutral, negative.
    """
    if not text or not text.strip():
        return {"score": 0.0, "label": "neutral", "confidence": 0.0, "keywords": [], "sentences": 0}

    cleaned = clean_text(text)
    sentences = [s.strip() for s in re.split(r"[.!?]", cleaned) if len(s.strip()) > 10]

    if not sentences:
        return {"score": 0.0, "label": "neutral", "confidence": 0.0, "keywords": [], "sentences": 0}

    scores = [score_sentence(s) for s in sentences]
    avg = sum(scores) / len(scores)

    # Normalise to [-1, +1]; dividing by 3 handles typical sentence densities
    norm = max(-1.0, min(1.0, avg / 3.0))

    if norm > 0.15:
        label = "positive"
    elif norm < -0.15:
        label = "negative"
    else:
        label = "neutral"

    # Confidence: absolute magnitude scaled up, floored at 40%, capped at 95%
    confidence = min(abs(norm) * 100 + 40, 95)

    # Extract top keywords (words longer than 4 chars, excluding stopwords)
    words = cleaned.split()
    filtered = [w for w in words if len(w) > 4 and w not in _STOPWORDS]
    keywords = [w for w, _ in Counter(filtered).most_common(8)]

    return {
        "score": round(norm, 3),
        "label": label,
        "confidence": round(confidence, 1),
        "keywords": keywords,
        "sentences": len(sentences),
    }


# ── News fetching via NewsAPI ─────────────────────────────────────────────────

def _get_newsapi_key() -> str:
    """Read the API key at call time so it respects late .env loads."""
    return os.getenv("NEWSAPI_KEY", "").strip()


def fetch_news(query: str, max_articles: int = 15) -> list[dict[str, Any]]:
    """
    Fetch recent English-language articles from NewsAPI for the given query.
    Falls back to _mock_news() when no API key is set or a network error occurs.
    """
    key = _get_newsapi_key()
    if not key:
        return _mock_news(query)

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": max_articles,
        "from": (datetime.utcnow() - timedelta(days=3)).strftime("%Y-%m-%d"),
        "apiKey": key,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "ok":
            # API returned an error payload (e.g. invalid key, rate limit)
            code = data.get("code", "unknown")
            if code == "apiKeyInvalid":
                raise ValueError("The NEWSAPI_KEY is invalid. Check your .env file.")
            if code == "rateLimited":
                raise RuntimeError("NewsAPI rate limit reached. Try again later.")
            raise RuntimeError(f"NewsAPI error: {data.get('message', code)}")

        articles = data.get("articles", [])
        return [
            {
                "title": a.get("title") or "",
                "description": a.get("description") or "",
                "source": (a.get("source") or {}).get("name", "Unknown"),
                "url": a.get("url") or "#",
                "published": (a.get("publishedAt") or "")[:10],
            }
            for a in articles
            if a.get("title") and a.get("title") != "[Removed]"
        ]

    except requests.exceptions.ConnectionError:
        raise RuntimeError("Could not reach NewsAPI. Check your internet connection.")
    except requests.exceptions.Timeout:
        raise RuntimeError("NewsAPI request timed out. Try again.")
    except requests.exceptions.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "?"
        if status == 401:
            raise ValueError("NewsAPI key is unauthorized. Verify NEWSAPI_KEY in .env.")
        if status == 429:
            raise RuntimeError("NewsAPI rate limit exceeded.")
        raise RuntimeError(f"NewsAPI HTTP error {status}.")


def _mock_news(query: str) -> list[dict[str, Any]]:
    """
    Return realistic demo articles when no API key is configured.
    Useful for local development and the demo script.
    """
    templates = [
        ("{q} reports record quarterly earnings, beating analyst expectations by 12%", "positive"),
        ("{q} stock surges after partnership announcement with major tech firm", "positive"),
        ("Investors bullish on {q} following strong product launch results", "positive"),
        ("{q} expands operations into Southeast Asia with new strategic investment", "positive"),
        ("{q} CEO outlines five-year innovation roadmap at annual investor day", "positive"),
        ("{q} faces regulatory scrutiny over data privacy concerns", "negative"),
        ("Market volatility impacts {q} shares amid broader economic uncertainty", "negative"),
        ("{q} announces layoffs affecting 8% of global workforce", "negative"),
        ("Rising interest rates cast shadow over {q} long-term valuation", "negative"),
        ("Supply chain disruptions continue to pressure {q} margins", "negative"),
        ("{q} maintains steady growth in emerging markets this quarter", "neutral"),
        ("Analysts remain divided on {q} outlook heading into next fiscal year", "neutral"),
    ]
    today = datetime.utcnow()
    news = []
    for i, (title_tmpl, _) in enumerate(templates):
        date = (today - timedelta(days=i % 3)).strftime("%Y-%m-%d")
        news.append({
            "title": title_tmpl.replace("{q}", query),
            "description": f"Full coverage of {query} developments — article {i + 1}.",
            "source": ["Reuters", "Bloomberg", "CNBC", "WSJ", "Financial Times"][i % 5],
            "url": "#",
            "published": date,
        })
    return news


# ── Full analysis pipeline ────────────────────────────────────────────────────

def analyse_topic(query: str) -> dict[str, Any]:
    """
    Fetch news for a topic and run sentiment analysis on every article.

    Returns a dict with:
      - query: the original search string
      - articles: list of per-article dicts (title, description, source, url,
                  published, score, label, confidence, keywords, sentences)
      - summary: aggregate statistics across all articles
    """
    if not query or not query.strip():
        raise ValueError("Query must not be empty.")

    articles = fetch_news(query.strip())

    if not articles:
        return {"query": query, "articles": [], "summary": {}}

    results = []
    for a in articles:
        text = f"{a['title']} {a['description']}"
        analysis = analyse_text(text)
        results.append({**a, **analysis})

    scores = [r["score"] for r in results]
    avg_score = round(float(np.mean(scores)), 3)
    label_dist = Counter(r["label"] for r in results)

    if avg_score > 0.1:
        overall = "positive"
    elif avg_score < -0.1:
        overall = "negative"
    else:
        overall = "neutral"

    # Aggregate top keywords across all articles
    all_kw = [kw for r in results for kw in r.get("keywords", [])]
    top_kw = [w for w, _ in Counter(all_kw).most_common(12)]

    # Daily average scores for the trend chart
    by_date: dict[str, list[float]] = {}
    for r in results:
        d = r.get("published") or "unknown"
        by_date.setdefault(d, []).append(r["score"])

    trend = [
        {"date": d, "avg_score": round(float(np.mean(v)), 3)}
        for d, v in sorted(by_date.items())
    ]

    return {
        "query": query,
        "articles": results,
        "summary": {
            "total": len(results),
            "avg_score": avg_score,
            "overall": overall,
            "positive": label_dist.get("positive", 0),
            "negative": label_dist.get("negative", 0),
            "neutral": label_dist.get("neutral", 0),
            "top_keywords": top_kw,
            "trend": trend,
        },
    }


if __name__ == "__main__":
    import json

    result = analyse_topic("Apple")
    print(json.dumps(result["summary"], indent=2))
