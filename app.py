from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from sentiment import analyse_topic

app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/analyse")
def analyse():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Query required"}), 400
    try:
        return jsonify(analyse_topic(query))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/compare")
def compare():
    queries = [q.strip() for q in request.args.get("q", "").split(",") if q.strip()]
    if len(queries) < 2:
        return jsonify({"error": "Provide at least 2 comma-separated topics"}), 400
    try:
        results = [{"query": q, **analyse_topic(q)["summary"]} for q in queries[:4]]
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
