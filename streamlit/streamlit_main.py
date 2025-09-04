import streamlit as st
import sys
import os
from datetime import datetime

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.agents.main_agent import MainAgent
from app.mongodb_manager import global_mongodb_manager
from app.embedding import EmbeddingManager


# Main Streamlit application for the GenAI SMS Chatbot. 
# This module provides a web-based interface for testing and demonstrating the multi-agent chatbot system. 





# ---------------- Page configuration ----------------
st.set_page_config(
    page_title="GenAI SMS Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- Custom CSS ----------------
st.markdown(
    """
    <style>
    /* Chat styling */
    .chat-message {
        padding: 1rem;
        border-radius: 0.75rem;
        margin-bottom: 1rem;
        font-size: 16px;
        line-height: 1.5;
    }
    .user-message {
        background-color: #1e88e5;
        border-left: 6px solid #1565c0;
        color: white;
    }
    .bot-message {
        background-color: #7b1fa2;
        border-left: 6px solid #4a148c;
        color: white;
    }
    .system-message {
        background-color: #f57c00;
        border-left: 6px solid #e65100;
        color: white;
        font-style: italic;
    }
    .registration-message {
        background-color: #4caf50;
        border-left: 6px solid #2e7d32;
        color: white;
        font-weight: 600;
    }
    /* Buttons */
    .stButton > button {
        width: 100%;
        background-color: #2196f3 !important;
        color: white !important;
        font-weight: 600;
    }
    .stButton > button:hover {
        background-color: #1976d2 !important;
    }
    /* Textarea */
    .stTextArea > div > div > textarea {
        background-color: #37474f !important;
        color: white !important;
        border-radius: 8px;
        font-size: 16px;
        padding: 1rem;
    }
    /* Headers */
    h1, h2, h3 {
        color: white !important;
        font-weight: 700 !important;
    }
    /* Right column as sidebar */
    [data-testid="column"]:nth-of-type(2) {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        justify-content: flex-start !important;
        margin-top: 0 !important;
        padding-left: 1rem;
        background-color: #2f2f2f;
        border-left: 2px solid #555;
        border-radius: 8px;
    }
    /* Make sidebar text white for readability */
    [data-testid="column"]:nth-of-type(2) * {
        color: #f5f5f5 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------- Initialization ----------------
def initialize_chatbot():
    """Initialize the chatbot system."""
    try:

        embedding_manager = EmbeddingManager()

        try:
            embedding_manager.run_embedding_pipeline()
        except Exception:
            pass  # fallback

        main_agent = MainAgent(mongodb_mgr=global_mongodb_manager)
        return main_agent
    except Exception as e:
        st.error(f"Failed to initialize chatbot: {str(e)}")
        return None

# ---------------- User message processing ----------------
def process_user_message(message: str):
    """Process a user message and add it to the conversation."""
    if not st.session_state.chatbot:
        st.error("Chatbot is not initialized. Please refresh the page.")
        return

    st.session_state.messages.append({
        "role": "user",
        "content": message,
        "timestamp": datetime.now()
    })

    try:
        response = st.session_state.chatbot.process_message(message)
        st.session_state.messages.append({
            "role": "assistant",
            "content": response.get("message", ""),
            "action": response.get("action", ""),
            "metadata": response.get("metadata", {}),
            "timestamp": datetime.now()
        })
    except Exception as e:
        st.session_state.messages.append({
            "role": "system",
            "content": f"Error processing message: {str(e)}",
            "timestamp": datetime.now()
        })

# ---------------- Sample questions ----------------
def show_sample_questions():
    sample_questions = [
        "What are the main responsibilities of this role?",
        "Do you offer remote work options?",
        "What's the interview process like?",
        "What technologies do you use?",
        "Is there room for growth and advancement?",
        "What's the team structure like?",
        "Do you provide training and development opportunities?"
    ]
    st.session_state.messages.append({
        "role": "system",
        "content": "**Sample questions you can ask:**\n" + "\n".join([f"• {q}" for q in sample_questions]),
        "timestamp": datetime.now()
    })

# ---------------- Main Application ----------------
def main():
    st.title("🤖 GenAI SMS Chatbot")
    st.markdown("**Multi-Agent Job Candidate Interaction System**")

    # ---------------- Session state ----------------
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'input_key' not in st.session_state:
        st.session_state.input_key = 0

   # ---------------- Chatbot initialization ----------------
    if "chatbot_initialized" not in st.session_state:
        st.session_state.chatbot_initialized = False

    if not st.session_state.chatbot_initialized:
        with st.spinner("Initializing chatbot..."):
            st.session_state.chatbot = initialize_chatbot()
            if not st.session_state.chatbot:
                st.error("❌ Initialization failed.")
                st.stop()

            # Trigger initial welcome message
            try:
                welcome_response = st.session_state.chatbot.process_message("hello")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": welcome_response.get("message", ""),
                    "action": welcome_response.get("action", ""),
                    "metadata": welcome_response.get("metadata", {}),
                    "timestamp": datetime.now()
                })
                st.session_state.chatbot_initialized = True  # ✅ mark as done
            except Exception as e:
                st.error(f"❌ Failed to get welcome message: {str(e)}")
                st.stop()

    # ---------------- Layout ----------------
    col1, col2 = st.columns([3, 1])


    # ---------------- Left Panel (Chat) ----------------
    with col1:
        # Container for chat messages + input
        chat_area = st.container()

        # Render all chat messages inside the container
        with chat_area:
            for msg in st.session_state.messages:
                role_class = {
                    "user": "user-message",
                    "assistant": "bot-message",
                    "system": "system-message",
                    "registration": "registration-message"
                }.get(msg["role"], "system-message")
                st.markdown(
                    f"""
                    <div class="chat-message {role_class}">
                        <strong>{msg['role'].capitalize()}:</strong> {msg['content']}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        # ---------------- Input Area ----------------
        last_action = st.session_state.messages[-1].get("action") if st.session_state.messages else None
        if last_action != "end":
            placeholder = "Type your message here..."
            user_input = st.text_area(
                "💬 Message",
                key=f"user_input_{st.session_state.input_key}",
                height=100,
                placeholder=placeholder
            )

            send_button = st.button("📤 Send", type="primary", use_container_width=True)

            # Process message if Send clicked
            if send_button and user_input.strip():
                process_user_message(user_input.strip())
                st.session_state.input_key += 1
                st.rerun()

            # ---------------- Smooth scroll + Enter-to-send ----------------
            st.markdown(
                f"""
                <script>
                const container = window.parent.document.querySelector('section[data-testid="stVerticalBlock"] div[style*="flex-direction: column"]');
                if(container) {{
                    // Scroll to bottom smoothly on load or rerun
                    container.scrollTo({{ top: container.scrollHeight, behavior: 'smooth' }});

                    // Keep input area visible while typing
                    const textareas = container.querySelectorAll('textarea');
                    textareas.forEach(ta => {{
                        ta.addEventListener('input', () => {{
                            container.scrollTo({{ top: container.scrollHeight, behavior: 'smooth' }});
                        }});

                        // Detect Enter key to send (Shift+Enter for newline)
                        ta.addEventListener('keydown', function(e) {{
                            if(e.key === 'Enter' && !e.shiftKey) {{
                                e.preventDefault();
                                const sendButton = window.parent.document.querySelector('button[kind="primary"]');
                                if(sendButton) sendButton.click();
                            }}
                        }});
                    }});
                }}
                </script>
                """,
                unsafe_allow_html=True
            )

        else:
            # Restart conversation
            if st.button("🔄 Restart", type="primary"):
                st.session_state.chatbot.reset_conversation()
                st.session_state.messages.clear()
                st.session_state.input_key = 0
                welcome_response = st.session_state.chatbot.process_message("hello")
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": welcome_response.get("message", ""),
                        "action": welcome_response.get("action", ""),
                        "metadata": welcome_response.get("metadata", {}),
                        "timestamp": datetime.now()
                    }
                )
                st.rerun()

    # ---------------- Right Panel (Sidebar/Stats) ----------------
    with col2:
        st.subheader("📋 System Status")
        last_msg = st.session_state.messages[-1] if st.session_state.messages else {}
        action = last_msg.get("action", "idle")
        if action == "end":
            st.warning("⚠️ Conversation Ended")
        else:
            st.success("✅ System Ready")

        # ---------------- Candidate Registration Info ----------------
        st.subheader("📝 Chat Info")
        main_agent_action = st.session_state.get("action", "Unknown")
        candidate_name = st.session_state.get("candidate_name", "Unknown")
        candidate_phone = st.session_state.get("candidate_phone", "Unknown")
        #is_returning = st.session_state.get("is_returning", False)
        registration_status = st.session_state.get("registration_step", "Unknown")
        interview_info = st.session_state.get("interview", {"date": None, "time": None})
        if isinstance(interview_info, dict) and "date" in interview_info and "time" in interview_info:
            interview_str = f"{interview_info['date']} {interview_info['time']}"
        else:
            interview_str = "Not scheduled"
        st.markdown(
            f"""
            - **Main Agent Action:** {main_agent_action}
            - **Name:** {candidate_name}
            - **Phone:** {candidate_phone}
            - **Registration Status:** {registration_status}
            """
        )

        # ---------------- Available Positions ----------------
        st.subheader("💼 Available Positions")
        positions = last_msg.get("metadata", {}).get("available_positions", [])
        positions = [p for p in positions if p['title'] != 'All Positions']
        if positions:
            for p in positions:
                st.markdown(f"**{p['title']}** - {p['company']} - {p['location']} - {p['type']}")
        else:
            st.markdown("**Python Developer** - TechCorp Solutions - Remote/Hybrid - Full-time")

        # ---------------- Chat Stats ----------------
        st.subheader("📊 Chat Stats")
        st.markdown(
            f"""
            - **Total Messages:** {len(st.session_state.messages)}
            - **User Messages:** {len([m for m in st.session_state.messages if m['role'] == 'user'])}
            - **Bot Messages:** {len([m for m in st.session_state.messages if m['role'] == 'assistant'])}
            """
        )

        # ---------------- Quick Actions ----------------
        st.subheader("⚡ Quick Actions")
        quick_actions = [
            ("👋 Greeting", "Hi!"),
            ("📅 Schedule", "I'd like to schedule an interview"),
            ("❓ Sample Questions", "show_samples")
        ]
        for label, msg in quick_actions:
            if st.button(label, key=f"quick_{label}"):
                if msg == "show_samples":
                    show_sample_questions()
                else:
                    process_user_message(msg)
                st.session_state.input_key += 1
                st.rerun()

if __name__ == "__main__":
    main()

# ---------------- End of File ----------------