#!/usr/bin/env python3
"""
NOKIA FACTORY GPT - Iterative Analyst
 
This agent combines robust iterative analysis with deep domain knowledge
for maximum accuracy in complex factory databases.
"""
 
import os
import warnings
import json
import re
from datetime import datetime
 
# --- Core Libraries ---
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain.schema import HumanMessage
import pyodbc
 
# --- Initial Setup ---
warnings.filterwarnings("ignore")
load_dotenv()
 
class FactoryGPT:
    def __init__(self):
        print("\n--- Initializing Nokia Factory GPT ---")
        self.db_connection_string = self.setup_database()
        self.llm = self.setup_llm()
        self.db_schema = self.get_database_schema()
       
        # Machine intelligence and conversation memory
        self.machine_intelligence = {}
        self.conversation_history = []
        self.learn_machine_intelligence()
 
        print("--------------------------------------\n")
 
    def setup_database(self):
        """Setup database connection using secure environment variables."""
        print("1. Preparing SQL Database Connection...")
        try:
            db_server = os.getenv("DB_SERVER")
            db_name = os.getenv("DB_DATABASE")
            db_user = os.getenv("DB_UID")
            db_pass = os.getenv("DB_PWD")
           
            if not all([db_server, db_name, db_user, db_pass]):
                raise ValueError("Database environment variables (DB_SERVER, DB_DATABASE, DB_UID, DB_PWD) not set.")
 
            connection_string = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={db_server};"
                f"DATABASE={db_name};"
                f"UID={db_user};"
                f"PWD={db_pass};"
            )
            with pyodbc.connect(connection_string, timeout=5) as conn: 
                pass
            print("   ✅ Database connection is valid.")
            return connection_string
        except Exception as e:
            raise Exception(f"Could not connect to SQL Database: {e}")
 
    def setup_llm(self):
        """Connecting to Azure OpenAI LLM."""
        print("2. Connecting to Azure OpenAI LLM...")
        try:
            azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            api_key = os.getenv("AZURE_OPENAI_KEY")
            deployment_name = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")
            api_version = os.getenv("AZURE_OPENAI_API_VERSION")
           
            if not all([azure_endpoint, api_key, deployment_name, api_version]):
                raise ValueError("One or more Azure OpenAI environment variables are missing.")
 
            llm = AzureChatOpenAI(
                azure_endpoint=azure_endpoint,
                openai_api_key=api_key,
                azure_deployment=deployment_name,
                openai_api_version=api_version,
                temperature=0.0,
            )
            print("   ✅ Connected to LLM.")
            return llm
        except Exception as e:
            raise Exception(f"Could not connect to LLM: {e}")
           
    def get_database_schema(self):
        """Discovering the full, dynamic database schema."""
        print("3. Discovering Database Schema...")
        schema_parts = []
        try:
            with pyodbc.connect(self.db_connection_string) as conn:
                cursor = conn.cursor()
                all_tables = [row.table_name for row in cursor.tables(tableType='TABLE')]
                relevant_tables = [table for table in all_tables if not table.lower().startswith("sys")]
               
                for table_name in relevant_tables:
                    columns = [f"    {row.column_name} {row.type_name.upper()}" 
                              for row in cursor.columns(table=table_name)]
                    if columns:
                        schema_parts.append(f"CREATE TABLE {table_name} (\n" + ",\n".join(columns) + "\n);")
           
            schema = "\n\n".join(schema_parts)
            print(f"   ✅ Complete schema discovered ({len(relevant_tables)} tables).")
            return schema
        except Exception as e:
            raise Exception(f"Could not discover schema: {e}")
 
    def learn_machine_intelligence(self):
        """Learns all distinct machine names and groups from relevant tables."""
        print("4. Learning Machine Intelligence...")
        try:
            with pyodbc.connect(self.db_connection_string) as conn:
                cursor = conn.cursor()
                all_tables = [row.table_name for row in cursor.tables(tableType='TABLE')]
                relevant_tables = [table for table in all_tables if not table.lower().startswith("sys")]
 
                for table in relevant_tables:
                    columns_cursor = cursor.columns(table=table)
                    column_names = [row.column_name for row in columns_cursor]
                   
                    if 'MACHINE_NAME' in column_names:
                        self._learn_machines_from_column(conn, table, 'MACHINE_NAME')
                    if 'MACHINE_GROUP' in column_names:
                        self._learn_machines_from_column(conn, table, 'MACHINE_GROUP')
           
            print(f"   ✅ Learned {len(self.machine_intelligence)} machine keywords.")
        except Exception as e:
            print(f"   ⚠️ WARNING: Could not learn machine intelligence. Error: {e}")
 
    def _learn_machines_from_column(self, conn, table, column):
        """Helper to query and store machine names."""
        try:
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT DISTINCT {column} FROM {table} WHERE {column} IS NOT NULL")
                rows = cursor.fetchall()
                machine_names = [row[0] for row in rows]
               
                for name in machine_names:
                    if not name: 
                        continue
                    # Advanced tokenizer
                    words = re.split(r'[^a-zA-Z0-9]', name)
                    camel_case_tokens = re.findall(r'[A-Z][a-z]*|[0-9]+|[a-z]+', name)
                    all_tokens = words + camel_case_tokens
 
                    for token in all_tokens:
                        clean_token = token.lower().strip()
                        if len(clean_token) > 2:
                            if clean_token not in self.machine_intelligence:
                                self.machine_intelligence[clean_token] = set()
                            self.machine_intelligence[clean_token].add(name)
        except Exception as e:
            print(f"      - Skipping machine learning for {table}.{column}. Error: {e}")
 
    def _execute_sql(self, sql: str):
        """Executes a SQL query with a safety gate."""
        # SQL Safety Gate
        disallowed_keywords = ['DELETE', 'DROP', 'UPDATE', 'INSERT', 'TRUNCATE', 'ALTER', 'EXEC', 'GRANT']
        sql_upper = sql.upper()
        if any(keyword in sql_upper for keyword in disallowed_keywords):
            print(f"      -> 🛑 SAFETY VIOLATION: Blocked destructive query.")
            return None, "SQL Error: Query contains restricted keywords (e.g., DELETE, DROP, UPDATE)."
 
        print(f"      -> Executing SQL: {sql}")
        try:
            with pyodbc.connect(self.db_connection_string) as conn:
                cursor = conn.cursor()
                cursor.execute(sql)
                rows = cursor.fetchall()
                columns = [column[0] for column in cursor.description]
                results = [dict(zip(columns, row)) for row in rows] if rows else []
                return results, None
        except pyodbc.Error as e:
            return None, f"SQL Error: {str(e)}"
           
    def _handle_general_conversation(self, question: str) -> str:
        """Handles non-data questions."""
        print("   -> Routing to general conversation module.")
        history_context = "\n".join([f"{entry['role']}: {entry['content']}" 
                                    for entry in self.conversation_history[-5:]])
       
        prompt = f"""You are Nokia Factory GPT, a helpful and friendly AI assistant for the Nokia factory.
       
CONVERSATION HISTORY:
{history_context}
       
USER'S CURRENT MESSAGE:
{question}
       
Respond naturally and conversationally. Be helpful, professional, and friendly.
If asked what you can do, mention you can help with factory data queries, machine information, production metrics, downtime analysis, and more.
"""
        response = self.llm.invoke([HumanMessage(content=prompt)])
        return response.content.strip()
       
    def _understand_intent(self, question: str) -> str:
        """A simple router to separate chat from data queries."""
        question_lower = question.lower()
       
        general_indicators = [
            "how are you", "what's up", "how do you feel", "tell me about yourself",
            "what can you do", "who are you", "introduce yourself", "are you gpt",
            "hello", "hi", "good morning", "good afternoon", "good evening", "hey"
        ]
        if any(indicator in question_lower for indicator in general_indicators):
            return "chat"
           
        return "data"
 
    def ask(self, question: str) -> str:
        """
        Main entry point for Factory GPT.
        Handles both chat and data queries using iterative analysis.
        """
        print(f"\n🤖 Processing: '{question}'")
       
        # Intent Router
        intent = self._understand_intent(question)
        if intent == "chat":
            answer = self._handle_general_conversation(question)
            self.conversation_history.append({"role": "user", "content": question})
            self.conversation_history.append({"role": "assistant", "content": answer})
            return answer
 
        # --- STAGE 1: THE HUNT ---
        history_context = "\n".join([f"{entry['role']}: {entry['content']}" 
                                    for entry in self.conversation_history[-10:]])
        machine_keywords = list(self.machine_intelligence.keys())
 
        planning_prompt = f"""You are an expert data analyst. Analyze the user's question and find the best way to answer it.
       
DATABASE SCHEMA:
{self.db_schema}
 
CONVERSATION HISTORY:
{history_context}
       
KNOWN MACHINE KEYWORDS:
{machine_keywords[:1000]}
 
User Question: "{question}"
 
Identify the TOP 3 most likely (table, column) pairs that could answer this question.
The "column" should be the primary metric (e.g., CYCLE_TIME, TOTAL_PRODUCTION_COUNT).
Return ONLY a valid JSON object with key "candidates" containing a list of objects with "table" and "column" keys.
"""
        print("\n   📊 Stage 1: Identifying possible paths...")
        response = self.llm.invoke([HumanMessage(content=planning_prompt)])
        try:
            content = response.content.strip().replace("`", "").replace("json", "")
            candidates = json.loads(content)["candidates"]
            print(f"      -> Found {len(candidates)} potential paths")
        except (json.JSONDecodeError, KeyError) as e:
            print(f"      -> ❌ Planning failed: {e}")
            return "My apologies, I was unable to form an initial plan. Please rephrase your question."
 
        # --- STAGE 2: ITERATIVE STRIKES ---
        print("\n   ⚔️ Stage 2: Attempting queries...")
       
        few_shot_examples = """
### EXAMPLES ###
       
-- Question: which machine has the highest downtime for macline-2 for yesterday?
SELECT TOP 1 MACHINE_NAME, MAX(CAST(ISNULL(NULLIF(ROBOT_DOWNTIME, ''), '0') AS FLOAT)) as max_downtime
FROM HOURLY_running_idle_downtime
WHERE (UPPER(MACHINE_NAME) LIKE '%MAC_LINE_2%' OR MACHINE_GROUP = 'MACLINE-2')
  AND CAST(CREATED_DATE AS DATE) = CAST(DATEADD(day, -1, GETDATE()) AS DATE)
GROUP BY MACHINE_NAME
ORDER BY max_downtime DESC;
       
-- Question: average cycletime for mac line 2 dual robot for may 2025
SELECT AVG(CAST(ISNULL(NULLIF(CYCLE_TIME, ''), '0') AS FLOAT)) as avg_cycle_time
FROM TBL_LIVE_MQTT_DATA
WHERE (UPPER(MACHINE_NAME) LIKE '%MAC_LINE_2%' AND UPPER(MACHINE_NAME) LIKE '%DUAL%')
  AND CAST(Created_Date AS DATE) >= '2025-05-01'
  AND CAST(Created_Date AS DATE) < '2025-06-01';
"""
 
        successful_result = None
        successful_sql = None
       
        for i, candidate in enumerate(candidates):
            print(f"\n   → Attempt {i+1}/{len(candidates)}")
            table = candidate.get("table")
            column = candidate.get("column")
            if not table or not column:
                continue
               
            print(f"      Target: {table}.{column}")
 
            sql_generation_prompt = f"""Write a flawless SQL Server query to answer the user's question.
MUST use table: {table}
MUST use column: {column}
 
RULES:
1. AGGREGATION:
   - Use SUM/AVG/COUNT/MAX/MIN for "total"/"average"/"highest"/"lowest"
   - For "what is [metric]" on live tables: SELECT TOP 1 ... ORDER BY Created_Date DESC
2. FILTERING:
   - Split machine keywords: "galvatron trx bullet" → LIKE '%GALVATRON%' AND LIKE '%TRX%' AND LIKE '%BULLET%'
   - Machine groups: (LIKE '%MACLINE 1%' OR MACHINE_GROUP = 'MACLINE-1')
3. NULL HANDLING:
   - Wrap metrics: CAST(ISNULL(NULLIF({column}, ''), '0') AS FLOAT)
 
SCHEMA:
{self.db_schema}
           
{few_shot_examples}
 
User Question: "{question}"
           
Return ONLY the SQL query.
"""
           
            response = self.llm.invoke([HumanMessage(content=sql_generation_prompt)])
            sql_query = response.content.strip().replace("```sql", "").replace("```", "").strip().rstrip(";")
           
            sql_result, error = self._execute_sql(sql_query)
 
            if error:
                print(f"      ❌ Failed: {error[:100]}")
                continue
 
            if not sql_result:
                print(f"      ⚠️ No data found")
                continue
           
            print("      ✅ Success!")
            successful_result = sql_result
            successful_sql = sql_query
            break
 
        # --- STAGE 3: SYNTHESIS ---
        if successful_result:
            print("\n   📝 Stage 3: Formatting response...")
            answer = self.format_conversational_response(question, successful_result)
           
            self.conversation_history.append({"role": "user", "content": question})
            self.conversation_history.append({
                "role": "assistant", 
                "content": answer, 
                "sql_executed": successful_sql
            })
           
            return answer
 
        print("   ❌ All attempts failed.")
        return "I couldn't find a definitive answer in the database. Please try rephrasing your question or check if the data exists."
 
    def format_conversational_response(self, question, result):
        """Renders the final result in a human-readable way."""
        question_lower = question.lower()
       
        if isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict):
           
            # Case 1: Single row, single value
            if len(result) == 1 and len(result[0]) == 1:
                key, value = list(result[0].items())[0]
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    return f"The result is: {value}"
               
                if any(word in question_lower for word in ["production", "count"]):
                    return f"📊 The total production count is **{value:,.0f} units**."
                elif "downtime" in question_lower:
                    if "average" in question_lower or "avg" in question_lower:
                        return f"⏱️ The average downtime is **{self._format_time_duration(value)}**."
                    elif "total" in question_lower or "sum" in question_lower:
                        return f"⏱️ The total downtime is **{self._format_time_duration(value)}**."
                    else:
                        return f"⏱️ The most recent downtime is **{self._format_time_duration(value)}**."
                elif any(word in question_lower for word in ["cycletime", "cycle time"]):
                    if "average" in question_lower or "avg" in question_lower:
                        return f"⏲️ The average cycle time is **{value:,.2f} seconds**."
                    else:
                        return f"⏲️ The most recent cycle time is **{value:,.2f} seconds**."
                else:
                    return f"The result is **{value:,.2f}**."
 
            # Case 2: Single row, multiple values
            if len(result) == 1 and len(result[0]) > 1:
                machine_name = result[0].get('MACHINE_NAME') or result[0].get('MACHINE_GROUP')
                value_key = next((k for k in result[0] if k not in ['MACHINE_NAME', 'MACHINE_GROUP']), None)
               
                if machine_name and value_key:
                    try:
                        value = float(result[0][value_key])
                    except (ValueError, TypeError):
                        return f"Found data for **{machine_name}**: {result[0][value_key]}"
                    
                    operation = "highest" if "highest" in question_lower else "lowest"
                   
                    if "downtime" in question_lower:
                        return f"🏭 The machine with the {operation} downtime is **{machine_name}** with **{self._format_time_duration(value)}**."
                    elif "cycletime" in question_lower or "cycle time" in question_lower:
                        return f"🏭 The machine with the {operation} cycle time is **{machine_name}** with **{value:,.2f} seconds**."
                    elif "production" in question_lower:
                        return f"🏭 The machine with the {operation} production is **{machine_name}** with **{value:,.0f} units**."
           
            # Case 3: Multiple rows
            if len(result) > 1:
                formatted_results = []
                for idx, row in enumerate(result[:5], 1):
                    row_str = ", ".join([f"{k}: {v}" for k, v in row.items()])
                    formatted_results.append(f"{idx}. {row_str}")
                
                return f"📋 Found {len(result)} results. Here are the top 5:\n\n" + "\n".join(formatted_results)
 
        # Fallback
        return f"Here's what I found:\n```\n{json.dumps(result, indent=2)}\n```"
 
    def _format_time_duration(self, seconds):
        """Format time duration in a human-readable way."""
        try:
            seconds = float(seconds)
        except (ValueError, TypeError):
            return str(seconds)
           
        if seconds > 3600:
            hours = seconds / 3600
            return f"{seconds:,.0f} seconds (~{hours:.1f} hours)"
        elif seconds > 60:
            minutes = seconds / 60
            return f"{seconds:,.0f} seconds (~{minutes:.1f} minutes)"
        else:
            return f"{seconds:,.0f} seconds"
 
 
# For standalone testing
if __name__ == "__main__":
    agent = FactoryGPT()
    print("\n✅ Factory GPT is ready!")
    print("   Type 'exit' or 'quit' to end the session.\n")
   
    while True:
        try:
            user_question = input("Ask a question: ")
            if user_question.lower().strip() in ["exit", "quit"]:
                print("👋 Goodbye!")
                break
           
            if user_question.strip():
                agent_answer = agent.ask(user_question)
                print("\n" + "="*80)
                print(f"🤖 {agent_answer}")
                print("="*80 + "\n")
               
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Goodbye!")
            break