import streamlit as st
import ollama
import time
import re
import hashlib

# --- Page Configuration ---
st.set_page_config(
    page_title="Context-Clash: Neural Showdown",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom Styling ---
st.markdown("""
<style>
    .stChatMessage { border-radius: 12px; padding: 15px; margin-bottom: 15px; border: 1px solid #f0f2f6; }
    .st-emotion-cache-1c7n2ka { background-color: #f8f9fa; }
    .metric-container { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e6e6e6; }
    /* Compact sidebar headers */
    .sidebar .stSubheader { margin-top: 0.5rem; margin-bottom: 0.2rem; }
</style>
""", unsafe_allow_html=True)

# --- Helper: Dynamic Model Fetching ---
def get_local_models():
    """Fetches a list of models currently installed in the local Ollama engine."""
    try:
        response = ollama.list()
        models = [m['model'] for m in response.get('models', [])]
        return models if models else ["llama3"]
    except Exception:
        return ["llama3"]

def get_emoji_for_persona(model, name, persona):
    """Asks the LLM to provide a single emoji that represents the persona."""
    # Ensure cache exists (fallback if called before init)
    if "emoji_cache" not in st.session_state:
        st.session_state.emoji_cache = {}
        
    # Generate a deterministic hash for the input parameters
    cache_key = hashlib.md5(f"{model}_{name}_{persona}".encode('utf-8')).hexdigest()
    
    # Return cached emoji if available
    if cache_key in st.session_state.emoji_cache:
        return st.session_state.emoji_cache[cache_key]

    prompt = (
        f"Context: You are characterizing '{name}' who is described as: {persona}\n"
        f"Task: Provide ONLY a single emoji character that best represents this persona.\n"
        f"Constraint: No text, no explanation, no markdown. Just the emoji itself."
    )
    try:
        response = ollama.generate(model=model, prompt=prompt, options={"num_predict": 10})
        raw_output = response['response'].strip()
        
        # Regex to find the first emoji in the string
        emoji_pattern = r'[\U00010000-\U0010ffff\u2600-\u26ff\u2700-\u27bf][\ufe0f]?'
        found = re.findall(emoji_pattern, raw_output)
        
        result = found[0] if found else "👤"
        st.session_state.emoji_cache[cache_key] = result
        return result
    except:
        return "👤"

# --- Session State Initialization ---
if "history" not in st.session_state:
    st.session_state.history = [] 
if "turn_count" not in st.session_state:
    st.session_state.turn_count = 0
if "paused" not in st.session_state:
    st.session_state.paused = True
if "battle_started" not in st.session_state:
    st.session_state.battle_started = False
if "total_tokens" not in st.session_state:
    st.session_state.total_tokens = 0
if "last_speed" not in st.session_state:
    st.session_state.last_speed = 0.0
if "context_limit" not in st.session_state:
    st.session_state.context_limit = 8192
if "emoji_cache" not in st.session_state:
    st.session_state.emoji_cache = {}

# --- Persistent Identity State ---
if "name_a" not in st.session_state:
    st.session_state.name_a = "Aristotle"
if "name_b" not in st.session_state:
    st.session_state.name_b = "Nietzsche"
if "persona_a" not in st.session_state:
    st.session_state.persona_a = "You are Aristotle. You value logic, empirical observation, and the Golden Mean. You argue with systematic rigor and reject radical skepticism."
if "persona_b" not in st.session_state:
    st.session_state.persona_b = "You are Friedrich Nietzsche. You value the Will to Power, the Ubermensch, and the transvaluation of all values. You speak in aphorisms and reject traditional morality and logic."

# --- Moderator Configuration ---
MODERATOR_NAME = "Moderator (You)"
MODERATOR_EMOJI = "🛂"
MODERATOR_PERSONA = "Human Oversight & Intervention"

# --- Sidebar: Arena Controls & Stats ---
with st.sidebar:
    st.title("⚖️ Arena Settings")
    
    # Section: Stats
    st.subheader("📊 Session Statistics")
    col_stat1, col_stat2 = st.columns(2)
    with col_stat1:
        st.metric("Total Tokens", f"{st.session_state.total_tokens:,}")
    with col_stat2:
        st.metric("Speed", f"{st.session_state.last_speed:.2f} t/s")
    
    usage_pct = min(st.session_state.total_tokens / st.session_state.context_limit, 1.0)
    st.write(f"**Context Saturation:** {usage_pct*100:.1f}%")
    st.progress(usage_pct)
    
    st.divider()
    
    # Section: Models
    st.subheader("Combatants")
    local_models = get_local_models()
    col_mod1, col_mod2 = st.columns(2)
    with col_mod1:
        model_a = st.selectbox("Model A", local_models, index=0)
    with col_mod2:
        model_b = st.selectbox("Model B", local_models, index=min(1, len(local_models)-1))
    
    if st.button("🔄 Refresh Model List"):
        st.rerun()

    st.divider()
    
    # Section: Names and Personas (Bound to session state)
    st.subheader("Identities")
    col_name1, col_name2 = st.columns(2)
    with col_name1:
        st.session_state.name_a = st.text_input("Name A", value=st.session_state.name_a)
    with col_name2:
        st.session_state.name_b = st.text_input("Name B", value=st.session_state.name_b)
    
    st.session_state.persona_a = st.text_area(
        f"{st.session_state.name_a} Persona:", 
        value=st.session_state.persona_a,
        height=100
    )
    
    st.session_state.persona_b = st.text_area(
        f"{st.session_state.name_b} Persona:", 
        value=st.session_state.persona_b,
        height=100
    )
    
    st.divider()
    
    # Section: Configuration
    st.subheader("Configuration")
    col_cfg1, col_cfg2 = st.columns([2, 1])
    with col_cfg1:
        verbosity = st.select_slider(
            "Verbosity:",
            options=["Concise", "Standard", "Verbose", "Uncapped"],
            value="Standard"
        )
    with col_cfg2:
        max_turns = st.number_input("Max Turns", min_value=2, max_value=200, value=20)
    
    v_map = {
        "Concise": {"limit": 150, "note": "Keep your response under 3 sentences."},
        "Standard": {"limit": 350, "note": "Provide a detailed technical/philosophical response (1-2 paragraphs)."},
        "Verbose": {"limit": 800, "note": "Provide a comprehensive analysis with multiple points."},
        "Uncapped": {"limit": -1, "note": "Feel free to be as expansive as you like."}
    }
    
    if st.button("🔥 Reset Clash", use_container_width=True):
        st.session_state.history = []
        st.session_state.turn_count = 0
        st.session_state.total_tokens = 0
        st.session_state.battle_started = False
        st.session_state.paused = True
        st.session_state.last_speed = 0.0
        st.rerun()

# Use localized names for the rest of the logic
name_a = st.session_state.name_a
name_b = st.session_state.name_b
persona_a = st.session_state.persona_a
persona_b = st.session_state.persona_b

# --- Main Interface ---
st.title("🤖 Context-Clash: Neural Showdown")

# Display Global Transcript
for msg in st.session_state.history:
    role = msg.get("role", "System")
    emoji = msg.get("emoji", "👤")
    avatar = emoji if re.search(r'[\U00010000-\U0010ffff\u2600-\u26ff\u2700-\u27bf]', emoji) else "👤"
    
    with st.chat_message(role, avatar=avatar):
        if msg.get("persona"):
            st.caption(msg["persona"])
        st.markdown(msg.get("content", ""))

# Turn Logic
is_a_turn = st.session_state.turn_count % 2 == 0
upcoming_label = name_a if is_a_turn else name_b

# --- LOGIC: Interaction Flow ---

if not st.session_state.battle_started:
    st.info("System Ready. Define the topic of the clash.")
    seed = st.text_input("Topic:", placeholder="e.g., The nature of morality in the modern world.")
    if st.button("Initiate Clash") and seed:
        st.session_state.history.append({
            "role": "System", 
            "content": seed, 
            "emoji": "📜", 
            "persona": "Global Context Topic"
        })
        st.session_state.battle_started, st.session_state.paused = True, False
        st.rerun()

elif not st.session_state.paused and st.session_state.turn_count < max_turns:
    active_name = name_a if is_a_turn else name_b
    rival_name = name_b if is_a_turn else name_a
    active_model = model_a if is_a_turn else model_b
    active_persona = persona_a if is_a_turn else persona_b
    rival_persona = persona_b if is_a_turn else persona_a
    
    # 1. GENERATE EMOJI FRESH FOR THIS TURN
    generated_emoji = get_emoji_for_persona(active_model, active_name, active_persona)
    active_emoji = generated_emoji if re.search(r'[\U00010000-\U0010ffff\u2600-\u26ff\u2700-\u27bf]', generated_emoji) else "👤"
    
    # 2. PERSPECTIVE-BASED HISTORY
    messages = [
        {
            "role": "system", 
            "content": (
                f"You are {active_name}.\n"
                f"CHARACTER PROFILE: {active_persona}\n"
                f"Your opponent is {rival_name} ({rival_persona}).\n"
                f"STRICT RULES:\n"
                f"1. ONLY speak as {active_name}. Never speak for {rival_name}.\n"
                f"2. {v_map[verbosity]['note']}\n"
                f"3. Do not break character. Do not be overly agreeable."
            )
        }
    ]
    
    for m in st.session_state.history:
        if m["role"] == "System":
            messages.append({"role": "user", "content": f"The topic is: {m['content']}"})
        elif m["role"] == active_name:
            messages.append({"role": "assistant", "content": m["content"]})
        elif m["role"] == rival_name:
            messages.append({"role": "user", "content": f"{rival_name} says: {m['content']}"})
        elif m["role"] == MODERATOR_NAME:
            messages.append({"role": "user", "content": f"Moderator says: {m['content']}"})

    with st.chat_message(active_name, avatar=active_emoji):
        st.caption(active_persona)
        placeholder = st.empty()
        full_response = ""
        try:
            start_time = time.perf_counter() 
            max_toks = v_map[verbosity]["limit"]
            stream = ollama.chat(
                model=active_model, 
                messages=messages, 
                stream=True,
                options={"num_predict": max_toks} if max_toks > 0 else {}
            )
            
            token_count = 0
            for chunk in stream:
                content = chunk['message']['content']
                full_response += content
                token_count += 1
                placeholder.markdown(full_response + "▌")
            
            duration = time.perf_counter() - start_time
            if full_response.lower().startswith(f"{active_name.lower()}:"):
                full_response = full_response[len(active_name)+1:].strip()
            
            placeholder.markdown(full_response)
            
            st.session_state.total_tokens += token_count
            if duration > 0.1: 
                st.session_state.last_speed = token_count / duration
            
            st.session_state.history.append({
                "role": active_name, 
                "content": full_response,
                "persona": active_persona,
                "emoji": active_emoji
            })
            st.session_state.turn_count += 1
            st.session_state.paused = True
            st.rerun()
        except Exception as e:
            st.error(f"Ollama Error: {e}")

elif st.session_state.paused and st.session_state.turn_count < max_turns:
    st.divider()
    st.subheader(f"Intervention (Next: {upcoming_label})")
    
    user_input = st.text_input("Heckle or Moderate:", key="mod_input")
    
    col_int1, col_int2, col_int3 = st.columns(3)
    
    # Button 1: Neutral Moderator Injection
    if col_int1.button("Inject as Moderator", use_container_width=True):
        if user_input:
            st.session_state.history.append({
                "role": MODERATOR_NAME, 
                "content": user_input,
                "emoji": MODERATOR_EMOJI,
                "persona": MODERATOR_PERSONA
            })
            st.session_state.paused = False
            st.rerun()
            
    # Button 2: Let AI Speak
    if col_int2.button(f"Let {upcoming_label} Speak", use_container_width=True):
        st.session_state.paused = False
        st.rerun()

    # Button 3: Impersonate upcoming AI (Skip AI Turn)
    if col_int3.button(f"Impersonate {upcoming_label}", use_container_width=True):
        if user_input:
            # Determine correct metadata for impersonated role
            imp_name = name_a if is_a_turn else name_b
            imp_model = model_a if is_a_turn else model_b
            imp_persona = persona_a if is_a_turn else persona_b
            
            # Generate emoji for the impersonation so UI is consistent
            imp_emoji = get_emoji_for_persona(imp_model, imp_name, imp_persona)
            
            st.session_state.history.append({
                "role": imp_name, 
                "content": user_input,
                "emoji": imp_emoji,
                "persona": imp_persona
            })
            st.session_state.turn_count += 1
            st.session_state.paused = False
            st.rerun()

if st.session_state.turn_count >= max_turns:
    st.success("The showdown has ended.")
    transcript = ""
    for m in st.session_state.history:
        transcript += f"[{m['role']} ({m.get('persona', 'N/A')})]\n{m['content']}\n\n"
    
    st.download_button(
        label="📥 Download Clash Transcript",
        data=transcript,
        file_name=f"clash_transcript_{int(time.time())}.txt",
        mime="text/plain"
    )