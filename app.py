import streamlit as st
from openai import OpenAI
from supabase import create_client
import os
import uuid
from datetime import datetime
import time

# --- 1. CONFIGURATION ---
# Try Streamlit secrets first, then environment variables
def get_secret(key, default=None):
    try:
        return st.secrets.get(key, os.environ.get(key, default))
    except:
        return os.environ.get(key, default)

GROQ_API_KEY = get_secret("GROQ_API_KEY")
SUPABASE_URL = get_secret("SUPABASE_URL", "https://cfsnpkuenfhdttsunknd.supabase.co")
SUPABASE_KEY = get_secret("SUPABASE_KEY")

# Initialize clients
client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 2. DATABASE FUNCTIONS ---
def get_all_chats():
    """Get all unique chat sessions"""
    try:
        response = supabase.table("chat_history").select("chat_id, created_at, content").order("created_at", desc=True).execute()
        chats = {}
        for row in response.data:
            chat_id = row.get("chat_id", "default")
            if chat_id not in chats:
                preview = row["content"][:30] + "..." if len(row["content"]) > 30 else row["content"]
                chats[chat_id] = {"preview": preview, "created_at": row["created_at"]}
        return chats
    except Exception as e:
        return {}

def load_chat_history(chat_id: str):
    """Load chat history for a specific chat from Supabase"""
    try:
        response = supabase.table("chat_history").select("*").eq("chat_id", chat_id).order("created_at", desc=False).execute()
        messages = []
        for row in response.data:
            messages.append({
                "role": row["role"], 
                "content": row["content"],
                "timestamp": row.get("created_at", "")
            })
        return messages
    except Exception as e:
        st.sidebar.warning(f"Could not load history: {e}")
        return []

def save_message(chat_id: str, role: str, content: str):
    """Save a message to Supabase"""
    try:
        timestamp = datetime.now().isoformat()
        supabase.table("chat_history").insert({
            "chat_id": chat_id,
            "role": role,
            "content": content,
            "created_at": timestamp
        }).execute()
        return timestamp
    except Exception as e:
        st.sidebar.warning(f"Could not save message: {e}")
        return None

def delete_chat(chat_id: str):
    """Delete a specific chat session"""
    try:
        supabase.table("chat_history").delete().eq("chat_id", chat_id).execute()
    except Exception as e:
        st.sidebar.warning(f"Could not delete chat: {e}")

