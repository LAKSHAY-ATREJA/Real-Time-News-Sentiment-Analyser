# Real-Time News Sentiment Analyser

A web application that fetches recent news headlines for any stock, company, or topic and runs sentiment analysis on them. The dashboard displays a per-article sentiment score, an aggregate signal, a distribution breakdown, a trend chart over time, and the most prominent keywords extracted from the headlines.

The application does not require a paid model or a GPU. It uses a domain-specific financial lexicon to score headlines, so it installs in seconds and runs anywhere Python runs.

---

## How it works

The sentiment engine in `sentiment.py` runs a five-step pipeline on each article:

1. Clean the text: strip URLs, remove punctuation, lowercase.
2. Split into sentences on `.`, `!`, and `?`.
3. Score each sentence against a positive and a negative word list, with negation handling (`not`, `never`, `no`) and intensity boosting (`very`, `extremely`, `significantly`).
4. Average the sentence scores and normalise to the range `[-1, +1]`.
5. Assign a label: positive (score above 0.15), negative (score below -0.15), or neutral otherwise.

News is fetched from NewsAPI. If no API key is configured, the application generates realistic mock articles so the dashboard is fully usable during local development and evaluation.

---

## Features

- Per-article sentiment score, label, and confidence estimate
- Aggregate sentiment signal with positive / neutral / negative breakdown
- Sentiment trend chart grouped by publication date
- Top keyword extraction across all articles
- REST API at `/api/analyse` and `/api/compare`
- Mock data fallback when no NewsAPI key is present
- Interactive dashboard built with Chart.js and plain JavaScript
- Deployable to Render, Railway, or any WSGI host with a single start command

---

## Requirements

- Python 3.10 or later
- A free NewsAPI key from newsapi.org (optional; mock data is used otherwise)

---

## Installation

```bash
git clone https://github.com/LAKSHAY-ATREJA/Real-Time-News-Sentiment-Analyser.git
cd Real-Time-News-Sentiment-Analyser

python3 -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate

pip install -r requirements.txt
```

---

## Running locally

```bash
python app.py
```

Open `http://localhost:5000` in a browser. The application starts on port 5000 by default. You can change the port by setting the `PORT` environment variable.

To enable live news instead of mock data, create a `.env` file first (see the Environment variables section below).

---

## Running the demo

The `demo.py` script exercises the full pipeline from the command line without starting a web server. It is useful for quickly verifying the installation or understanding the API.

```bash
python demo.py
```

The demo runs four sections:

1. Single-text analysis on three hand-written sentences
2. Full topic analysis for "Tesla", showing per-article scores and a trend chart in ASCII
3. Side-by-side comparison of Apple, Tesla, Bitcoin, and Google
4. Raw JSON summary output for "Apple"

When no `NEWSAPI_KEY` is set, the demo uses the built-in mock articles. Set the key in `.env` beforehand to see live headline results.

---

## Environment variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

| Variable       | Required | Description                                                                          |
|----------------|----------|--------------------------------------------------------------------------------------|
| `NEWSAPI_KEY`  | No       | API key from newsapi.org. Without it, the app uses mock data instead of live news.  |
| `PORT`         | No       | Port the development server listens on. Defaults to 5000.                            |
| `FLASK_DEBUG`  | No       | Set to `true` to enable Flask debug mode. Never use `true` in production.            |

To get a free NewsAPI key:
1. Go to https://newsapi.org and create an account.
2. Copy the key shown on your account dashboard.
3. Add it to your `.env` file as `NEWSAPI_KEY=your_key_here`.

The free tier allows 100 requests per day and returns articles from the past 30 days.

---

## API reference

### GET /api/analyse

Runs sentiment analysis on recent news for a single topic.

```
GET /api/analyse?q=Apple
```

Response:

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
    "top_keywords": ["earnings", "iphone", "revenue", "growth", "record"],
    "trend": [
      {"date": "2026-06-20", "avg_score": 0.31},
      {"date": "2026-06-21", "avg_score": 0.18}
    ]
  },
  "articles": [
    {
      "title": "Apple reports record quarterly earnings",
      "description": "Revenue beat analyst expectations by 12%.",
      "source": "Reuters",
      "url": "https://example.com/article",
      "published": "2026-06-21",
      "score": 0.42,
      "label": "positive",
      "confidence": 82.0,
      "keywords": ["record", "earnings", "revenue"],
      "sentences": 3
    }
  ]
}
```

### GET /api/compare

Runs sentiment analysis on up to four comma-separated topics and returns a summary for each.

```
GET /api/compare?q=Apple,Tesla,Google
```

Response:

```json
{
  "results": [
    {"query": "Apple",  "avg_score": 0.214, "overall": "positive", "positive": 7, ...},
    {"query": "Tesla",  "avg_score": -0.08, "overall": "neutral",  "positive": 4, ...},
    {"query": "Google", "avg_score": 0.11,  "overall": "positive", "positive": 5, ...}
  ]
}
```

### GET /api/health

Returns `{"status": "ok"}`. Used by Render and Railway as a liveness probe.

---

## Project structure

```
app.py              Flask application with REST endpoints
sentiment.py        Lexicon-based NLP engine, news fetcher, and mock data
demo.py             Standalone command-line demonstration
templates/
    index.html      Interactive Chart.js dashboard
requirements.txt    Python dependencies
render.yaml         Render deployment configuration
Procfile            Process file for Railway and Heroku
.env.example        Template for environment variables
```

---

## Deployment

### Render (recommended for free hosting)

1. Push this repository to GitHub.
2. Go to https://render.com and create a new Web Service.
3. Connect the repository.
4. Set the build command to `pip install -r requirements.txt`.
5. Set the start command to `gunicorn app:app`.
6. Add `NEWSAPI_KEY` as an environment variable in the Render dashboard.
7. Deploy. The service is live within a few minutes.

Alternatively, Render will detect `render.yaml` in the repository root and pre-fill most of these settings automatically.

### Railway

1. Push this repository to GitHub.
2. Create a new project on https://railway.app and import the repository.
3. Railway detects the `Procfile` and sets the start command automatically.
4. Add `NEWSAPI_KEY` in the environment variables panel.
5. Deploy.

### Any WSGI server

```bash
gunicorn app:app --bind 0.0.0.0:8000 --workers 2
```

---

## Tech stack

| Layer       | Technology                          |
|-------------|-------------------------------------|
| NLP engine  | Custom financial lexicon (no model) |
| News data   | NewsAPI.org free tier               |
| Backend     | Flask, Flask-CORS, Gunicorn         |
| Frontend    | Chart.js, Vanilla JavaScript        |
| Language    | Python 3.10+                        |

---

## License

MIT. Built by Lakshay Atreja.
