import streamlit as st
from openai import OpenAI
from supabase import create_client
import os
import uuid
from datetime import datetime

# --- 1. CONFIGURATION ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://cfsnpkuenfhdttsunknd.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNmc25wa3VlbmZoZHR0c3Vua25kIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA0NjY5MDUsImV4cCI6MjA4NjA0MjkwNX0.bv0QELFBOwhB1wJKvCL_iDHqrKJClbS1YJJcoLOG3rA")

# --- 2. PAGE CONFIG (must be first Streamlit command) ---
st.set_page_config(
    page_title="Aman's Assistant",
    page_icon="🦣",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Initialize clients
@st.cache_resource
def init_clients():
    client = OpenAI(
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1",
    )
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    return client, supabase

client, supabase = init_clients()

# --- 3. DATABASE FUNCTIONS ---
@st.cache_data(ttl=5)
def get_all_chats():
    """Get all unique chat sessions"""
    try:
        response = supabase.table("chat_history").select("chat_id, created_at, content, role").order("created_at", desc=True).execute()
        chats = {}
        for row in response.data:
            chat_id = row.get("chat_id", "default")
            if chat_id and chat_id not in chats:
                # Use first user message as title preview
                if row["role"] == "user":
                    preview = row["content"][:35] + "..." if len(row["content"]) > 35 else row["content"]
                    chats[chat_id] = {"preview": preview, "created_at": row["created_at"]}
        return chats
    except Exception:
        return {}

def load_chat_history(chat_id: str):
    """Load chat history for a specific chat"""
    try:
        response = supabase.table("chat_history").select("*").eq("chat_id", chat_id).order("created_at", desc=False).execute()
        return [{"role": row["role"], "content": row["content"]} for row in response.data]
    except Exception:
        return []

def save_message(chat_id: str, role: str, content: str):
    """Save a message to database"""
    try:
        supabase.table("chat_history").insert({
            "chat_id": chat_id,
            "role": role,
            "content": content,
            "created_at": datetime.now().isoformat()
        }).execute()
        get_all_chats.clear()  # Clear cache to refresh chat list
    except Exception:
        pass

def delete_chat(chat_id: str):
    """Delete a specific chat session"""
    try:
        supabase.table("chat_history").delete().eq("chat_id", chat_id).execute()
        get_all_chats.clear()  # Clear cache
    except Exception:
        pass

# --- 4. CUSTOM CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    .stApp {
        background: linear-gradient(180deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
        font-family: 'Inter', sans-serif;
    }
    
    #MainMenu, footer, .stDeployButton {display: none;}
    
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 4rem;
        max-width: 800px;
    }
    
    h1 {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700;
        font-size: 2.5rem !important;
        text-align: center;
        margin-bottom: 0.5rem !important;
    }
    
    .subtitle {
        text-align: center;
        color: #888;
        font-size: 0.95rem;
        margin-bottom: 2rem;
    }
    
    .stChatMessage {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 16px !important;
        padding: 1rem !important;
        margin-bottom: 1rem !important;
    }
    
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%) !important;
        border: 1px solid rgba(102, 126, 234, 0.3) !important;
    }
    
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    .stChatMessage p {
        color: #e0e0e0 !important;
        font-size: 1rem !important;
        line-height: 1.6 !important;
    }
    
    [data-testid="stChatInput"] {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 25px !important;
    }
    
    [data-testid="stChatInput"]:focus-within {
        border-color: #667eea !important;
        box-shadow: 0 0 20px rgba(102, 126, 234, 0.3) !important;
    }
    
    [data-testid="stChatInput"] textarea {
        color: #ffffff !important;
    }
    
    [data-testid="stChatInput"] button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border-radius: 50% !important;
        border: none !important;
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d0d0d 0%, #1a1a2e 100%) !important;
    }
    
    [data-testid="stSidebar"] .stButton > button {
        background: rgba(102, 126, 234, 0.2) !important;
        color: white !important;
        border: 1px solid rgba(102, 126, 234, 0.4) !important;
        border-radius: 8px !important;
        transition: all 0.2s !important;
    }
    
    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(102, 126, 234, 0.4) !important;
        border-color: #667eea !important;
    }
    
    .chat-btn {
        text-align: left !important;
        font-size: 0.85rem !important;
    }
    
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(102, 126, 234, 0.5); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# --- 5. SESSION STATE ---
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 6. SIDEBAR ---
with st.sidebar:
    st.markdown("## 🦣 Aman's Assistant")
    st.markdown("---")
    
    # New Chat button
    if st.button("✨ New Chat", use_container_width=True):
        st.session_state.current_chat_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 📜 Chat History")
    
    # Get all chats
    all_chats = get_all_chats()
    
    if all_chats:
        for chat_id, chat_info in list(all_chats.items())[:10]:  # Show max 10 chats
            col1, col2 = st.columns([5, 1])
            
            is_current = chat_id == st.session_state.current_chat_id
            
            with col1:
                label = f"{'▶ ' if is_current else ''}{chat_info['preview']}"
                if st.button(label, key=f"chat_{chat_id}", use_container_width=True):
                    st.session_state.current_chat_id = chat_id
                    st.session_state.messages = load_chat_history(chat_id)
                    st.rerun()
            
            with col2:
                if st.button("🗑️", key=f"del_{chat_id}", help="Delete"):
                    delete_chat(chat_id)
                    if chat_id == st.session_state.current_chat_id:
                        st.session_state.current_chat_id = str(uuid.uuid4())
                        st.session_state.messages = []
                    st.rerun()
    else:
        st.caption("No chat history yet")
    
    st.markdown("---")
    
    # Download current chat
    if st.session_state.messages:
        chat_text = "\n\n".join([
            f"{'You' if m['role'] == 'user' else 'Assistant'}:\n{m['content']}"
            for m in st.session_state.messages
        ])
        st.download_button("📥 Download Chat", chat_text, "chat.txt", use_container_width=True)

# --- 7. MAIN UI ---
st.title("🦣 Aman's Assistant")
st.markdown('<p class="subtitle">Powered by Llama 3.3 • Lightning fast ⚡</p>', unsafe_allow_html=True)

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 8. CHAT LOGIC ---
if prompt := st.chat_input("Ask me anything..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_message(st.session_state.current_chat_id, "user", prompt)
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            stream = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                stream=True,
            )
            response = st.write_stream(stream)
            
            st.session_state.messages.append({"role": "assistant", "content": response})
            save_message(st.session_state.current_chat_id, "assistant", response)
        
        except Exception as e:
            st.error(f"⚠️ {e}")
