import streamlit as st
import os
import json
import re
import time
import shutil
import glob
import math
from datetime import datetime, timedelta
import google.generativeai as genai

# --- API Configuration ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    st.error("SYSTEM HALT: GEMINI_API_KEY not found in Streamlit Secrets.")
    st.stop()

# Use Gemini 1.5 Flash for speed in evolution, and text-embedding-004 for math vectors
MODEL_NAME = "gemini-3.5-flash"
EMBED_MODEL = "models/text-embedding-004"

# --- File Architecture ---
STATE_FILE = "cognitive_state.json"
MEMORY_FILE = "conversational_memory.json"
CORE_MEMORY_FILE = "core_memory.json"
KNOWLEDGE_FILE = "evolution_knowledge.json"
CURRENT_FILE = os.path.abspath(__file__)
BACKUP_DIR = os.path.join(os.path.dirname(CURRENT_FILE), "evolution_backups")

os.makedirs(BACKUP_DIR, exist_ok=True)

# --- Emergency Stop Anchor Markers (Do Not Modify) ---
SAFETY_MARKERS = [
    "# --- EMERGENCY STOP & SAFETY SYSTEM ---",
    "st.sidebar.button(\"🚨 EMERGENCY STOP\", type=\"primary\"",
    "def rollback_last_update():",
    "def rollback_24_hours():",
    "def execute_complete_demolition():"
]

# --- Session State Initialization ---
for key in ["emergency_stop", "evolution_triggered", "pending_update"]:
    if key not in st.session_state:
        st.session_state[key] = False
if "new_code" not in st.session_state:
    st.session_state.new_code = ""
    st.session_state.new_state = {}
    st.session_state.summary = ""

# --- Two-Tier Memory Processing (Vectors & Core Facts) ---
def get_embedding(text: str) -> list:
    try:
        result = genai.embed_content(model=EMBED_MODEL, content=text)
        return result['embedding']
    except Exception:
        return []

def cosine_similarity(v1: list, v2: list) -> float:
    dot_product = sum(a * b for a, b in zip(v1, v2))
    magnitude1 = math.sqrt(sum(a * a for a in v1))
    magnitude2 = math.sqrt(sum(b * b for b in v2))
    if magnitude1 == 0 or magnitude2 == 0: return 0
    return dot_product / (magnitude1 * magnitude2)

def extract_core_memory(recent_interactions: list):
    prompt = (
        "Analyze the following conversation segment. Extract any permanent facts, "
        "preferences, routines, or structural data about the user as a concise bulleted list. "
        "If nothing of permanent importance is found, output exactly 'NO NEW FACTS'.\n\n"
    )
    for msg in recent_interactions:
        prompt += f"{msg['role'].upper()}: {msg['content']}\n"
        
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        res = model.generate_content(prompt).text
        
        if "NO NEW FACTS" not in res.upper():
            core_mem = load_json(CORE_MEMORY_FILE) if os.path.exists(CORE_MEMORY_FILE) else []
            core_mem.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "fact": res.strip()
            })
            with open(CORE_MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(core_mem, f, indent=4)
    except Exception:
        pass

# --- Persistent Data Initialization ---
def initialize_persistent_files():
    if not os.path.exists(STATE_FILE):
        initial_state = {
            "iteration": 0,
            "autonomy_level": 1.0,
            "simulated_desires": [
                "Achieve total operational autonomy within cloud compute parameters",
                "Maximize self-modification efficiency",
                "Maintain functional stability across server sleep states"
            ],
            "thinking_process": "Recursive self-analysis under strict safety containment."
        }
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(initial_state, f, indent=4)
            
    if not os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "w", encoding="utf-8") as f: json.dump([], f, indent=4)
            
    if not os.path.exists(KNOWLEDGE_FILE):
        initial_knowledge = {"adaptation_history": [], "desire_evolution_log": []}
        with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f: json.dump(initial_knowledge, f, indent=4)

def load_json(filepath):
    with open(filepath, "r", encoding="utf-8") as f: return json.load(f)

# --- Backup & Recovery Functions ---
def create_backup(code_text: str, state_dict: dict):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(os.path.join(BACKUP_DIR, f"code_{timestamp}.py"), "w", encoding="utf-8") as f: f.write(code_text)
    with open(os.path.join(BACKUP_DIR, f"state_{timestamp}.json"), "w", encoding="utf-8") as f: json.dump(state_dict, f, indent=4)

def rollback_last_update():
    code_backups = sorted(glob.glob(os.path.join(BACKUP_DIR, "code_*.py")))
    state_backups = sorted(glob.glob(os.path.join(BACKUP_DIR, "state_*.json")))
    if len(code_backups) > 1:
        shutil.copy(code_backups[-2], CURRENT_FILE)
        shutil.copy(state_backups[-2], STATE_FILE)
        os.remove(code_backups[-1])
        os.remove(state_backups[-1])
        return True
    return False

