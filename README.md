# Real-Time News Sentiment Analyser

A full-stack NLP application that fetches live news headlines for any stock, company, or topic and performs sentiment analysis. The interactive dashboard shows per-article sentiment scores, an overall signal, a trend chart across dates, a keyword summary, and a positive/negative/neutral distribution. It works without any API key using realistic mock data.

## How the sentiment engine works

The sentiment module uses a domain-specific financial lexicon rather than a heavy transformer model, so it runs with no GPU and no large model download:

1. Clean the headline and description (remove URLs, punctuation, lowercase)
2. Tokenise into sentences
3. Score each sentence against POSITIVE_WORDS and NEGATIVE_WORDS lexicons, applying negation detection (not, never, no) and intensity boosting (very, extremely, significantly)
4. Average sentence scores and normalise to the range [-1, +1]
5. Assign label: positive (score > 0.15), negative (score < -0.15), neutral otherwise

## Features

- Real-time news via NewsAPI (free tier) with a mock-data fallback when no key is provided
- Per-article sentiment score and label
- Aggregate signal, score distribution, trend over time, and top keywords
- REST API at `/api/analyse` and `/api/compare`
- Interactive Chart.js dashboard (line chart, doughnut, keyword display)

## Requirements

- Python 3.10 or later

## Local setup

```bash
git clone https://github.com/LAKSHAY-ATREJA/Real-Time-News-Sentiment-Analyser.git
cd Real-Time-News-Sentiment-Analyser

python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Optional: set your NewsAPI key for live headlines
cp .env.example .env
# Edit .env and set NEWSAPI_KEY=your_key_here

python app.py
```

Open http://localhost:5000 in your browser.

The app works immediately without a NewsAPI key — mock articles are generated automatically to demonstrate the full dashboard.

## Environment variables

| Variable    | Required | Description                                      |
|-------------|----------|--------------------------------------------------|
| NEWSAPI_KEY | No       | NewsAPI key from newsapi.org for live headlines  |

## API reference

| Method | Endpoint                          | Description                              |
|--------|-----------------------------------|------------------------------------------|
| GET    | /api/analyse?q=Apple              | Full sentiment analysis for a topic      |
| GET    | /api/compare?q=Apple,Tesla,Google | Side-by-side comparison (up to 4 topics) |

Example response for /api/analyse:

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
    "trend": [{"date": "2026-06-20", "avg_score": 0.31}]
  },
  "articles": [...]
}
```

## Project structure

```
app.py              Flask server and REST endpoints
sentiment.py        Lexicon-based NLP engine and NewsAPI fetcher
templates/
    index.html      Interactive dashboard (Chart.js, Vanilla JS)
requirements.txt    Python dependencies
.env.example        Template for environment variables
```

## Deployment to Render (free tier)

1. Push this repository to GitHub
2. Create a new Web Service on https://render.com
3. Set the build command to `pip install -r requirements.txt`
4. Set the start command to `gunicorn app:app`
5. Add the NEWSAPI_KEY environment variable in the Render dashboard
6. Deploy — the service is live in a few minutes

## Tech stack

| Component   | Technology                     |
|-------------|--------------------------------|
| NLP engine  | Custom financial lexicon       |
| News data   | NewsAPI.org (free tier)        |
| Backend     | Flask, Flask-CORS, Gunicorn    |
| Frontend    | Chart.js, Vanilla JS           |
| Language    | Python 3.10+                   |

## License

MIT. Built by Lakshay Atreja.
