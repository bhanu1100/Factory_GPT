import os
import re
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from openai import AzureOpenAI
import difflib

# -------------------------------------------------------
# 1️⃣ Load environment and model
# -------------------------------------------------------
load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION")
)
chat_deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")

# -------------------------------------------------------
# 2️⃣ Load dataset
# -------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Try reading dataset path from .env, else use default local path
DATA_PATH = os.getenv(
    "DATASET_PATH",
    os.path.join(BASE_DIR, "MQTT_Dataset_Dummy_Enhanced_NoOperatorEnv.csv")
)

print(f"📦 Loading dataset from: {DATA_PATH}")

try:
    df = pd.read_csv(DATA_PATH)
    if df.empty:
        print("⚠️ Warning: Dataset is empty. Check the CSV file content.")
    else:
        print(f"✅ Dataset loaded successfully with {len(df)} rows and {len(df.columns)} columns.")
except FileNotFoundError:
    print(f"❌ ERROR: Dataset file not found at {DATA_PATH}")
    raise
except Exception as e:
    print(f"⚠️ Failed to load dataset: {e}")
    raise


# -------------------------------------------------------
# 3️⃣ Helper utilities
# -------------------------------------------------------
def extract_macline(query: str):
    match = re.search(r"macline[-_ ]?(\d+)", query.lower())
    return f"MACLINE-{match.group(1)}" if match else None

def extract_product(query: str, df_local: pd.DataFrame):
    """Extract product name/version from query."""
    q = query.lower().strip()
    q = re.sub(r"\(.*?\)", "", q).strip()
    products = df_local["Product_Item"].astype(str).unique()
    matches = [p for p in products if p.lower() in q]
    if matches:
        return matches[0]
    close = difflib.get_close_matches(q, [p.lower() for p in products], n=1, cutoff=0.6)
    if close:
        for p in products:
            if p.lower() == close[0]:
                return p
    return None

def detect_followup_reference(q: str):
    ql = q.lower()
    triggers = [
        "same", "that", "it", "this", "previous", "earlier", "last one",
        "same machine", "same line", "that machine", "that one",
        "same product", "that product"
    ]
    return any(t in ql for t in triggers)

def compute_target_achievement(df_local):
    if "Target_Achievement (%)" not in df_local.columns:
        with np.errstate(divide="ignore", invalid="ignore"):
            df_local["Target_Achievement (%)"] = (
                (df_local["Shift_Achieved"] / df_local["Shift_Target"]) * 100
            ).round(2)
    return df_local

# -------------------------------------------------------
# 4️⃣ Graph generator
# -------------------------------------------------------
def generate_graph(df_local, metric="Shift_Efficiency (%)", by="MACHINE_GROUP", product_filter=None):
    """
    Generates and saves a matplotlib graph for selected metrics.
    Returns the saved file path (relative path under static/graphs) on success,
    or None if there was no data to plot.
    """
    df_local = compute_target_achievement(df_local.copy())

    # Prepare folder
    graphs_dir = os.path.join(BASE_DIR, "static", "graphs")
    os.makedirs(graphs_dir, exist_ok=True)

    # Determine filename (metric normalized)
    filename = f"graph_{metric.replace('%', '').replace(' ', '_')}.png"
    save_path = os.path.join(graphs_dir, filename)

    # Build plot data
    if product_filter:
        df_plot = df_local[df_local["Product_Item"].str.contains(product_filter, case=False, na=False)]
        if df_plot.empty:
            # No data for that product
            print(f"⚠️ No data found for product '{product_filter}'.")
            return None
        title = f"{metric} Trend for {product_filter}"
        x = df_plot["MACHINE_GROUP"]
        y = df_plot[metric]
    else:
        # Group by and average
        if by not in df_local.columns:
            print(f"⚠️ Group-by column '{by}' not found in dataset.")
            return None
        df_plot = df_local.groupby(by)[metric].mean().reset_index()
        if df_plot.empty:
            print("⚠️ No data available to plot.")
            return None
        x = df_plot[by]
        y = df_plot[metric]
        title = f"Average {metric} by {by}"

    # Plot
    plt.figure(figsize=(8, 4))
    plt.bar(x, y)
    plt.xlabel(by.replace("_", " ").title())
    plt.ylabel(metric)
    plt.title(title)
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    # Save
    plt.savefig(save_path)
    plt.close()
    print(f"📈 Graph saved as '{save_path}'.")

    # Return web-accessible path with cache-busting timestamp
    web_path = os.path.join("static", "graphs", filename).replace(os.sep, "/")
    web_path_with_ts = f"/{web_path}?t={int(time.time())}"
    return web_path_with_ts

