# 📰 SentimentPulse – Real-Time News Sentiment Analyser

A full-stack NLP application that fetches live news headlines for any stock, company, or topic and performs sentiment analysis — with an interactive dashboard showing scores, trends, keyword clouds, and article-level breakdowns.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-black?logo=flask)
![NLP](https://img.shields.io/badge/NLP-Lexicon%20%2B%20Rules-purple)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🚀 Features

- **Real-Time News** – Fetches latest headlines via NewsAPI (free tier)
- **Financial NLP** – Domain-specific lexicon with negation handling & intensity boosting
- **Sentiment Scoring** – Per-article score (-1 to +1) + overall signal
- **Trend Chart** – Sentiment over time across fetched articles
- **Distribution Doughnut** – Positive / Negative / Neutral breakdown
- **Keyword Cloud** – Most frequent meaningful terms across all articles
- **REST API** – `/api/analyse` and `/api/compare` endpoints
- **Zero-dependency fallback** – Works with mock data when no API key is set

---

## 🧠 How Sentiment Works

```
Raw headline + description
        ↓
   Text cleaning (remove URLs, punctuation, lowercase)
        ↓
   Sentence tokenisation
        ↓
   Lexicon scoring per sentence
   (POSITIVE_WORDS / NEGATIVE_WORDS)
   + negation detection (not, never, no…)
   + intensity boosting (very, extremely…)
        ↓
   Normalise avg score → [-1, +1]
        ↓
   Label: positive (>0.15) | neutral | negative (<-0.15)
```

---

## 📁 Project Structure

```
news-sentiment-analyser/
├── app.py              # Flask app & REST API
├── sentiment.py        # NLP engine + NewsAPI fetcher
├── requirements.txt
├── .env.example
└── templates/
    └── index.html      # Interactive dashboard (Chart.js)
```

---

## ⚙️ Setup & Run

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/news-sentiment-analyser.git
cd news-sentiment-analyser

# 2. Virtual environment
python -m venv venv
source venv/bin/activate

# 3. Install
pip install -r requirements.txt

# 4. (Optional) Add NewsAPI key for live data
cp .env.example .env
# Edit .env → NEWSAPI_KEY=your_key_here
# Free key at https://newsapi.org

# 5. Run
python app.py
# → http://localhost:5000
```

> Works **without** a NewsAPI key using realistic mock data.

---

## 🔌 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/analyse?q=Apple` | Full sentiment analysis for a topic |
| GET | `/api/compare?q=Apple,Tesla,Google` | Side-by-side comparison (up to 4) |

### Example Response
```json
{
  "query": "Apple",
  "summary": {
    "total": 12,
    "avg_score": 0.214,
    "overall": "positive",
    "positive": 7,
    "negative": 3,
    "neutral": 2,
    "top_keywords": ["earnings", "iphone", "revenue", "growth"],
    "trend": [{"date": "2026-05-29", "avg_score": 0.31}]
  },
  "articles": [...]
}
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| NLP Engine | Custom financial lexicon, rule-based |
| News Data | NewsAPI.org (free tier) |
| Backend | Flask, Flask-CORS |
| Frontend | Chart.js, Vanilla JS |
| Deployment | Gunicorn |

---

## 🔮 Future Improvements

- [ ] Swap lexicon for FinBERT transformer model
- [ ] Twitter/X feed sentiment integration
- [ ] Email alerts when sentiment crosses threshold
- [ ] Historical sentiment database (SQLite)
- [ ] Multi-topic comparison view
- [ ] Deploy to Render

---

## 📄 License

MIT © Lakshay Atreja
