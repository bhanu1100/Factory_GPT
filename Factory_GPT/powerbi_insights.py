import os
import base64
import tempfile
import uuid
import markdown
from flask import Blueprint, request, jsonify, session, render_template
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

powerbi_bp = Blueprint(
    "powerbi_bp",
    __name__,
    template_folder="templates",  # points to Factory_GPT/templates
    static_folder="static"        # points to Factory_GPT/static
)

# --- Azure OpenAI Setup ---
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2024-02-15-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)
AZURE_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")

INITIAL_PROMPT = (
    "You are an expert Power BI analyst. A user has uploaded a Power BI report visual. "
    "Provide a concise, high-level summary identifying the main KPIs, key trends, and one actionable insight. "
    "Keep it brief, professional, and invite follow-up questions."
)


# -----------------------------
# 🧠 Helper — Send image + chat to Azure OpenAI
# -----------------------------
def get_ai_chat_response(image_path, chat_history):
    """Send uploaded visual and chat history to GPT."""
    try:
        with open(image_path, "rb") as img_file:
            image_base64 = base64.b64encode(img_file.read()).decode("utf-8")
    except FileNotFoundError:
        return "⚠️ File not found. Please upload again."

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": INITIAL_PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
            ]
        }
    ] + chat_history

    try:
        response = client.chat.completions.create(
            model=AZURE_DEPLOYMENT_NAME,
            messages=messages,
            max_tokens=2048,
            timeout=60.0
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI model error: {e}"


# -----------------------------
# 🌐 ROUTES
# -----------------------------
@powerbi_bp.route("/", methods=["GET"])
def home():
    """Render your Nokia Power BI HTML frontend."""
    session.clear()
    return render_template("pbi.html")  # ✅ your actual file name


@powerbi_bp.route("/upload", methods=["POST"])
def upload():
    """Handle Power BI visual upload."""
    if "report_file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["report_file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    temp_dir = tempfile.gettempdir()
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    image_path = os.path.join(temp_dir, unique_filename)
    file.save(image_path)

    session["image_path"] = image_path
    session["chat_history"] = []

    initial_summary_md = get_ai_chat_response(image_path, [])
    session["chat_history"].append({"role": "assistant", "content": initial_summary_md})

    initial_summary_html = markdown.markdown(initial_summary_md, extensions=["fenced_code", "tables"])
    return jsonify({"initial_summary": initial_summary_html})


@powerbi_bp.route("/ask", methods=["POST"])
def ask():
    """Handle Power BI chat follow-ups."""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    user_question = request.json.get("question")
    if not user_question:
        return jsonify({"error": "No question provided"}), 400

    if "image_path" not in session or "chat_history" not in session:
        return jsonify({"error": "Session expired. Please re-upload the report."}), 400

    session["chat_history"].append({"role": "user", "content": user_question})
    ai_response_md = get_ai_chat_response(session["image_path"], session["chat_history"])
    session["chat_history"].append({"role": "assistant", "content": ai_response_md})

    ai_response_html = markdown.markdown(ai_response_md, extensions=["fenced_code", "tables"])
    return jsonify({"answer": ai_response_html})
