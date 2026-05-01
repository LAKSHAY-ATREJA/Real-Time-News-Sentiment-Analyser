import os
import logging

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from sentiment import analyse_topic

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/analyse")
def analyse():
    """
    GET /api/analyse?q=<topic>

    Run sentiment analysis on recent news for the given topic.
    Returns a JSON object with keys: query, articles, summary.
    """
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Query parameter 'q' is required."}), 400

    logger.info("analyse request  query=%r", query)
    try:
        result = analyse_topic(query)
        return jsonify(result)
    except ValueError as exc:
        logger.warning("analyse bad request  query=%r  error=%s", query, exc)
        return jsonify({"error": str(exc)}), 400
    except RuntimeError as exc:
        logger.error("analyse runtime error  query=%r  error=%s", query, exc)
        return jsonify({"error": str(exc)}), 502
    except Exception as exc:
        logger.exception("analyse unexpected error  query=%r", query)
        return jsonify({"error": "An unexpected error occurred."}), 500


@app.route("/api/compare")
def compare():
    """
    GET /api/compare?q=Apple,Tesla,Google

    Run sentiment analysis on up to 4 comma-separated topics and return a
    side-by-side summary list.
    """
    raw = request.args.get("q", "")
    queries = [q.strip() for q in raw.split(",") if q.strip()]

    if len(queries) < 2:
        return jsonify({"error": "Provide at least 2 comma-separated topics."}), 400

    queries = queries[:4]
    logger.info("compare request  queries=%r", queries)

    results = []
    errors = []
    for q in queries:
        try:
            data = analyse_topic(q)
            results.append({"query": q, **data["summary"]})
        except (ValueError, RuntimeError) as exc:
            errors.append({"query": q, "error": str(exc)})
        except Exception as exc:
            logger.exception("compare unexpected error  query=%r", q)
            errors.append({"query": q, "error": "Unexpected error."})

    response = {"results": results}
    if errors:
        response["errors"] = errors

    return jsonify(response)


@app.route("/api/health")
def health():
    """Simple liveness probe used by Render and Railway."""
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    logger.info("Starting server on port %d  debug=%s", port, debug)
    app.run(debug=debug, host="0.0.0.0", port=port)
