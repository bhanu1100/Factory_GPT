from flask import Flask, render_template, request, jsonify, redirect
import webbrowser
import threading
import time
import os
from dotenv import load_dotenv

# -------------------------------------------------------
# 🤖 Factory GPT integration
# -------------------------------------------------------
from factory_gpt import FactoryGPT

# -------------------------------------------------------
# 📊 Power BI AI Insights integration
# -------------------------------------------------------
try:
    from powerbi_insights import powerbi_bp
    POWERBI_AVAILABLE = True
except ImportError:
    POWERBI_AVAILABLE = False
    print("⚠️ Power BI insights module not found. Skipping Power BI routes.")

# -------------------------------------------------------
# ⚙️ Environment setup
# -------------------------------------------------------
load_dotenv()

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.getenv("SECRET_KEY", os.urandom(24).hex())

BASE_PATH = "/nokia-ai"

# -------------------------------------------------------
# 🧠 Global GPT Agent
# -------------------------------------------------------
agent = None
agent_initialized = False
agent_error = None


def init_agent():
    """Initialize Factory GPT asynchronously"""
    global agent, agent_initialized, agent_error
    try:
        print("🤖 Initializing Factory GPT Agent...")
        agent = FactoryGPT()
        agent_initialized = True
        print("✅ Factory GPT initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize Factory GPT: {str(e)}")
        agent_error = str(e)
        agent = None
        agent_initialized = True  # even if failed


# -------------------------------------------------------
# 🌐 Routes
# -------------------------------------------------------

@app.route(f"{BASE_PATH}/")
def home():
    """Main homepage"""
    return render_template("home.html")


@app.route(f"{BASE_PATH}/factory-gpt")
def factory_gpt():
    """Factory GPT chat interface"""
    return render_template("chatgpt.html")


@app.route(f"{BASE_PATH}/lead-time-analytics")
def lead_time_analytics():
    """Redirect to Power BI lead time report"""
    return redirect(
        "https://app.powerbi.com/groups/me/reports/e862eff0-61e0-4b2b-855c-ef41ce32ef22/ReportSection5d4fdc396f845009e47f?experience=power-bi"
    )


# -------------------------------------------------------
# 📊 Register Power BI AI Blueprint (if available)
# -------------------------------------------------------
if POWERBI_AVAILABLE:
    app.register_blueprint(powerbi_bp, url_prefix=f"{BASE_PATH}/powerbi-insights")
    print("✅ Power BI AI Insights module loaded successfully.")
else:
    print("⚠️ Power BI AI Insights module not found — skipping.")


# -------------------------------------------------------
# 🧩 Factory GPT Endpoint
# -------------------------------------------------------
@app.route(f"{BASE_PATH}/ask", methods=["POST"])
def ask():
    """Handle Factory GPT questions and graph generation"""
    global agent, agent_initialized, agent_error

    try:
        # Initialization check
        if not agent_initialized:
            return jsonify({
                "answer": "🤖 Factory GPT is still initializing... Please wait a moment.",
                "graph": None,
                "status": "initializing"
            })

        if agent is None:
            return jsonify({
                "answer": f"❌ Factory GPT failed to initialize. Error: {agent_error or 'Unknown error'}",
                "graph": None,
                "status": "error"
            })

        # Parse question
        data = request.get_json()
        question = data.get("question", "").strip()

        if not question:
            return jsonify({
                "answer": "Please enter a valid question.",
                "graph": None,
                "status": "error"
            })

        print(f"📝 Processing question: {question}")
        result = agent.ask(question)

        # Handle dict result (text + optional graph)
        if isinstance(result, dict):
            answer_text = result.get("text", "")
            graph_url = result.get("graph", None)
        else:
            answer_text = result
            graph_url = None

        return jsonify({
            "answer": answer_text,
            "graph": graph_url,
            "status": "success"
        })

    except Exception as e:
        print(f"❌ Error in /ask: {e}")
        return jsonify({
            "answer": f"⚠️ Internal error: {e}",
            "graph": None,
            "status": "error"
        })


# -------------------------------------------------------
# 🧠 Agent Status Checker
# -------------------------------------------------------
@app.route(f"{BASE_PATH}/agent-status", methods=["GET"])
def agent_status():
    """Check if GPT agent is ready"""
    global agent, agent_initialized, agent_error

    if not agent_initialized:
        return jsonify({"status": "initializing"})
    elif agent is None:
        return jsonify({"status": "error", "message": agent_error})
    else:
        return jsonify({"status": "ready"})


# -------------------------------------------------------
# 🧭 Auto-open browser
# -------------------------------------------------------
def open_browser():
    time.sleep(3)
    webbrowser.open(f"http://localhost:5050{BASE_PATH}/")


# -------------------------------------------------------
# 🚀 Run Flask App
# -------------------------------------------------------
if __name__ == "__main__":
    print("🚀 Starting Nokia AI Portal...")

    # Initialize GPT in background thread
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Thread(target=init_agent, daemon=True).start()
        threading.Thread(target=open_browser, daemon=True).start()

    app.run(debug=True, host="0.0.0.0", port=5050)
