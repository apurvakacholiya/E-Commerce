import json
import os
import re
import requests
import yaml
from pathlib import Path
from snowflake.snowpark import Session

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------
RUN_RESULTS_PATH = os.path.join("target", "run_results.json")

# dbt Profile Settings (Update if your profile names differ)
DBT_PROFILE_NAME = "E_Commerce" 
DBT_TARGET = "dev"

# Snowflake Cortex Model Selection
# 🧠 Ordered list of Cortex models to try (Best reasoning models first)
CORTEX_MODELS = [
    "llama3.3-70b",          # The best balance: extremely smart at SQL, very cheap.
    "llama3.1-8b",           # Ultra-lightweight and cheap fallback for basic typos.
    "mistral-large3",        # Strong enterprise logic fallback.
    "snowflake-arctic"       # Snowflake's native enterprise model. 
]

def resolve_profile_value(value):
    """Return the dbt profile value as-is for plain literals or Jinja expressions."""
    if not isinstance(value, str):
        return value

    value = value.strip()
    if value.startswith("{{") and "env_var" in value:
        match = re.search(r"env_var\('([^']+)'(?:,\s*'([^']*)')?\)", value)
        if match:
            env_name, default = match.groups()
            return os.getenv(env_name, default)

    return value


def get_snowflake_credentials():
    """Reads Snowflake credentials securely from dbt's profiles.yml."""
    project_dir = Path(__file__).resolve().parent
    candidate_paths = [
        project_dir / "profiles.yml",
        Path.home() / ".dbt" / "profiles.yml",
        Path.home() / "profiles.yml",
    ]

    profiles_path = None
    for path in candidate_paths:
        if path.exists():
            profiles_path = path
            break

    if not profiles_path:
        raise FileNotFoundError("Could not find profiles.yml in the project directory or ~/.dbt/.")

    print(f"📖 Reading credentials from {profiles_path}...")
    
    with open(profiles_path, 'r', encoding='utf-8') as f:
        profiles = yaml.safe_load(f)

    try:
        target_config = profiles[DBT_PROFILE_NAME]['outputs'][DBT_TARGET]
        
        connection_params = {
            "account": resolve_profile_value(target_config.get("account")),
            "user":  (target_config.get("user")),
            "password": resolve_profile_value(target_config.get("password")),
            "role": resolve_profile_value(target_config.get("role")),
            "warehouse": resolve_profile_value(target_config.get("warehouse")),
            "database": resolve_profile_value(target_config.get("database")),
            "schema": resolve_profile_value(target_config.get("schema")),
            "authenticator": resolve_profile_value(target_config.get("authenticator")),
        }
        
        if not connection_params["password"]:
             print("⚠️ Warning: No password found in profiles.yml. Ensure you are using standard auth for this PoC.")
             
        return connection_params
        
    except KeyError as e:
        raise KeyError(f"Error parsing profiles.yml. Check that profile '{DBT_PROFILE_NAME}' and target '{DBT_TARGET}' exist. Missing: {e}")


def send_alert(title: str, body: str):
    """Prints the agent diagnosis to the terminal."""
    print("\n" + "="*80)
    print(f"🚨 {title}")
    print("="*80)
    print(body)
    print("="*80 + "\n")


def parse_run_results(file_path: str):
    """Parses dbt's run_results.json to find failed models or tests."""
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}. Please run 'dbt build' or 'dbt run' first.")
        return []

    with open(file_path, "r") as f:
        data = json.load(f)

    failures = []
    for result in data.get("results", []):
        if result.get("status") in ["error", "fail"]:
            unique_id = result.get("unique_id", "")
            message = result.get("message", "")
            compiled_path = result.get("compiled_path")
            
            failures.append({
                "unique_id": unique_id,
                "status": result.get("status"),
                "message": message,
                "compiled_path": compiled_path
            })
            
    return failures


