import os
import re
import requests
from datetime import datetime, timedelta
from collections import Counter
import numpy as np

# ── Sentiment lexicon (no heavy model needed out-of-the-box) ──────────────────
POSITIVE_WORDS = {
    "surge", "soar", "rally", "gain", "profit", "beat", "growth", "record",
    "strong", "positive", "bullish", "upgrade", "buy", "outperform", "rise",
    "climb", "jump", "boost", "exceed", "optimistic", "recovery", "robust",
    "breakthrough", "innovative", "expand", "partnership", "win", "success",
    "revenue", "dividend", "acquisition", "launch", "approval", "milestone"
}

NEGATIVE_WORDS = {
    "crash", "plunge", "fall", "loss", "miss", "decline", "bearish", "sell",
    "downgrade", "underperform", "drop", "slump", "risk", "concern", "weak",
    "negative", "layoff", "cut", "recession", "debt", "fraud", "lawsuit",
    "investigation", "recall", "ban", "penalty", "fine", "warning", "fear",
    "volatile", "uncertainty", "default", "bankruptcy", "crisis", "scandal"
}

INTENSIFIERS = {"very", "extremely", "highly", "significantly", "massively", "sharply"}
NEGATORS     = {"not", "no", "never", "neither", "nor", "hardly", "barely"}


def clean_text(text: str) -> str:
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^a-zA-Z\s]", " ", text)
    return text.lower()


def score_sentence(sentence: str) -> float:
    words  = sentence.split()
    score  = 0.0
    negate = False
    boost  = 1.0

    for i, w in enumerate(words):
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
        boost  = 1.0

    return score


def analyse_text(text: str) -> dict:
    cleaned   = clean_text(text)
    sentences = [s.strip() for s in re.split(r'[.!?]', cleaned) if len(s.strip()) > 10]
    if not sentences:
        return {"score": 0.0, "label": "neutral", "confidence": 0.0}

    scores = [score_sentence(s) for s in sentences]
    total  = sum(scores)
    avg    = total / len(scores)

    # Normalise to -1 … +1
    norm = max(-1.0, min(1.0, avg / 3.0))

    if norm > 0.15:
        label = "positive"
    elif norm < -0.15:
        label = "negative"
    else:
        label = "neutral"

    confidence = min(abs(norm) * 100 + 40, 95)

    # Top keywords
    words    = cleaned.split()
    filtered = [w for w in words if len(w) > 4 and w not in
                {"about", "their", "which", "would", "could", "should", "there",
                 "these", "those", "being", "after", "while", "since", "where"}]
    keywords = [w for w, _ in Counter(filtered).most_common(8)]

    return {
        "score":      round(norm, 3),
        "label":      label,
        "confidence": round(confidence, 1),
        "keywords":   keywords,
        "sentences":  len(sentences),
    }


# ── News fetching via NewsAPI (free tier) ─────────────────────────────────────

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")          # set in .env or export


def fetch_news(query: str, max_articles: int = 15) -> list[dict]:
    """
    Fetch news from NewsAPI.  Falls back to mock data when no key is set.
    """
    if not NEWSAPI_KEY:
        return _mock_news(query)

    url    = "https://newsapi.org/v2/everything"
    params = {
        "q":        query,
        "language": "en",
        "sortBy":   "publishedAt",
        "pageSize": max_articles,
        "from":     (datetime.utcnow() - timedelta(days=3)).strftime("%Y-%m-%d"),
        "apiKey":   NEWSAPI_KEY,
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    articles = r.json().get("articles", [])

    return [
        {
            "title":       a.get("title", ""),
            "description": a.get("description", "") or "",
            "source":      a.get("source", {}).get("name", "Unknown"),
            "url":         a.get("url", "#"),
            "published":   a.get("publishedAt", "")[:10],
        }
        for a in articles if a.get("title")
    ]


def _mock_news(query: str) -> list[dict]:
    """Demo articles used when no API key is configured."""
    templates = [
        ("{q} reports record quarterly earnings, beating analyst expectations by 12%", "positive"),
        ("{q} stock surges after partnership announcement with major tech firm",         "positive"),
        ("Investors bullish on {q} following strong product launch results",            "positive"),
        ("{q} faces regulatory scrutiny over data privacy concerns",                    "negative"),
        ("Market volatility impacts {q} shares amid broader economic uncertainty",      "negative"),
        ("{q} announces layoffs affecting 8% of global workforce",                      "negative"),
        ("{q} maintains steady growth in emerging markets this quarter",                "neutral"),
        ("Analysts remain divided on {q} outlook heading into next fiscal year",        "neutral"),
        ("{q} expands operations into Southeast Asia with new strategic investment",    "positive"),
        ("Rising interest rates cast shadow over {q} long-term valuation",             "negative"),
        ("{q} CEO outlines five-year innovation roadmap at annual investor day",        "positive"),
        ("Supply chain disruptions continue to pressure {q} margins",                  "negative"),
    ]
    today = datetime.utcnow()
    news  = []
    for i, (title_tmpl, _) in enumerate(templates):
        date = (today - timedelta(days=i % 3)).strftime("%Y-%m-%d")
        news.append({
            "title":       title_tmpl.replace("{q}", query),
            "description": f"Full coverage of {query} — article {i+1}.",
            "source":      ["Reuters", "Bloomberg", "CNBC", "WSJ", "FT"][i % 5],
            "url":         "#",
            "published":   date,
        })
    return news


# ── Full pipeline ─────────────────────────────────────────────────────────────

def analyse_topic(query: str) -> dict:
    articles = fetch_news(query)

    results = []
    for a in articles:
        text     = f"{a['title']} {a['description']}"
        analysis = analyse_text(text)
        results.append({**a, **analysis})

    if not results:
        return {"query": query, "articles": [], "summary": {}}

    scores     = [r["score"] for r in results]
    avg_score  = round(np.mean(scores), 3)
    labels     = [r["label"] for r in results]
    label_dist = Counter(labels)

    if avg_score > 0.1:
        overall = "positive"
    elif avg_score < -0.1:
        overall = "negative"
    else:
        overall = "neutral"

    # Aggregate keywords
    all_kw   = [kw for r in results for kw in r.get("keywords", [])]
    top_kw   = [w for w, _ in Counter(all_kw).most_common(12)]

    # Score over time
    by_date = {}
    for r in results:
        d = r.get("published", "unknown")
        by_date.setdefault(d, []).append(r["score"])
    trend = [
        {"date": d, "avg_score": round(np.mean(v), 3)}
        for d, v in sorted(by_date.items())
    ]

    return {
        "query":    query,
        "articles": results,
        "summary": {
            "total":        len(results),
            "avg_score":    avg_score,
            "overall":      overall,
            "positive":     label_dist.get("positive", 0),
            "negative":     label_dist.get("negative", 0),
            "neutral":      label_dist.get("neutral",  0),
            "top_keywords": top_kw,
            "trend":        trend,
        }
    }


if __name__ == "__main__":
    import json
    result = analyse_topic("Apple")
    print(json.dumps(result["summary"], indent=2))
