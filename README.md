# Factory_GPT
An interactive secure chatbot which can answer internal data questions efficiently and can also give analytics about the data provided.
Nokia GPT is an AI-powered intelligent assistant designed to optimize industrial operations, automate quality checks, and enhance predictive maintenance in a smart manufacturing environment.
Developed for the Hackathon, this project integrates Generative AI, Computer Vision, and IoT data insights to bring intelligence to factory floors.

# Overview

Nokia GPT acts as a digital co-pilot for manufacturing engineers and operators.
It can:

Analyze production line data and generate actionable insights

Perform quality inspection using vision-based detection models

Predict potential machine failures using predictive maintenance analytics

Respond to natural language queries using GPT-powered dialogue

Integrate seamlessly with existing factory dashboards or robotic systems

# Tech Stack
Category	        Tools / Technologies
Frontend	        HTML, CSS, JavaScript, Flask / Streamlit
Backend	Python    (Flask / FastAPI)
AI/ML Models	    OpenAI GPT (via Azure / API), Vision Inspection Model (YOLOv8 / custom CNN)
Data Processing	  Pandas, NumPy, Power BI (for visualization)
IoT Integration	  REST-based communication
Deployment	      GitHub Pages


# Features

1. High Accuracy Insights – Delivers precise results in vision inspection, anomaly detection, and predictive maintenance using advanced AI models.

2. Real-Time Data Processing – Monitors live factory metrics, generating alerts and recommendations instantly.

3. Multi-Modal Intelligence – Combines computer vision, sensor data, and natural language understanding to make smarter decisions.

4. Scalable Architecture – Can easily be deployed across multiple production lines or plants without major reconfiguration.

5. Seamless Integration – Connects smoothly with existing dashboards, IoT devices, and factory management systems (MES / ERP).

6. User-Friendly Interface – Simple, intuitive web dashboard and chat interface for engineers, operators, and managers.

7. Customizable Responses – Fine-tuned GPT model allows plant-specific terminology and contextual understanding.


# Hackathon Impact

“Empowering smarter manufacturing with AI-driven insights.”

Nokia GPT showcases how AI can seamlessly combine data, vision, and natural language understanding to drive efficiency, reduce downtime, and enable human–machine collaboration in industrial environments.


# How to Run Locally
1️⃣ Clone the Repository
git clone https://github.com/<your-username>/File_name.git

2️⃣ Install Dependencies
pip install -r requirements.txt

3️⃣ Add Environment Variables

Create a .env file in the root directory:


# AZURE Credentials
AZURE_OPENAI_ENDPOINT="your_azure_endpoint_here"
AZURE_OPENAI_KEY="your_api_key_here"
AZURE_OPENAI_API_VERSION= "Version_details"
AZURE_OPENAI_CHAT_DEPLOYMENT= Deployment_name
AZURE_OPENAI_EMBED_DEPLOYMENT= Deployment_name
# SQL Database Credentials
DB_SERVER="your_server_name"
DB_DATABASE="your_DB_name"
DB_UID="DB_user_ID"
DB_PWD="DB_password"


4️⃣ Run the App
python app.py
