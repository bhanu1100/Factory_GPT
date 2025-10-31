from flask import Flask, render_template, request, jsonify, redirect, url_for
import webbrowser
import threading
import time
import os
from dotenv import load_dotenv

# Imports for Factory GPT integration
from factory_gpt import FactoryGPT

# Import Power BI blueprint (comment out if not available)
try:
    from powerbi_insights import powerbi_bp
    POWERBI_AVAILABLE = True
except ImportError:
    POWERBI_AVAILABLE = False
    print("⚠️ Power BI insights module not found. Skipping Power BI routes.")

# Load environment variables
load_dotenv()

app = Flask(__name__, template_folder='templates')
app.secret_key = os.getenv("SECRET_KEY", os.urandom(24).hex())

BASE_PATH = "/nokia-ai"

# Global agent instance for Factory GPT
agent = None
agent_initialized = False
agent_error = None

def init_agent():
    """Initialize the SQL agent in background"""
    global agent, agent_initialized, agent_error
    try:
        print("🤖 Initializing Factory GPT Agent...")
        agent = FactoryGPT()
        agent_initialized = True
        print("✅ Agent initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {str(e)}")
        agent_error = str(e)
        agent = None
        agent_initialized = True  # Mark as done even if failed

# ------------------ Routes ------------------

@app.route(f"{BASE_PATH}/")
def home():
    return render_template("home.html")

@app.route(f"{BASE_PATH}/factory-gpt")
def factory_gpt():
    return render_template("chatgpt.html")

@app.route(f"{BASE_PATH}/lead-time-analytics")
def lead_time_analytics():
    return redirect("https://app.powerbi.com/groups/325598ff-043d-4c5c-b5ad-bbb336ab596d/reports/98a4cc9e-347b-4820-a02b-76d2e141a749/ReportSectiond652b3abd0f8b7670df0?experience=power-bi")

# Register Power BI blueprint (if available)
if POWERBI_AVAILABLE:
    app.register_blueprint(powerbi_bp, url_prefix=f"{BASE_PATH}/powerbi-insights")

@app.route(f"{BASE_PATH}/ask", methods=["POST"])
def ask():
    """Handle Factory GPT questions"""
    global agent, agent_initialized, agent_error
    
    try:
        # Check if agent is still initializing
        if not agent_initialized:
            return jsonify({
                "answer": "🤖 Factory GPT is still initializing... Please wait a moment and try again.",
                "status": "initializing"
            })
        
        # Check if agent failed to initialize
        if agent is None:
            return jsonify({
                "answer": f"❌ Factory GPT failed to initialize. Error: {agent_error or 'Unknown error'}. Please check your database connection and API keys.",
                "status": "error"
            })
        
        # Get question from request
        data = request.get_json()
        question = data.get("question", "").strip()
        
        if not question:
            return jsonify({
                "answer": "Please enter a question.",
                "status": "error"
            })
        
        # Process the question
        print(f"📝 Processing question: {question}")
        answer = agent.ask(question)
        
        return jsonify({
            "answer": answer,
            "status": "success"
        })
        
    except Exception as e:
        print(f"❌ Error in /ask endpoint: {str(e)}")
        return jsonify({
            "answer": f"Sorry, I encountered an error: {str(e)}",
            "status": "error"
        })

@app.route(f"{BASE_PATH}/agent-status", methods=["GET"])
def agent_status():
    """Check if agent is ready"""
    global agent, agent_initialized, agent_error
    
    if not agent_initialized:
        return jsonify({"status": "initializing"})
    elif agent is None:
        return jsonify({"status": "error", "message": agent_error})
    else:
        return jsonify({"status": "ready"})

# ------------------ Auto-open browser ------------------

def open_browser():
    time.sleep(3)
    webbrowser.open(f"http://localhost:5050{BASE_PATH}/")

if __name__ == "__main__":
    print("🚀 Starting Nokia AI Portal...")
    
    # Initialize agent in background thread (only in main process)
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        agent_thread = threading.Thread(target=init_agent, daemon=True)
        agent_thread.start()
        
        # Open browser
        threading.Thread(target=open_browser, daemon=True).start()
    
    app.run(debug=True, host="0.0.0.0", port=5050)