def run_agent():
    print("🤖 Initializing Autonomous dbt Debugger Agent (Version 2 - Schema Aware)...")

    # 1. Parse run_results.json
    failures = parse_run_results(RUN_RESULTS_PATH)
    if not failures:
        print("✅ No errors found in run_results.json. Everything built cleanly!")
        return

    print(f"🔍 Found {len(failures)} failure(s) in dbt run.")

    # 2. Connect to Snowflake dynamically using profiles.yml
    print("❄️ Connecting to Snowflake...")
    try:
        connection_params = get_snowflake_credentials()
        session = Session.builder.configs(connection_params).create()
    except Exception as e:
        print(f"❌ Failed to connect to Snowflake: {e}")
        return

    for item in failures:
        unique_id = item["unique_id"]
        error_msg = item["message"]

        print(f"\n⚙️ Analyzing node: {unique_id}")

        # 3. Read compiled SQL (Aggressive Search)
        # 3. Read compiled SQL (Smart Pathing for Models AND Tests)
        compiled_sql = "Compiled SQL file not available."
        compiled_path_str = item.get("compiled_path")
        
        # Use os.getcwd() to guarantee we start at the dbt project root
        project_root = Path(os.getcwd())
        
        # First, try to use the exact path dbt gave us in run_results.json
        if compiled_path_str:
            full_path = project_root / compiled_path_str
            if full_path.exists():
                print(f"📄 Successfully loaded compiled SQL from dbt path: {full_path.name}")
                with open(full_path, "r", encoding="utf-8") as f:
                    compiled_sql = f.read()
            else:
                print(f"⚠️ Warning: dbt provided path {full_path} but it wasn't found on disk.")
                
        # If that fails, aggressively search the target folder for the correct file name
        if compiled_sql == "Compiled SQL file not available.":
            # Extract the actual file name (Tests have hashes at the end, Models do not)
            node_parts = unique_id.split('.')
            if unique_id.startswith('test.') and len(node_parts) >= 3:
                model_name = node_parts[-2] + ".sql"  # Grabs the actual test name, ignoring the hash
            else:
                model_name = node_parts[-1] + ".sql"  # Grabs standard model names
                
            target_compiled_dir = project_root / "target" / "compiled"
            found_files = list(target_compiled_dir.rglob(model_name))
            
            if found_files:
                full_path = found_files[0]
                print(f"📄 Successfully loaded compiled SQL from aggressive search: {full_path.name}")
                with open(full_path, "r", encoding="utf-8") as f:
                    compiled_sql = f.read()
            else:
                print(f"⚠️ Warning: Could not find compiled SQL file for {unique_id}")

        # 3.5 Context Enrichment (Fetch Schema from Snowflake)
        print("🔎 Extracting upstream schema context from Snowflake...")
        schema_context = ""
        
        # Regex to find fully qualified table names like DATABASE.SCHEMA.TABLE in the compiled SQL
        table_matches = re.findall(r'([A-Za-z0-9_]+)\.([A-Za-z0-9_]+)\.([A-Za-z0-9_]+)', compiled_sql)
        unique_tables = set(table_matches)
        
        for db, schema, table in unique_tables:
            try:
                # Query Snowflake for the actual columns in this table
                query = f"SELECT COLUMN_NAME FROM {db}.INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = '{schema.upper()}' AND TABLE_NAME = '{table.upper()}'"
                results = session.sql(query).collect()
                columns = [row["COLUMN_NAME"].lower() for row in results]
                
                if columns:
                    schema_context += f"- Upstream Table `{table}` actually contains these columns: {', '.join(columns)}\n"
            except Exception as e:
                print(f"⚠️ Could not fetch schema for {table}: {e}")
                
        if not schema_context:
            schema_context = "No upstream table context could be extracted."
        else:
            print("✅ Successfully fetched schema context!")

        # 4. Construct Prompt
        prompt = f"""You are an expert Data Engineer debugging a dbt pipeline on Snowflake.
A dbt execution failed on node: '{unique_id}'.

Error Details:
{error_msg}

Compiled SQL from dbt target directory:
```sql
{compiled_sql}
```
CRITICAL DATABASE SCHEMA CONTEXT:
Use the following verified column names to fix the SQL. Do NOT guess or hallucinate column names.
{schema_context}

STRICT INSTRUCTIONS:
Do NOT show your thought process, intermediate steps, or incorrect queries.
Do NOT write conversational filler. Get straight to the point.
If the "Compiled SQL" provided above says it is not available, do NOT attempt to write the full query. Instead, provide 2-3 concise bullet points on how the user can fix the test.
If the "Compiled SQL" is provided, you MUST return the FULL, untruncated SQL with all errors fixed.

You MUST format your response EXACTLY using this template:

🎯 Root Cause
[Identify the exact root cause of the error. 1-2 sentences explaining exactly why it failed based on the schema or error.]

🛠️ Suggested Fix
[1-2 bullet points explaining exactly what line/column needs to be changed.]

IMPORTANT: Review the ENTIRE provided SQL code. If an incorrect column name (like the one in the error) is referenced in multiple CTEs or SELECT statements, you MUST fix every single occurrence.

✅ Corrected Code
[Provide the FULL, complete, corrected SQL script(highlighted) here. If the original SQL was not available, leave this block empty.
Do NOT truncate the code or use placeholders like "...rest of the code...".
Keep your explanation concise and format the fixed code cleanly in Markdown with the corrected places as highlighted.]
"""

        # # 5. Call Groq API Directly via REST
        # print("🧠 Invoking Groq AI (Llama 3) for diagnosis...")
        # try:
        #     api_key = os.environ.get("GROQ_API_KEY")
        #     if not api_key:
        #         print("❌ GROQ_API_KEY not found in .env file.")
        #         continue

        #     url = "https://api.groq.com/openai/v1/chat/completions"
        #     headers = {
        #         "Authorization": f"Bearer {api_key}",
        #         "Content-Type": "application/json"
        #     }
        #     payload = {
        #         "model": "llama-3.3-70b-versatile",
        #         "messages": [{"role": "user", "content": prompt}]
        #     }

        #     response = requests.post(url, headers=headers, json=payload)

        #     if response.status_code == 200:
        #         diagnosis = response.json()['choices'][0]['message']['content']
                
        #         # 6. Output Results
        #         send_alert(
        #             title=f"dbt Failure Detected: {unique_id}",
        #             body=f"**Error Message:**\n{error_msg}\n\n**🤖 AI Diagnosis & Fix:**\n{diagnosis}"
        #         )
        #     else:
        #         print(f"❌ Groq API Error: {response.status_code}\n{response.text}")

        # except Exception as e:
        #     print(f"❌ Failed to run AI completion: {e}") 

        # 5. Call Snowflake Cortex AI (With Fallback Mechanism)
        print("🧠 Invoking Snowflake Cortex AI...")
        diagnosis = None
        used_model = None

        for model in CORTEX_MODELS:
            print(f"   🔄 Trying model: {model}...")
            try:
                # Use Snowflake's $$ string delimiters to safely pass complex prompts containing code/quotes
                query = f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{model}', $${prompt}$$)"
                
                # Execute the built-in SQL function and extract the text response
                result = session.sql(query).collect()
                diagnosis = result[0][0]
                
                used_model = model
                print(f"   ✅ Successfully generated response using {model}!")
                break  # Exit the loop entirely because it worked!
            
            except Exception as e:
                # Print the actual error so we know exactly WHY it failed
                print(f"   ⚠️ {model} failed. Reason: {str(e).strip()}")
                
        # 6. Output Results
        if diagnosis:
            send_alert(
                title=f"dbt Failure Detected: {unique_id}",
                body=f"**Error Message:**\n{error_msg}\n\n**🤖 AI Diagnosis & Fix (via {used_model}):**\n{diagnosis}"
            )
        else:
            print("\n❌ All Cortex models failed. Please verify that:")
            print("   1. Your role has the SNOWFLAKE.CORTEX_USER database role.")
            print("   2. At least one of the specified models is available in your Snowflake region.")

    session.close()
    print("👋 Agent finished execution. Session closed.")


if __name__ == "__main__":
    run_agent()