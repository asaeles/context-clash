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
</style>
""", unsafe_allow_html=True)

# --- Helper: Dynamic Model Fetching ---
def get_local_models():
    """Fetches a list of models currently installed in the local Ollama engine."""
    try:
        response = ollama.list()
        # Extract model names from the response objects
        models = [m['model'] for m in response.get('models', [])]
        return models if models else ["llama3"] # Fallback if list is empty
    except Exception:
        return ["llama3"] # Fallback if Ollama service isn't reachable

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
    
    # --- Live Statistics Section ---
    st.subheader("📊 Session Statistics")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Tokens", f"{st.session_state.total_tokens:,}")
    with col2:
        st.metric("Speed", f"{st.session_state.last_speed:.1f} t/s")
    
    # Context Window Progress Bar
    usage_pct = min(st.session_state.total_tokens / st.session_state.context_limit, 1.0)
    st.write(f"**Context Saturation:** {usage_pct*100:.1f}%")
    st.progress(usage_pct)

    st.divider()
    
    # --- Dynamic Model Selection ---
    st.subheader("Model Selection")
    local_models = get_local_models()
    
    ai1_model = st.selectbox("AI 1 Model", local_models, index=0)
    ai2_model = st.selectbox("AI 2 Model", local_models, index=min(1, len(local_models)-1))
    
    if st.button("🔄 Refresh Model List"):
        st.rerun()

    st.divider()
    
    st.subheader("Personas")
    ai1_persona = st.text_area("AI 1 Persona:", "You are a grumpy old wizard who hates technology.")
    ai2_persona = st.text_area("AI 2 Persona:", "You are a hyper-enthusiastic, passive-aggressive tech support agent.")
    
    st.divider()
    
    max_turns = st.slider("Max Clash Turns:", 2, 100, 20)
    
    if st.session_state.history:
        transcript = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.history])
        st.download_button("💾 Save Transcript", transcript, "transcript.txt")
    
    if st.button("🔥 Reset Clash", use_container_width=True):
        st.session_state.history, st.session_state.turn_count, st.session_state.total_tokens = [], 0, 0
        st.session_state.battle_started, st.session_state.paused = False, True
        st.rerun()

# --- Main Interface ---
st.title("🤖 Context-Clash: Neural Showdown")
st.caption("The ultimate pausable debate between local AI minds.")

for msg in st.session_state.history:
    avatar = "🧙‍♂️" if "AI 1" in msg["role"] else ("🤖" if "AI 2" in msg["role"] else "👤")
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

if not st.session_state.battle_started:
    st.info("Arena Ready. Set the first topic.")
    seed = st.text_input("First Topic:", placeholder="e.g., Is a hotdog a sandwich?")
    if st.button("Initiate Clash") and seed:
        st.session_state.history.append({"role": "User Trigger", "content": seed})
        st.session_state.battle_started, st.session_state.paused = True, False
        st.rerun()

elif not st.session_state.paused and st.session_state.turn_count < max_turns:
    is_ai1 = st.session_state.turn_count % 2 == 0
    label, model, persona = ("AI 1", ai1_model, ai1_persona) if is_ai1 else ("AI 2", ai2_model, ai2_persona)
    
    last_msg = st.session_state.history[-1]["content"]
    
    with st.chat_message(label, avatar="🧙‍♂️" if is_ai1 else "🤖"):
        with st.spinner(f"{label} is thinking..."):
            try:
                start = time.time()
                resp = ollama.chat(model=model, messages=[
                    {"role": "system", "content": f"{persona} Keep it concise."},
                    {"role": "user", "content": last_msg}
                ])
                dur = time.time() - start
                
                reply = resp['message']['content']
                tokens = resp.get('prompt_eval_count', 0) + resp.get('eval_count', 0)
                
                st.session_state.total_tokens += tokens
                if dur > 0: st.session_state.last_speed = resp.get('eval_count', 0) / dur
                
                st.markdown(reply)
                st.session_state.history.append({"role": label, "content": reply})
                st.session_state.turn_count += 1
                st.session_state.paused = True
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

elif st.session_state.paused:
    st.divider()
    st.subheader("⏸️ Intervention Mode")
    user_input = st.text_input("Heckle/Interject:", key="heckle")
    c1, c2 = st.columns(2)
    if c1.button("Inject & Continue"):
        if user_input:
            st.session_state.history.append({"role": "User Intervention", "content": user_input})
            st.session_state.paused = False
            st.rerun()
    if c2.button("Let AI Continue"):
        st.session_state.paused = False
        st.rerun()