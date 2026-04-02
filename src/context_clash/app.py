import streamlit as st
import ollama
import time

# --- Page Configuration ---
st.set_page_config(
    page_title="Context-Clash: Neural Showdown",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom Styling ---
st.markdown("""
<style>
    .stChatMessage { border-radius: 15px; padding: 10px; margin-bottom: 10px; }
    .metric-container { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e6e6e6; margin-bottom: 10px; }
    .stButton > button { border-radius: 8px; }
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

# --- Sidebar: Arena Controls & Stats ---
with st.sidebar:
    st.title("🛡️ Clash Controls")
    
    st.subheader("📊 Session Statistics")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Tokens", f"{st.session_state.total_tokens:,}")
    with col2:
        st.metric("Speed", f"{st.session_state.last_speed:.2f} t/s")
    
    usage_pct = min(st.session_state.total_tokens / st.session_state.context_limit, 1.0)
    st.write(f"**Context Saturation:** {usage_pct*100:.1f}%")
    st.progress(usage_pct)

    st.divider()
    
    st.subheader("Model Selection")
    local_models = get_local_models()
    ai1_model = st.selectbox("AI 1 Model", local_models, index=0)
    ai2_model = st.selectbox("AI 2 Model", local_models, index=min(1, len(local_models)-1))
    
    if st.button("🔄 Refresh Model List"):
        st.rerun()

    st.divider()
    
    st.subheader("Generation Settings")
    # Restored 'help' parameter
    verbosity = st.select_slider(
        "Response Verbosity:",
        options=["Short", "Medium", "Long", "Uncapped"],
        value="Medium",
        help="Controls the 'Soft Limit' (what the AI is told to write) and the 'Hard Limit' (where the engine cuts it off)."
    )
    
    verbosity_config = {
        "Short": {"limit": 100, "note": "Keep your response extremely brief (1-2 sentences maximum)."},
        "Medium": {"limit": 250, "note": "Provide a concise response (about 1 paragraph)."},
        "Long": {"limit": 500, "note": "Provide a detailed, expansive response with multiple points."},
        "Uncapped": {"limit": -1, "note": "Feel free to be as verbose as you like."}
    }
    
    current_config = verbosity_config[verbosity]
    max_tokens = current_config["limit"]
    length_instruction = current_config["note"]

    st.divider()
    
    st.subheader("Personas")
    ai1_persona = st.text_area("AI 1 Persona:", "You are a grumpy old wizard who hates technology.")
    ai2_persona = st.text_area("AI 2 Persona:", "You are a hyper-enthusiastic, passive-aggressive tech support agent.")
    
    st.divider()
    
    max_turns = st.slider("Max Clash Turns:", 2, 100, 20)
    
    if st.button("🔥 Reset Clash", use_container_width=True):
        st.session_state.history, st.session_state.turn_count, st.session_state.total_tokens = [], 0, 0
        st.session_state.battle_started, st.session_state.paused, st.session_state.last_speed = False, True, 0.0
        st.rerun()

# --- Main Interface ---
st.title("🤖 Context-Clash: Neural Showdown")
st.caption("A pausable debate arena with identity-anchoring and real-time streaming.")

# Display Chat History
for msg in st.session_state.history:
    avatar = "🧙‍♂️" if "AI 1" in msg["role"] else ("🤖" if "AI 2" in msg["role"] else "👤")
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# Determining turns
is_ai1_turn = st.session_state.turn_count % 2 == 0
upcoming_label = "AI 1" if is_ai1_turn else "AI 2"

# --- LOGIC: Interaction Flow ---

if not st.session_state.battle_started:
    st.info("Arena Ready. Set the first topic.")
    seed = st.text_input("First Topic:", placeholder="e.g., Is a hotdog a sandwich?")
    if st.button("Initiate Clash") and seed:
        st.session_state.history.append({"role": "User Trigger", "content": seed})
        st.session_state.battle_started, st.session_state.paused = True, False
        st.rerun()

elif not st.session_state.paused and st.session_state.turn_count < max_turns:
    label, rival_label = ("AI 1", "AI 2") if is_ai1_turn else ("AI 2", "AI 1")
    model, persona = (ai1_model, ai1_persona) if is_ai1_turn else (ai2_model, ai2_persona)
    rival_persona = ai2_persona if is_ai1_turn else ai1_persona
    
    # --- REINFORCED IDENTITY ANCHORING ---
    messages = [
        {
            "role": "system", 
            "content": (
                f"You are {label}. Your character is: {persona}\n"
                f"Your opponent is {rival_label} (who is: {rival_persona}).\n"
                f"LENGTH GOAL: {length_instruction}\n"
                f"STRICT RULE: Only speak as {label}. Do not describe {rival_label}'s actions or thoughts. Output ONLY dialogue."
            )
        }
    ]
    
    for m in st.session_state.history:
        if m["role"] == label:
            messages.append({"role": "assistant", "content": m["content"]})
        elif m["role"] == rival_label:
            messages.append({"role": "user", "content": f"Message from your rival {rival_label}: {m['content']}"})
        elif m["role"] == "User Trigger":
            messages.append({"role": "user", "content": f"The topic is: {m['content']}"})
        else:
            messages.append({"role": "user", "content": f"Moderator says: {m['content']}"})
    
    with st.chat_message(label, avatar="🧙‍♂️" if is_ai1_turn else "🤖"):
        placeholder = st.empty()
        full_response = ""
        try:
            start_time = time.perf_counter() 
            stream = ollama.chat(
                model=model, 
                messages=messages, 
                stream=True,
                options={"num_predict": max_tokens} if max_tokens > 0 else {}
            )
            
            token_count = 0
            for chunk in stream:
                content = chunk['message']['content']
                full_response += content
                token_count += 1
                placeholder.markdown(full_response + "▌")
            
            duration = time.perf_counter() - start_time
            
            # Remove any accidentally generated name tags
            if full_response.startswith(f"{label}:"):
                full_response = full_response[len(f"{label}:"):].strip()
            
            placeholder.markdown(full_response)
            
            # Stats updates
            st.session_state.total_tokens += token_count
            if duration > 0.05: 
                st.session_state.last_speed = token_count / duration
            
            st.session_state.history.append({"role": label, "content": full_response})
            st.session_state.turn_count += 1
            st.session_state.paused = True
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

elif st.session_state.paused and st.session_state.turn_count < max_turns:
    st.divider()
    st.subheader(f"⏸️ Intervention Mode (Next: {upcoming_label})")
    
    # Restored 'help' parameter
    mode = st.radio(
        "Action Identity:", 
        ["Moderator (Neutral)", f"Impersonate {upcoming_label} (Skip AI turn)"], 
        horizontal=True,
        help="Impersonating will record the response as coming from the AI itself, skipping its generation turn."
    )
    user_input = st.text_input("Enter your message:", key="heckle_input")
    
    c1, c2 = st.columns(2)
    if c1.button("Submit & Continue", use_container_width=True):
        if user_input:
            if "Impersonate" in mode:
                st.session_state.history.append({"role": upcoming_label, "content": user_input})
                st.session_state.turn_count += 1
            else:
                st.session_state.history.append({"role": "User Intervention", "content": user_input})
            st.session_state.paused = False
            st.rerun()
            
    if c2.button(f"Let {upcoming_label} Speak", use_container_width=True):
        st.session_state.paused = False
        st.rerun()

if st.session_state.turn_count >= max_turns:
    st.success("The clash has reached its turn limit. You can reset or save the transcript.")