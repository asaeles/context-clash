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
    .identity-tag { font-size: 0.8em; color: #666; margin-bottom: 4px; }
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
    st.session_state.last_speed = 0
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
        st.metric("Speed", f"{st.session_state.last_speed:.1f} t/s")
    
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
    verbosity = st.select_slider(
        "Response Verbosity:",
        options=["Short", "Medium", "Long", "Uncapped"],
        value="Medium"
    )
    verbosity_map = {"Short": 50, "Medium": 150, "Long": 400, "Uncapped": -1}
    max_tokens = verbosity_map[verbosity]

    st.divider()
    
    st.subheader("Personas")
    ai1_persona = st.text_area("AI 1 (Wizard) Persona:", "You are a grumpy old wizard who hates technology.")
    ai2_persona = st.text_area("AI 2 (Support) Persona:", "You are a hyper-enthusiastic, passive-aggressive tech support agent.")
    
    st.divider()
    
    max_turns = st.slider("Max Clash Turns:", 2, 100, 20)
    
    if st.button("🔥 Reset Clash", use_container_width=True):
        st.session_state.history, st.session_state.turn_count, st.session_state.total_tokens = [], 0, 0
        st.session_state.battle_started, st.session_state.paused = False, True
        st.rerun()

# --- Main Interface ---
st.title("🤖 Context-Clash: Neural Showdown")

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
    
    # --- IDENTITY ANCHORING FIX ---
    messages = [
        {
            "role": "system", 
            "content": (
                f"You are {label}. Your character description is: {persona}\n"
                f"You are currently debating your rival, {rival_label} (who is: {rival_persona}).\n"
                "STRICT RULE: Only speak for yourself. Do not summarize or act as your rival. "
                "Output ONLY your character's dialogue."
            )
        }
    ]
    
    for m in st.session_state.history:
        if m["role"] == label:
            messages.append({"role": "assistant", "content": m["content"]})
        elif m["role"] == rival_label:
            # We explicitly label the rival's message with their identity to prevent character bleed
            messages.append({"role": "user", "content": f"Message from your rival {rival_label}: {m['content']}"})
        elif m["role"] == "User Trigger":
            messages.append({"role": "user", "content": f"The Moderator set the topic as: {m['content']}"})
        else:
            messages.append({"role": "user", "content": f"A Moderator interjects: {m['content']}"})
    
    with st.chat_message(label, avatar="🧙‍♂️" if is_ai1_turn else "🤖"):
        placeholder = st.empty()
        full_response = ""
        try:
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
            
            # Clean up potential role-play hallucinations
            if full_response.startswith(f"{label}:"):
                full_response = full_response[len(f"{label}:"):].strip()
            
            placeholder.markdown(full_response)
            st.session_state.total_tokens += token_count
            st.session_state.history.append({"role": label, "content": full_response})
            st.session_state.turn_count += 1
            st.session_state.paused = True
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

elif st.session_state.paused:
    st.divider()
    st.subheader(f"⏸️ Intervention Mode (Next up: {upcoming_label})")
    
    mode = st.radio(
        "Choose your action identity:",
        ["Moderator (Neutral)", f"Impersonate {upcoming_label} (Skip AI turn)"],
        horizontal=True,
        help="Impersonating will record the response as the AI itself, skipping its generation turn."
    )
    
    user_input = st.text_input("Enter your words:", key="heckle_input")
    
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("Submit Response", use_container_width=True):
            if user_input:
                if "Impersonate" in mode:
                    st.session_state.history.append({"role": upcoming_label, "content": user_input})
                    st.session_state.turn_count += 1
                else:
                    st.session_state.history.append({"role": "User Intervention", "content": user_input})
                st.session_state.paused = False
                st.rerun()
                
    with c2:
        if st.button(f"Let {upcoming_label} Speak", use_container_width=True):
            st.session_state.paused = False
            st.rerun()