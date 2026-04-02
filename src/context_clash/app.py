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
    .stChatMessage {
        border-radius: 15px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .metric-container {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #e6e6e6;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
if "history" not in st.session_state:
    st.session_state.history = []
if "turn_count" not in st.session_state:
    st.session_state.turn_count = 0
if "paused" not in st.session_state:
    st.session_state.paused = True
if "battle_started" not in st.session_state:
    st.session_state.battle_started = False

# Stats Tracking
if "total_tokens" not in st.session_state:
    st.session_state.total_tokens = 0
if "last_speed" not in st.session_state:
    st.session_state.last_speed = 0
if "context_limit" not in st.session_state:
    st.session_state.context_limit = 4096 

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
    if usage_pct > 0.8:
        st.warning("⚠️ Memory getting crowded!")

    st.divider()
    
    st.subheader("Model Selection")
    ai1_model = st.selectbox("AI 1 Model", ["llama3", "mistral", "phi3", "tinyllama"], index=0)
    ai2_model = st.selectbox("AI 2 Model", ["mistral", "llama3", "phi3", "tinyllama"], index=0)
    
    st.divider()
    
    st.subheader("Personas")
    ai1_persona = st.text_area("AI 1 Persona:", 
                                "You are a grumpy old wizard who hates technology and speaks in slightly archaic English.")
    ai2_persona = st.text_area("AI 2 Persona:", 
                                "You are a hyper-enthusiastic, passive-aggressive corporate tech support agent.")
    
    st.divider()
    
    max_turns = st.slider("Max Clash Turns:", 2, 100, 20)
    
    # --- Export Feature ---
    if st.session_state.history:
        transcript = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.history])
        st.download_button(
            label="💾 Save Transcript",
            data=transcript,
            file_name="context_clash_transcript.txt",
            mime="text/plain"
        )
    
    if st.button("🔥 Reset Clash", use_container_width=True):
        st.session_state.history = []
        st.session_state.turn_count = 0
        st.session_state.total_tokens = 0
        st.session_state.last_speed = 0
        st.session_state.paused = True
        st.session_state.battle_started = False
        st.rerun()

# --- Main Interface ---
st.title("🤖 Context-Clash: Neural Showdown")
st.caption("The ultimate pausable debate between two AI minds.")

# Display Chat History
for msg in st.session_state.history:
    avatar = "🧙‍♂️" if "AI 1" in msg["role"] else ("🤖" if "AI 2" in msg["role"] else "👤")
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# --- Logic: The Interaction Loop ---

if not st.session_state.battle_started:
    st.info("The arena is ready. Set the first topic.")
    seed_prompt = st.text_input("First Topic:", placeholder="e.g., Is a hotdog a sandwich?")
    if st.button("Initiate Clash"):
        st.session_state.history.append({"role": "User Trigger", "content": seed_prompt})
        st.session_state.battle_started = True
        st.session_state.paused = False
        st.rerun()

elif not st.session_state.paused and st.session_state.turn_count < max_turns:
    is_ai1 = st.session_state.turn_count % 2 == 0
    speaker_label = "AI 1" if is_ai1 else "AI 2"
    current_model = ai1_model if is_ai1 else ai2_model
    current_persona = ai1_persona if is_ai1 else ai2_persona
    
    last_message = st.session_state.history[-1]["content"]
    
    with st.chat_message(speaker_label, avatar="🧙‍♂️" if is_ai1 else "🤖"):
        with st.spinner(f"{speaker_label} is responding..."):
            try:
                start_time = time.time()
                
                response = ollama.chat(model=current_model, messages=[
                    {"role": "system", "content": f"{current_persona} Keep your replies concise and stay in character."},
                    {"role": "user", "content": last_message}
                ])
                
                end_time = time.time()
                duration = end_time - start_time
                
                reply = response['message']['content']
                in_tokens = response.get('prompt_eval_count', 0)
                out_tokens = response.get('eval_count', 0)
                
                st.session_state.total_tokens += (in_tokens + out_tokens)
                if duration > 0:
                    st.session_state.last_speed = out_tokens / duration
                
                st.markdown(reply)
                st.session_state.history.append({"role": speaker_label, "content": reply})
                st.session_state.turn_count += 1
                st.session_state.paused = True 
                st.rerun()
                
            except Exception as e:
                st.error(f"Error: {e}")

elif st.session_state.paused:
    st.divider()
    st.subheader("⏸️ Intervention / Heckler Mode")
    
    col1, col2 = st.columns([4, 1])
    with col1:
        user_input = st.text_input("Interject/Heckle:", placeholder="Say something to stir the pot...")
    with col2:
        st.write("") 
        if st.button("Inject Words", use_container_width=True):
            if user_input:
                st.session_state.history.append({"role": "User Intervention", "content": user_input})
                st.session_state.paused = False
                st.rerun()
        if st.button("Let AI Continue", use_container_width=True):
            st.session_state.paused = False
            st.rerun()

if st.session_state.turn_count >= max_turns:
    st.success("Clash ended. Maximum turns reached.")