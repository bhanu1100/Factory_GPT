import os
import base64
import tempfile
import uuid
import markdown
from flask import Blueprint, request, jsonify, session, render_template
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

# Create Blueprint
powerbi_bp = Blueprint('powerbi', __name__, template_folder='templates')

# --- AZURE OPENAI SETUP ---
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2024-02-15-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)
AZURE_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")

# --- PROMPT ---
INITIAL_PROMPT = (
    "You are an expert Power BI analyst. A user has uploaded the following report visual. "
    "Provide a concise, high-level summary to start the conversation. "
    "Identify the main KPIs, summarize the key trend, and suggest one business action. "
    "Keep it brief and invite the user to ask follow-up questions."
)

# --- AI FUNCTION ---
def get_ai_chat_response(image_path, chat_history):
    try:
        with open(image_path, "rb") as img_file:
            image_base64 = base64.b64encode(img_file.read()).decode("utf-8")
    except FileNotFoundError:
        return "Error: The file for this session was not found. It may have been cleared from the server's temporary cache. Please upload the file again."

    messages = [
        {"role": "user", "content": [
            {"type": "text", "text": INITIAL_PROMPT}, 
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
        ]}
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

# --- ROUTES ---
@powerbi_bp.route('/')
def powerbi_home():
    """Main Power BI insights page"""
    return render_template('pbi.html')

@powerbi_bp.route('/upload', methods=['POST'])
def upload():
    if 'report_file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['report_file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    temp_dir = tempfile.gettempdir()
    unique_filename = f"{str(uuid.uuid4())}_{file.filename}"
    image_path = os.path.join(temp_dir, unique_filename)
    file.save(image_path)
    
    # Store in session with a prefix to avoid conflicts
    session['powerbi_image_path'] = image_path
    session['powerbi_chat_history'] = []

    initial_summary_md = get_ai_chat_response(image_path, [])
    session['powerbi_chat_history'].append({"role": "assistant", "content": initial_summary_md})
    
    initial_summary_html = markdown.markdown(initial_summary_md, extensions=['fenced_code', 'tables'])
    
    return jsonify({"initial_summary": initial_summary_html})

@powerbi_bp.route('/ask', methods=['POST'])
def ask():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    user_question = request.json.get('question')
    if not user_question:
        return jsonify({"error": "No question provided"}), 400
    
    if 'powerbi_image_path' not in session or 'powerbi_chat_history' not in session:
        return jsonify({"error": "Session expired. Please upload a file again."}), 400
    
    session['powerbi_chat_history'].append({"role": "user", "content": user_question})
    ai_response_md = get_ai_chat_response(session['powerbi_image_path'], session['powerbi_chat_history'])
    session['powerbi_chat_history'].append({"role": "assistant", "content": ai_response_md})
    
    ai_response_html = markdown.markdown(ai_response_md, extensions=['fenced_code', 'tables'])
    
    return jsonify({"answer": ai_response_html})

@powerbi_bp.route('/clear', methods=['POST'])
def clear_session():
    """Clear Power BI session data"""
    session.pop('powerbi_image_path', None)
    session.pop('powerbi_chat_history', None)
    return jsonify({"success": True})