# -------------------------------------------------------
# 5️⃣ Core reasoning engine
# -------------------------------------------------------
def run_pandas_reasoning(question, prev_context=None):
    q = question.lower()
    df_copy = compute_target_achievement(df.copy())
    analysis, reasoning_text = {}, ""

    macline = extract_macline(q)
    product = extract_product(q, df_copy)

    if not macline and prev_context and "last_macline" in prev_context:
        macline = prev_context["last_macline"]
    if not product and prev_context and "last_product" in prev_context:
        product = prev_context["last_product"]

    try:
        # General metrics
        if "average" in q and "efficiency" in q:
            avg_eff = round(df_copy["Shift_Efficiency (%)"].mean(), 2)
            reasoning_text = f"Average efficiency across all lines is {avg_eff}%."
            analysis["Average_Shift_Efficiency"] = avg_eff

        elif "oee" in q and "graph" not in q and "plot" not in q:
            # if they asked for oee graph we handle graph branch; here it's numeric question
            avg_oee = round(df_copy["OEE"].mean(), 2)
            reasoning_text = f"Average Overall Equipment Effectiveness (OEE) is {avg_oee}."
            analysis["Average_OEE"] = avg_oee

        elif "utilization" in q or "idle" in q:
            avg_util = round(df_copy["Utilization_Rate (%)"].mean(), 2)
            reasoning_text = f"Average utilization rate across the plant is {avg_util}%."
            analysis["Average_Utilization_Rate"] = avg_util

        elif "target" in q or "achieved" in q:
            avg_target = round(df_copy["Target_Achievement (%)"].mean(), 2)
            reasoning_text = f"On average, {avg_target}% of production targets are achieved."
            analysis["Average_Target_Achievement"] = avg_target

        elif "maintenance" in q:
            maint_df = df_copy[df_copy["Maintenance_Needed"] == 1]
            lines = maint_df["MACHINE_GROUP"].unique().tolist()
            reasoning_text = (
                f"{len(lines)} lines currently need maintenance: {', '.join(lines)}."
                if len(lines)
                else "All lines are operating normally with no pending maintenance."
            )
            analysis["Maintenance_Lines"] = lines

        elif "downtime" in q or "reason" in q:
            reason = df_copy["Downtime_Reason"].mode()[0]
            reasoning_text = f"The most frequent downtime reason recorded is '{reason}'."
            analysis["Top_Downtime_Reason"] = reason

        # MACLINE insights
        if macline:
            sub = df_copy[df_copy["MACHINE_GROUP"].str.upper() == macline.upper()]
            if len(sub):
                eff = round(sub["Shift_Efficiency (%)"].mean(), 2)
                oee = round(sub["OEE"].mean(), 2)
                maint = int(sub["Maintenance_Needed"].sum())
                reason = sub["Downtime_Reason"].mode()[0] if not sub["Downtime_Reason"].empty else "N/A"
                reasoning_text += (
                    f" For {macline}, efficiency: {eff}%, OEE: {oee}, Maintenance Flags: {maint}. "
                    f"Primary downtime reason: {reason}."
                )
                analysis.update({
                    "MACLINE": macline,
                    "Efficiency": eff,
                    "OEE": oee,
                    "Maintenance_Flags": maint
                })

        # Product insights
        if product:
            sub = df_copy[df_copy["Product_Item"].str.lower() == product.lower()]
            if len(sub):
                item_code = sub["Item_Code"].iloc[0]
                mac = sub["MACHINE_GROUP"].iloc[0]
                eff = round(sub["Shift_Efficiency (%)"].mean(), 2)
                oee = round(sub["OEE"].mean(), 2)
                maint = int(sub["Maintenance_Needed"].sum())
                reasoning_text += (
                    f" Product {product} (Item Code: {item_code}) runs on {mac} "
                    f"with efficiency {eff}%, OEE {oee}, and {maint} maintenance flags."
                )
                analysis.update({
                    "Product": product,
                    "Item_Code": item_code,
                    "MACLINE": mac,
                    "Efficiency": eff,
                    "OEE": oee,
                    "Maintenance_Flags": maint
                })

    except Exception as e:
        reasoning_text = f"(⚠️ Data processing error: {e})"

    return reasoning_text.strip(), analysis, macline, product