# --- 3. PAGE CONFIG ---
st.set_page_config(
    page_title="Aman's Assistant",
    page_icon="🦣",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- 4. CUSTOM CSS (Enhanced with animations) ---
st.markdown("""
<style>
    /* Import modern font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Main app styling with animated gradient */
    .stApp {
        background: linear-gradient(180deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
        font-family: 'Inter', sans-serif;
        position: relative;
        overflow: hidden;
    }
    
    /* Animated particles background */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
            radial-gradient(2px 2px at 20px 30px, rgba(102, 126, 234, 0.4), transparent),
            radial-gradient(2px 2px at 40px 70px, rgba(118, 75, 162, 0.3), transparent),
            radial-gradient(1px 1px at 90px 40px, rgba(240, 147, 251, 0.4), transparent),
            radial-gradient(2px 2px at 130px 80px, rgba(102, 126, 234, 0.3), transparent),
            radial-gradient(1px 1px at 160px 120px, rgba(118, 75, 162, 0.4), transparent);
        background-size: 200px 200px;
        animation: sparkle 20s linear infinite;
        pointer-events: none;
        z-index: 0;
    }
    
    @keyframes sparkle {
        0% { transform: translateY(0); opacity: 1; }
        50% { opacity: 0.5; }
        100% { transform: translateY(-100vh); opacity: 1; }
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 4rem;
        max-width: 800px;
        position: relative;
        z-index: 1;
    }
    
    /* Title styling with enhanced glow */
    h1 {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700;
        font-size: 2.5rem !important;
        text-align: center;
        margin-bottom: 0.5rem !important;
        animation: glow 2s ease-in-out infinite alternate, float 3s ease-in-out infinite;
    }
    
    @keyframes glow {
        from { filter: drop-shadow(0 0 10px rgba(102, 126, 234, 0.5)); }
        to { filter: drop-shadow(0 0 25px rgba(118, 75, 162, 0.9)); }
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-5px); }
    }
    
    /* Subtitle with fade-in */
    .subtitle {
        text-align: center;
        color: #888;
        font-size: 0.95rem;
        margin-bottom: 2rem;
        animation: fadeIn 1s ease-out;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Chat messages with slide-in animation */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 16px !important;
        padding: 1rem !important;
        margin-bottom: 1rem !important;
        backdrop-filter: blur(10px);
        animation: slideIn 0.3s ease-out;
    }
    
    @keyframes slideIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* User message styling with gradient border */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%) !important;
        border: 1px solid rgba(102, 126, 234, 0.3) !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.1);
    }
    
    /* Assistant message styling with glow */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        box-shadow: 0 4px 15px rgba(118, 75, 162, 0.1);
    }
    
    /* Avatar styling with pulse animation */
    .stChatMessage [data-testid="chatAvatarIcon-user"],
    .stChatMessage [data-testid="chatAvatarIcon-assistant"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border-radius: 10px !important;
        animation: pulse 2s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { box-shadow: 0 0 0 0 rgba(102, 126, 234, 0.4); }
        50% { box-shadow: 0 0 0 8px rgba(102, 126, 234, 0); }
    }
    
    /* Message text */
    .stChatMessage p {
        color: #e0e0e0 !important;
        font-size: 1rem !important;
        line-height: 1.6 !important;
    }
    
    /* Timestamp styling */
    .timestamp {
        font-size: 0.7rem;
        color: #666;
        margin-top: 8px;
        text-align: right;
    }
    
    /* Chat input container with glow on focus */
    .stChatInput {
        border-radius: 25px !important;
    }
    
    [data-testid="stChatInput"] {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 25px !important;
        transition: all 0.3s ease;
    }
    
    [data-testid="stChatInput"]:focus-within {
        border-color: #667eea !important;
        box-shadow: 0 0 25px rgba(102, 126, 234, 0.4) !important;
        transform: scale(1.01);
    }
    
    /* Input text */
    [data-testid="stChatInput"] textarea {
        color: #ffffff !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    [data-testid="stChatInput"] textarea::placeholder {
        color: #666 !important;
    }
    
    /* Send button with hover effect */
    [data-testid="stChatInput"] button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border-radius: 50% !important;
        border: none !important;
        transition: all 0.3s ease;
    }
    
    [data-testid="stChatInput"] button:hover {
        transform: scale(1.15) rotate(15deg);
        box-shadow: 0 0 20px rgba(102, 126, 234, 0.6) !important;
    }
    
    /* Typing indicator animation */
    .typing-indicator {
        display: flex;
        align-items: center;
        gap: 5px;
        padding: 15px 20px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        margin-bottom: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .typing-dot {
        width: 8px;
        height: 8px;
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 50%;
        animation: typingBounce 1.4s ease-in-out infinite;
    }
    
    .typing-dot:nth-child(1) { animation-delay: 0s; }
    .typing-dot:nth-child(2) { animation-delay: 0.2s; }
    .typing-dot:nth-child(3) { animation-delay: 0.4s; }
    
    @keyframes typingBounce {
        0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
        30% { transform: translateY(-10px); opacity: 1; }
    }
    
    .typing-text {
        color: #888;
        font-size: 0.9rem;
        margin-left: 10px;
    }
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #667eea, #764ba2);
        border-radius: 3px;
    }
    
    /* Error message styling */
    .stAlert {
        background: rgba(255, 75, 75, 0.1) !important;
        border: 1px solid rgba(255, 75, 75, 0.3) !important;
        border-radius: 12px !important;
        animation: shake 0.5s ease-in-out;
    }
    
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-5px); }
        75% { transform: translateX(5px); }
    }
    
    /* Code blocks in responses */
    .stChatMessage code {
        background: rgba(0, 0, 0, 0.4) !important;
        color: #f093fb !important;
        padding: 2px 6px;
        border-radius: 4px;
    }
    
    .stChatMessage pre {
        background: rgba(0, 0, 0, 0.4) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
    }
    
    /* Sidebar styling with gradient */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d0d0d 0%, #1a1a2e 100%) !important;
    }
    
    [data-testid="stSidebar"] .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        transition: all 0.3s ease;
    }
    
    [data-testid="stSidebar"] .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }
    
    /* Welcome message styling */
    .welcome-card {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-radius: 20px;
        padding: 30px;
        text-align: center;
        margin: 20px 0;
        animation: fadeIn 0.5s ease-out;
    }
    
    .welcome-title {
        font-size: 1.5rem;
        color: #fff;
        margin-bottom: 10px;
    }
    
    .welcome-subtitle {
        color: #888;
        font-size: 0.95rem;
    }
    
    .suggestion-chips {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        justify-content: center;
        margin-top: 20px;
    }
    
    .chip {
        background: rgba(102, 126, 234, 0.2);
        border: 1px solid rgba(102, 126, 234, 0.4);
        border-radius: 20px;
        padding: 8px 16px;
        color: #e0e0e0;
        font-size: 0.85rem;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .chip:hover {
        background: rgba(102, 126, 234, 0.4);
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

# --- 5. SESSION STATE INITIALIZATION ---
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- SIDEBAR: Chat Management ---
with st.sidebar:
    st.markdown("### 🦣 Aman's Assistant")
    st.markdown("---")
    
    # New Chat button
    if st.button("✨ New Chat", use_container_width=True, type="primary"):
        st.session_state.current_chat_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 📜 Chat History")
    
    # Get all chats
    all_chats = get_all_chats()
    
    if all_chats:
        for chat_id, chat_info in all_chats.items():
            col1, col2 = st.columns([4, 1])
            
            with col1:
                is_current = chat_id == st.session_state.current_chat_id
                label = f"{'▶ ' if is_current else ''}{chat_info['preview']}"
                if st.button(label, key=f"chat_{chat_id}", use_container_width=True):
                    st.session_state.current_chat_id = chat_id
                    st.session_state.messages = load_chat_history(chat_id)
                    st.rerun()
            
            with col2:
                if st.button("🗑️", key=f"del_{chat_id}", help="Delete this chat"):
                    delete_chat(chat_id)
                    if chat_id == st.session_state.current_chat_id:
                        st.session_state.current_chat_id = str(uuid.uuid4())
                        st.session_state.messages = []
                    st.rerun()
    else:
        st.markdown("*No chat history yet*")
    
    st.markdown("---")
    
    # Download current chat
    if st.session_state.messages:
        chat_text = ""
        for msg in st.session_state.messages:
            role = "You" if msg["role"] == "user" else "Aman's Assistant"
            chat_text += f"{role}:\n{msg['content']}\n\n"
        
        st.download_button(
            label="📥 Download Chat",
            data=chat_text,
            file_name="chat_history.txt",
            mime="text/plain",
            use_container_width=True
        )

# --- 6. UI HEADER ---
st.title("🦣 Aman's Assistant")
st.markdown('<p class="subtitle">Powered by Llama 3.3 • Lightning fast responses ⚡</p>', unsafe_allow_html=True)

# Welcome message if no chat history
if not st.session_state.messages:
    st.markdown("""
    <div class="welcome-card">
        <div class="welcome-title">👋 Welcome!</div>
        <div class="welcome-subtitle">I'm your personal AI assistant. Ask me anything!</div>
        <div class="suggestion-chips">
            <span class="chip">💡 Explain something</span>
            <span class="chip">✍️ Help me write</span>
            <span class="chip">🧠 Brainstorm ideas</span>
            <span class="chip">🔧 Solve a problem</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Helper function to format timestamp
def format_timestamp(ts):
    if not ts:
        return ""
    try:
        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        return dt.strftime("%I:%M %p")
    except:
        return ""

# Display chat history with timestamps
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("timestamp"):
            st.markdown(f'<div class="timestamp">{format_timestamp(message["timestamp"])}</div>', unsafe_allow_html=True)

# --- 7. CHAT LOGIC ---
if prompt := st.chat_input("Ask me anything..."):
    # Save and display user message
    timestamp = datetime.now().isoformat()
    st.session_state.messages.append({
        "role": "user", 
        "content": prompt,
        "timestamp": timestamp
    })
    save_message(st.session_state.current_chat_id, "user", prompt)
    
    with st.chat_message("user"):
        st.markdown(prompt)
        st.markdown(f'<div class="timestamp">{format_timestamp(timestamp)}</div>', unsafe_allow_html=True)

    # Show typing indicator
    typing_placeholder = st.empty()
    typing_placeholder.markdown("""
    <div class="typing-indicator">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <span class="typing-text">Aman's Assistant is thinking...</span>
    </div>
    """, unsafe_allow_html=True)

    with st.chat_message("assistant"):
        try:
            # Clear typing indicator
            typing_placeholder.empty()
            
            stream = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                stream=True,
            )
            response = st.write_stream(stream)
            
            # Save and store assistant response
            response_timestamp = datetime.now().isoformat()
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response,
                "timestamp": response_timestamp
            })
            save_message(st.session_state.current_chat_id, "assistant", response)
            
            st.markdown(f'<div class="timestamp">{format_timestamp(response_timestamp)}</div>', unsafe_allow_html=True)
        
        except Exception as e:
            typing_placeholder.empty()
            st.error(f"⚠️ {e}")