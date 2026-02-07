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
                # Use first message as title preview
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
            messages.append({"role": row["role"], "content": row["content"]})
        return messages
    except Exception as e:
        st.sidebar.warning(f"Could not load history: {e}")
        return []

def save_message(chat_id: str, role: str, content: str):
    """Save a message to Supabase"""
    try:
        supabase.table("chat_history").insert({
            "chat_id": chat_id,
            "role": role,
            "content": content,
            "created_at": datetime.now().isoformat()
        }).execute()
    except Exception as e:
        st.sidebar.warning(f"Could not save message: {e}")

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

# --- 4. CUSTOM CSS (Grok-inspired dark theme) ---
st.markdown("""
<style>
    /* Import modern font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Main app styling */
    .stApp {
        background: linear-gradient(180deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
        font-family: 'Inter', sans-serif;
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
    }
    
    /* Title styling */
    h1 {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700;
        font-size: 2.5rem !important;
        text-align: center;
        margin-bottom: 0.5rem !important;
        animation: glow 2s ease-in-out infinite alternate;
    }
    
    @keyframes glow {
        from { filter: drop-shadow(0 0 10px rgba(102, 126, 234, 0.5)); }
        to { filter: drop-shadow(0 0 20px rgba(118, 75, 162, 0.8)); }
    }
    
    /* Subtitle */
    .subtitle {
        text-align: center;
        color: #888;
        font-size: 0.95rem;
        margin-bottom: 2rem;
    }
    
    /* Chat messages container */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 16px !important;
        padding: 1rem !important;
        margin-bottom: 1rem !important;
        backdrop-filter: blur(10px);
    }
    
    /* User message styling */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%) !important;
        border: 1px solid rgba(102, 126, 234, 0.3) !important;
    }
    
    /* Assistant message styling */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    /* Avatar styling */
    .stChatMessage [data-testid="chatAvatarIcon-user"],
    .stChatMessage [data-testid="chatAvatarIcon-assistant"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border-radius: 10px !important;
    }
    
    /* Message text */
    .stChatMessage p {
        color: #e0e0e0 !important;
        font-size: 1rem !important;
        line-height: 1.6 !important;
    }
    
    /* Chat input container */
    .stChatInput {
        border-radius: 25px !important;
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
    
    /* Input text */
    [data-testid="stChatInput"] textarea {
        color: #ffffff !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    [data-testid="stChatInput"] textarea::placeholder {
        color: #666 !important;
    }
    
    /* Send button */
    [data-testid="stChatInput"] button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border-radius: 50% !important;
        border: none !important;
    }
    
    [data-testid="stChatInput"] button:hover {
        transform: scale(1.1);
        box-shadow: 0 0 15px rgba(102, 126, 234, 0.5) !important;
    }
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(102, 126, 234, 0.5);
        border-radius: 3px;
    }
    
    /* Error message styling */
    .stAlert {
        background: rgba(255, 75, 75, 0.1) !important;
        border: 1px solid rgba(255, 75, 75, 0.3) !important;
        border-radius: 12px !important;
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
    
    /* Spinner styling */
    .stSpinner > div {
        border-color: #667eea transparent transparent transparent !important;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d0d0d 0%, #1a1a2e 100%) !important;
    }
    
    [data-testid="stSidebar"] .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
    }
    
    /* Chat history items */
    .chat-item {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 8px;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .chat-item:hover {
        background: rgba(102, 126, 234, 0.2);
        border-color: rgba(102, 126, 234, 0.4);
    }
    
    .chat-item.active {
        background: rgba(102, 126, 234, 0.3);
        border-color: #667eea;
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
                # Make chat selectable
                is_current = chat_id == st.session_state.current_chat_id
                label = f"{'▶ ' if is_current else ''}{chat_info['preview']}"
                if st.button(label, key=f"chat_{chat_id}", use_container_width=True):
                    st.session_state.current_chat_id = chat_id
                    st.session_state.messages = load_chat_history(chat_id)
                    st.rerun()
            
            with col2:
                # Delete button
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

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 7. CHAT LOGIC ---
if prompt := st.chat_input("Ask me anything..."):
    # Save and display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_message(st.session_state.current_chat_id, "user", prompt)
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
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
            st.session_state.messages.append({"role": "assistant", "content": response})
            save_message(st.session_state.current_chat_id, "assistant", response)
        
        except Exception as e:
            st.error(f"⚠️ {e}")