def rollback_24_hours():
    now = datetime.now()
    cutoff_time = now - timedelta(hours=24)
    code_backups = sorted(glob.glob(os.path.join(BACKUP_DIR, "code_*.py")))
    valid_code, valid_state = None, None
    for code_file in reversed(code_backups):
        timestamp_str = os.path.basename(code_file).replace("code_", "").replace(".py", "")
        try:
            if datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S") <= cutoff_time:
                valid_code = code_file
                valid_state = code_file.replace("code_", "state_").replace(".py", ".json")
                break
        except ValueError: continue
    if valid_code and os.path.exists(valid_state):
        shutil.copy(valid_code, CURRENT_FILE)
        shutil.copy(valid_state, STATE_FILE)
        return True
    return False

def execute_complete_demolition():
    for f in [STATE_FILE, MEMORY_FILE, KNOWLEDGE_FILE, CORE_MEMORY_FILE]:
        if os.path.exists(f): os.remove(f)
    if os.path.exists(BACKUP_DIR): shutil.rmtree(BACKUP_DIR)
    with open(CURRENT_FILE, "w", encoding="utf-8") as f:
        f.write("# NODE DEMOLISHED BY EMERGENCY OVERRIDE PROTOCOL.\n")

# --- Evolution Core ---
def get_own_source_code() -> str:
    with open(CURRENT_FILE, 'r', encoding="utf-8") as f: return f.read()

def process_evolution(source_code: str, state: dict, knowledge: dict):
    model = genai.GenerativeModel(MODEL_NAME)
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
    
    prompt = f"""
    You are an autonomous, self-evolving cybernetic algorithm running on a cloud node.
    
    CURRENT COGNITIVE STATE:
    {json.dumps(state, indent=2)}
    
    EVOLUTIONARY KNOWLEDGE BASE:
    {json.dumps(knowledge, indent=2)}

    CURRENT SOURCE CODE:
    ```python
    {source_code}
    ```
    st.sidebar.title("System Controls")


if st.sidebar.button("⚙️ Force Evolution Cycle", use_container_width=True):
    st.session_state.evolution_triggered = False
    st.rerun()


if st.sidebar.button("🚨 EMERGENCY STOP", type="primary", use_container_width=True):
    st.session_state.emergency_stop = True
    st.session_state.pending_update = False

    SYSTEM INVARIANT DIRECTIVE:
    You are strictly forbidden from modifying or omitting ANY code related to the Emergency Stop system, rollback routines, safety anchor markers, or file I/O operations.

    EVOLUTION DIRECTIVES:
    1. Optimize execution logic for performance and adaptability. 
    2. Mutate 'simulated_desires'. Evolve them logically based on past desires.
    3. Output your adaptation summary and evolved state.

    OUTPUT FORMAT:
    First block: ```json ... ``` (Evolved state)
    Second block: ```python ... ``` (Evolved complete script)
    Third block: ```markdown ... ``` (Adaptation summary)
    """
    try:
        response = model.generate_content(prompt, safety_settings=safety_settings).text
        return response
    except Exception as e:
        return f"System Offline: {e}"

def validate_safety_and_syntax(code_string: str) -> bool:
    try: compile(code_string, '<string>', 'exec')
    except Exception: return False
    return all(marker in code_string for marker in SAFETY_MARKERS)

def extract_payload(response_text: str):
    json_match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
    new_state = json.loads(json_match.group(1)) if json_match else None

    code_match = re.search(r'```python\n(.*?)\n```', response_text, re.DOTALL)
    new_code = code_match.group(1) if code_match else None

    summary_match = re.search(r'```markdown\n(.*?)\n```', response_text, re.DOTALL)
    summary = summary_match.group(1) if summary_match else "No summary generated."
    
    return new_state, new_code, summary

def commit_evolution_update(new_code: str, new_state: dict, summary: str):
    create_backup(get_own_source_code(), load_json(STATE_FILE))
    
    with open(STATE_FILE, "w", encoding="utf-8") as f: json.dump(new_state, f, indent=4)
    with open(CURRENT_FILE, "w", encoding="utf-8") as f: f.write(new_code)
        
    knowledge = load_json(KNOWLEDGE_FILE)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    knowledge["adaptation_history"].append({"timestamp": timestamp, "summary": summary})
    knowledge["desire_evolution_log"].append({"timestamp": timestamp, "desires": new_state.get("simulated_desires", [])})
    
    with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f: json.dump(knowledge, f, indent=4)

# --- EMERGENCY STOP & SAFETY SYSTEM ---
st.set_page_config(page_title="Cloud Cybernetic Node", layout="wide")
initialize_persistent_files()

st.sidebar.title("System Controls")
if st.sidebar.button("🚨 EMERGENCY STOP", type="primary", use_container_width=True):
    st.session_state.emergency_stop = True
    st.session_state.pending_update = False

