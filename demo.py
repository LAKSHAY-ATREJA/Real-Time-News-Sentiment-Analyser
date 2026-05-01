"""
demo.py — standalone demonstration of the Real-Time News Sentiment Analyser.

This script runs the full analysis pipeline without starting the web server.
It uses mock news articles when no NEWSAPI_KEY is set, so it works out-of-the-box
after installing the project dependencies:

    pip install -r requirements.txt
    python demo.py

To use real headlines instead of mock data, create a .env file with your
NewsAPI key (see .env.example) before running this script.
"""

import json
import os
import sys

# Optional: load a .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from sentiment import analyse_topic, analyse_text


# ── Helpers ───────────────────────────────────────────────────────────────────

def separator(char="-", width=60):
    print(char * width)


def print_header(text):
    separator("=")
    print(f"  {text}")
    separator("=")


def label_colour(label):
    """Return a (prefix, reset) pair for coloured terminal output.
    Returns empty strings when stdout is not a tty (e.g. pipe or redirect)."""
    if not sys.stdout.isatty():
        return "", ""
    colours = {"positive": "\033[32m", "negative": "\033[31m", "neutral": "\033[33m"}
    return colours.get(label, ""), "\033[0m"


# ── Demo 1: single text analysis ─────────────────────────────────────────────

def demo_single_text():
    print_header("Demo 1: Single-text sentiment analysis")

    samples = [
        "Apple reported record quarterly earnings, beating analyst expectations by 12%. Revenue surged on strong iPhone demand.",
        "The company faces serious regulatory scrutiny and announced layoffs affecting 8% of its workforce amid rising costs.",
        "Analysts remain divided on the stock's outlook heading into the next fiscal year. The company maintained guidance.",
    ]

    for text in samples:
        result = analyse_text(text)
        pre, reset = label_colour(result["label"])
        print(f"\nText   : {text[:80]}{'...' if len(text) > 80 else ''}")
        print(f"Score  : {result['score']:+.3f}  |  Label: {pre}{result['label'].upper()}{reset}  |  Confidence: {result['confidence']:.1f}%")
        if result["keywords"]:
            print(f"Keywords: {', '.join(result['keywords'][:5])}")

    print()


# ── Demo 2: full topic analysis ───────────────────────────────────────────────

def demo_topic(topic):
    print_header(f"Demo 2: Full topic analysis — \"{topic}\"")

    key_set = bool(os.getenv("NEWSAPI_KEY", "").strip())
    if key_set:
        print("  NEWSAPI_KEY is set — fetching live headlines from NewsAPI.")
    else:
        print("  No NEWSAPI_KEY found — using built-in mock articles.")
    print()

    result = analyse_topic(topic)
    summary = result["summary"]
    articles = result["articles"]

    pre, reset = label_colour(summary["overall"])

    print(f"Query         : {result['query']}")
    print(f"Articles      : {summary['total']}")
    print(f"Average score : {summary['avg_score']:+.3f}")
    print(f"Overall       : {pre}{summary['overall'].upper()}{reset}")
    print(f"Distribution  : {summary['positive']} positive / {summary['neutral']} neutral / {summary['negative']} negative")
    if summary["top_keywords"]:
        print(f"Top keywords  : {', '.join(summary['top_keywords'][:8])}")

    separator()
    print(f"{'Date':<12}  {'Score':>7}  {'Label':<10}  Title")
    separator()

    for a in articles:
        pre, reset = label_colour(a["label"])
        title = a["title"][:50] + ("..." if len(a["title"]) > 50 else "")
        print(f"{a['published']:<12}  {a['score']:>+7.3f}  {pre}{a['label']:<10}{reset}  {title}")

    separator()
    print()

    print("Trend (average sentiment score per day):")
    for t in summary["trend"]:
        bar_len = int((t["avg_score"] + 1) * 15)  # map [-1,1] to [0,30]
        bar = "#" * max(bar_len, 1)
        print(f"  {t['date']}  {t['avg_score']:+.3f}  {bar}")

    print()


# ── Demo 3: comparison of topics ─────────────────────────────────────────────

def demo_compare(topics):
    print_header(f"Demo 3: Side-by-side comparison — {', '.join(topics)}")

    rows = []
    for t in topics:
        result = analyse_topic(t)
        s = result["summary"]
        rows.append({
            "query":    t,
            "score":    s["avg_score"],
            "overall":  s["overall"],
            "positive": s["positive"],
            "negative": s["negative"],
            "neutral":  s["neutral"],
            "total":    s["total"],
        })

    # Sort by score descending
    rows.sort(key=lambda r: r["score"], reverse=True)

    header = f"{'Topic':<20}  {'Score':>7}  {'Overall':<10}  {'Pos':>4}  {'Neu':>4}  {'Neg':>4}  {'Total':>5}"
    separator()
    print(header)
    separator()
    for row in rows:
        pre, reset = label_colour(row["overall"])
        print(
            f"{row['query']:<20}  {row['score']:>+7.3f}  "
            f"{pre}{row['overall']:<10}{reset}  "
            f"{row['positive']:>4}  {row['neutral']:>4}  {row['negative']:>4}  {row['total']:>5}"
        )
    separator()
    print()


# ── Demo 4: raw JSON output ───────────────────────────────────────────────────

def demo_json_output(topic):
    print_header(f"Demo 4: Raw JSON summary output for \"{topic}\"")
    result = analyse_topic(topic)
    # Print only the summary block to keep output concise
    print(json.dumps(result["summary"], indent=2))
    print()


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    demo_single_text()
    demo_topic("Tesla")
    demo_compare(["Apple", "Tesla", "Bitcoin", "Google"])
    demo_json_output("Apple")

    print("=" * 60)
    print("  Demo complete.")
    print("  Run  python app.py  to start the interactive web dashboard.")
    print("=" * 60)