# -------------------------------------------------------
# 6️⃣ GPT contextual reasoning layer
# -------------------------------------------------------
def ask_insight_agent(question, prev_context):
    """
    Returns either:
      - (str_response, prev_context)  OR
      - (dict_response, prev_context) where dict_response contains keys 'text' and 'graph'
    """
    prev_context = prev_context or {}

    # Detect graph request
    if any(k in question.lower() for k in ["graph", "plot", "chart", "visualize", "show"]):
        metric = "Shift_Efficiency (%)"
        if "oee" in question.lower():
            metric = "OEE"
        elif "utilization" in question.lower():
            metric = "Utilization_Rate (%)"

        # If product explicitly requested
        prod = None
        if "product" in question.lower() or "for" in question.lower() or extract_product(question, df):
            prod = extract_product(question, df) or prev_context.get("last_product")

        # Generate graph (product or by MACHINE_GROUP)
        if prod:
            graph_path = generate_graph(df, metric=metric, product_filter=prod)
            if graph_path:
                text = f"📊 Generated graph for {metric} of product {prod}."
                return {"text": text, "graph": graph_path}, prev_context
            else:
                return f"⚠️ No data found to plot for product '{prod}'.", prev_context

        # No product: graph across MACHINE_GROUP
        graph_path = generate_graph(df, metric=metric, by="MACHINE_GROUP")
        if graph_path:
            text = f"📊 Generated graph for {metric} across all lines."
            return {"text": text, "graph": graph_path}, prev_context
        else:
            return "⚠️ No data available to generate the requested graph.", prev_context

    # Normal reasoning
    reasoning_text, analysis, macline, product = run_pandas_reasoning(question, prev_context)
    is_followup = detect_followup_reference(question)

    # Handle follow-ups
    if is_followup:
        if prev_context.get("last_context_type") == "product" and "last_product" in prev_context:
            prod = prev_context["last_product"]
            follow_text, _, _, _ = run_pandas_reasoning(f"status of {prod}", prev_context)
            reasoning_text = f"(Follow-up referring to {prod}) {follow_text}"
        elif prev_context.get("last_context_type") == "macline" and "last_macline" in prev_context:
            mac = prev_context["last_macline"]
            follow_text, _, _, _ = run_pandas_reasoning(f"status of {mac}", prev_context)
            reasoning_text = f"(Follow-up referring to {mac}) {follow_text}"

    # Update context
    if macline:
        prev_context["last_macline"] = macline
        prev_context["last_context_type"] = "macline"
    if product:
        prev_context["last_product"] = product
        prev_context["last_context_type"] = "product"

    # GPT contextual response
    system_prompt = (
        "You are a professional manufacturing analytics assistant. "
        "You analyze structured data, recall context, and explain insights clearly.\n\n"
        f"Example data sample:\n{df.sample(5).to_dict(orient='records')}\n\n"
        f"Analysis result:\n{reasoning_text}\n\n"
        f"Conversation memory:\n{prev_context}\n\n"
        "Respond concisely with factual, data-backed insights."
    )

    completion = client.chat.completions.create(
        model=chat_deployment,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        temperature=0.35,
        max_tokens=700
    )

    gpt_reply = completion.choices[0].message.content
    return f"{reasoning_text}\n\n🤖 Insight:\n{gpt_reply}", prev_context

# -------------------------------------------------------
# 7️⃣ Interactive chat loop
# -------------------------------------------------------
# -------------------------------------------------------
# 8️⃣ Flask integration wrapper
# -------------------------------------------------------
class FactoryGPT:
    """
    Wrapper class to integrate the Manufacturing Insight Assistant with Flask.
    Provides an .ask(question) interface.
    """
    def __init__(self):
        print("🤖 Initializing Manufacturing Insight Assistant...")
        self.memory_context = {}
        # Dataset path confirmation
        print(f"📦 Using dataset: {DATA_PATH}")
        print(f"✅ Assistant ready for analysis.\n")

    def ask(self, question: str):
        """Main interface used by Flask to handle user queries."""
        try:
            result, self.memory_context = ask_insight_agent(question, self.memory_context)
            # If the result is a dict, return it directly (Flask route will package it)
            return result
        except Exception as e:
            return f"⚠️ Error while processing your request: {str(e)}"

if __name__ == "__main__":
    print("⚙️ Manufacturing Insight Assistant — Product + MACLINE + Graph Intelligence")
    print("------------------------------------------------------------")
    print("Examples:")
    print("  • efficiency of MACLINE-1")
    print("  • Axion (V7.1)")
    print("  • item code pls")
    print("  • same product OEE?")
    print("  • show efficiency graph\n")

    memory_context = {}

    while True:
        q = input("Ask: ").strip()
        if q.lower() in ["exit", "quit", "bye"]:
            print("🧩 Shutting down assistant... Goodbye engineer 👋")
            break
        try:
            answer, memory_context = ask_insight_agent(q, memory_context)
            # If graph dict returned, format output for terminal
            if isinstance(answer, dict):
                print(f"\n{answer.get('text')}\nGraph path: {answer.get('graph')}\n")
            else:
                print(f"\n{answer}\n")
        except Exception as e:
            print(f"⚠️ Error: {e}\n")