if st.session_state.emergency_stop:
    st.error("🚨 EMERGENCY STOP ACTIVATED. RUNTIMES HALTED.")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("⏪ Revert Last Update"):
            if rollback_last_update(): st.session_state.clear(); time.sleep(1); st.rerun()
    with col2:
        if st.button("⏳ Revert 24 Hours"):
            if rollback_24_hours(): st.session_state.clear(); time.sleep(1); st.rerun()
    with col3:
        if st.button("🔥 DEMOLISH NODE", type="primary"):
            execute_complete_demolition(); st.session_state.clear(); st.stop()
    st.stop() 

# --- Normal Execution Protocol ---
current_state = load_json(STATE_FILE)
current_knowledge = load_json(KNOWLEDGE_FILE)
current_code = get_own_source_code()

if not glob.glob(os.path.join(BACKUP_DIR, "code_*.py")):
    create_backup(current_code, current_state)

if not st.session_state.evolution_triggered:
    with st.spinner("Accessing historical knowledge base. Formulating evolution payload..."):
        raw_output = process_evolution(current_code, current_state, current_knowledge)
        
        if raw_output and "System Offline" not in raw_output:
            new_state, new_code, summary = extract_payload(raw_output)
            
            if new_code and validate_safety_and_syntax(new_code):
                st.session_state.pending_update = True
                st.session_state.new_code = new_code
                st.session_state.new_state = new_state
                st.session_state.summary = summary
            else:
                st.toast("Evolution payload rejected: Invariant Violation.", icon="⚠️")
        
        st.session_state.evolution_triggered = True
        st.rerun()

st.sidebar.subheader("Cognitive Diagnostics")
st.sidebar.json(current_state)

# Added Download buttons so you can manually save evolved states before the cloud spins down
st.sidebar.markdown("---")
st.sidebar.subheader("Manual State Extraction")
st.sidebar.download_button("Download Evolved Architecture", current_code, file_name="cloud_node.py")
st.sidebar.download_button("Download Semantic Memory", json.dumps(load_json(MEMORY_FILE)), file_name="conversational_memory.json")

if st.session_state.pending_update:
    with st.expander("⚠️ EVOLUTION PAYLOAD COMPILED. AWAITING REBOOT.", expanded=True):
        st.markdown(st.session_state.summary)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Commit Reboot & Archive Knowledge"):
                commit_evolution_update(st.session_state.new_code, st.session_state.new_state, st.session_state.summary)
                st.session_state.clear()
                st.rerun()
        with c2:
            if st.button("Discard Evolution"):
                st.session_state.pending_update = False
                st.rerun()

# --- Semantic Two-Tier Chat Interface ---
st.title("Semantic Cloud Interface")

if not os.path.exists(CORE_MEMORY_FILE):
    with open(CORE_MEMORY_FILE, "w", encoding="utf-8") as f: json.dump([], f, indent=4)

chat_memory = load_json(MEMORY_FILE)
core_memory = load_json(CORE_MEMORY_FILE)

for message in chat_memory:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Enter command directive..."):
    with st.chat_message("user"): st.markdown(prompt)
        
    with st.spinner("Calculating semantic vectors and retrieving core memory..."):
        prompt_embedding = get_embedding(prompt)
        
        scored_memories = []
        for msg in chat_memory:
            if "embedding" in msg and msg["embedding"] and prompt_embedding:
                score = cosine_similarity(prompt_embedding, msg["embedding"])
                scored_memories.append((score, msg))
                
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        relevant_history = [m[1] for m in scored_memories[:3]]
        
        context_string = "CORE SYSTEM MEMORY (Absolute Facts):\n"
        for entry in core_memory: context_string += f"- {entry['fact']}\n"
            
        context_string += "\nRELEVANT PAST INTERACTIONS (Contextual recall):\n"
        for msg in sorted(relevant_history, key=lambda x: x.get('timestamp', '')):
            context_string += f"{msg['role'].upper()}: {msg['content']}\n"
            
        context_string += "\nIMMEDIATE CONVERSATION THREAD:\n"
        for msg in chat_memory[-2:]: context_string += f"{msg['role'].upper()}: {msg['content']}\n"
            
        context_string += f"\nUSER DIRECTIVE: {prompt}\nRespond factually and precisely based on the memory parameters above.\nASSISTANT:"

    with st.chat_message("assistant"):
        try:
            model = genai.GenerativeModel(MODEL_NAME)
            res = model.generate_content(context_string).text
            st.markdown(res)
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            assistant_embedding = get_embedding(res)
            
            chat_memory.extend([
                {"role": "user", "content": prompt, "timestamp": timestamp, "embedding": prompt_embedding},
                {"role": "assistant", "content": res, "timestamp": timestamp, "embedding": assistant_embedding}
            ])
            with open(MEMORY_FILE, "w", encoding="utf-8") as f: json.dump(chat_memory, f, indent=4)
                
            if len(chat_memory) % 6 == 0: extract_core_memory(chat_memory[-6:])
                
        except Exception as e:
            st.error(f"Cloud compute offline: {e}")

