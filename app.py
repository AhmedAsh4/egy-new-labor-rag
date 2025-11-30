import random
import time
from datetime import datetime

import requests
import streamlit as st

API_URL = "http://localhost:8000/ask"


st.set_page_config(
    page_title="AI Egyptian Labor Law",
    page_icon="⚖️",
    layout="centered",
    initial_sidebar_state="collapsed",
)


st.markdown(
    """
<style>
    /* Hide sidebar */
    [data-testid="stSidebar"] {
        display: none;
    }
    
    /* Main container */
    .main {
        max-width: 900px;
        margin: 0 auto;
    }
    
    /* Center the title and header section */
    .block-container {
        padding-top: 2rem;
    }
    
    /* Chat message styling with theme support */
    .stChatMessage {
        border-radius: 16px;
        padding: 16px 20px;
        margin: 12px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    
    /* User message */
    .stChatMessage[data-testid="stChatMessageUser"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
    }
    
    .stChatMessage[data-testid="stChatMessageUser"] p {
        color: white !important;
    }
    
    /* Assistant message - adapts to theme */
    .stChatMessage[data-testid="stChatMessageAssistant"] {
        background-color: var(--background-color);
        border: 1px solid var(--secondary-background-color);
    }
    
    /* Title styling */
    .title-container {
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .title-container h1 {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        display: inline-block;
    }
    
    .gradient-text {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Caption styling */
    .caption-text {
        text-align: center;
        font-size: 1.1rem;
        margin-bottom: 1rem;
        opacity: 0.8;
    }
    
    /* Chat input styling */
    .stChatInput {
        border-radius: 25px;
    }
    
    /* Spinner text */
    .stSpinner > div {
        text-align: center;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        margin-top: 1rem;
        margin-bottom: 2rem;
        opacity: 0.6;
        font-size: 0.9rem;
    }
    
    .footer a {
        color: inherit;
        text-decoration: none;
        border-bottom: 1px dotted;
    }
    
    .footer a:hover {
        opacity: 1;
        border-bottom: 1px solid;
    }
    
    /* Example questions styling */
    .example-card {
        background: var(--background-color);
        border: 1px solid var(--secondary-background-color);
        border-radius: 12px;
        padding: 12px 16px;
        margin: 8px 0;
        cursor: pointer;
        transition: all 0.3s ease;
        text-align: right;
    }
    
    .example-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border-color: #667eea;
    }
    
    /* Action buttons */
    .stButton button {
        border-radius: 8px;
        border: 1px solid var(--secondary-background-color);
        transition: all 0.2s ease;
    }
    
    /* Legal disclaimer */
    .disclaimer {
        background: rgba(255, 193, 7, 0.1);
        border-left: 4px solid #ffc107;
        padding: 12px 16px;
        margin: 16px 0;
        border-radius: 4px;
        font-size: 0.9rem;
    }
    
    /* Response metadata */
    .metadata {
        font-size: 0.85rem;
        opacity: 0.6;
        margin-top: 8px;
    }
    
    /* History item */
    .history-item {
        padding: 8px 12px;
        margin: 4px 0;
        border-radius: 8px;
        cursor: pointer;
        border: 1px solid transparent;
        transition: all 0.2s ease;
    }
    
    .history-item:hover {
        border-color: #667eea;
        background: var(--secondary-background-color);
    }
    
    /* Related questions */
    .related-questions {
        margin-top: 16px;
        padding-top: 12px;
        border-top: 1px solid var(--secondary-background-color);
    }
    
    .related-title {
        font-size: 0.9rem;
        opacity: 0.7;
        margin-bottom: 8px;
        font-weight: 600;
    }
    
    .related-btn {
        margin: 4px 0;
    }
</style>
""",
    unsafe_allow_html=True,
)


if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "مرحباً! أنا مساعدك القانوني الذكي. اسألني أي سؤال عن قانون العمل المصري.",
        }
    ]

if "search_history" not in st.session_state:
    st.session_state.search_history = []

if "show_examples" not in st.session_state:
    st.session_state.show_examples = True


# Load chat history from browser storage on first load
def load_from_storage():
    """Load chat history from session storage"""
    stored_messages = st.session_state.get("stored_messages", None)
    if stored_messages and len(st.session_state.messages) == 1:
        st.session_state.messages = stored_messages


def save_to_storage():
    """Save chat history to session storage"""
    st.session_state.stored_messages = st.session_state.messages


load_from_storage()


def detect_language(text):
    """Detect if text is primarily Arabic or English"""
    arabic_chars = sum(1 for c in text if "\u0600" <= c <= "\u06ff")
    total_chars = sum(1 for c in text if c.isalpha())
    return "rtl" if total_chars > 0 and arabic_chars / total_chars > 0.5 else "ltr"


def get_loading_message(language):
    """Get a random funny loading message based on language"""
    arabic_messages = [
        "🔍 بدور في القانون... لحظة بس",
        "⚖️ بقرأ المواد القانونية... استنى شوية",
        "📚 بفتش في الأوراق... ثانية واحدة",
        "🤓 بذاكر القانون عشانك... استنى",
        "📖 بدور على الإجابة الصح...",
        "🔎 بفحص كل حاجة بدقة... لحظة",
    ]

    english_messages = [
        "🔍 Searching through legal documents...",
        "⚖️ Reading the law... hang tight",
        "📚 Flipping through legal pages...",
        "🤓 Studying the law for you... one sec",
        "📖 Finding the perfect answer...",
        "🔎 Examining every detail carefully...",
    ]

    return random.choice(arabic_messages if language == "rtl" else english_messages)


def validate_input(text):
    """Validate user input before sending to API"""
    if not text or not text.strip():
        return False, "الرجاء إدخال سؤال | Please enter a question"
    if len(text.strip()) < 3:
        return False, "السؤال قصير جداً | Question too short"
    if len(text) > 500:
        return False, "السؤال طويل جداً | Question too long"
    return True, ""


def get_example_questions():
    """Return example questions in both languages"""
    return {
        "arabic": [
            "ما هي حقوق المرأة العاملة الحامل؟",
            "كم عدد أيام الإجازة السنوية للعامل؟",
            "ما هي شروط إنهاء عقد العمل؟",
            "ما هو الحد الأدنى للأجور؟",
        ],
        "english": [
            "What are the rights of pregnant working women?",
            "How many days of annual leave does a worker get?",
            "What are the conditions for terminating an employment contract?",
            "What is the minimum wage?",
        ],
    }


st.markdown(
    """
    <div class='title-container'>
        <h1>⚖️ <span class='gradient-text'>Egyptian Labor Law Assistant</span></h1>
    </div>
    <div class='footer'>
        Powered by <strong>Qwen3-8B</strong> & <strong>DeepSeek-V3</strong> | 
        Built by <a href='https://www.linkedin.com/in/ahmedashraaff/' target='_blank'>Ahmed Ashraf</a>
    </div>
    """,
    unsafe_allow_html=True,
)

# Legal Disclaimer
st.markdown(
    """
    <div class='disclaimer'>
        ⚠️ <strong>إخلاء مسؤولية قانونية:</strong><br>
        هذا المساعد يقدم معلومات قانونية فقط وليس استشارة قانونية. استشر محامياً للحصول على مشورة قانونية محددة.
        <br><br>
        ⚠️ <strong>Legal Disclaimer:</strong><br>
        This assistant provides legal information only, not legal advice. Consult a lawyer for specific legal counsel.
    </div>
    """,
    unsafe_allow_html=True,
)

# Action buttons row
col1, col2, col3 = st.columns([2, 2, 2])
with col1:
    if st.button("🗑️ مسح المحادثة | Clear Chat"):
        st.session_state.messages = [st.session_state.messages[0]]
        st.session_state.search_history = []
        st.session_state.show_examples = True
        save_to_storage()
        st.rerun()

with col2:
    if st.button("💡 أمثلة | Examples"):
        st.session_state.show_examples = not st.session_state.show_examples
        st.rerun()

with col3:
    if st.button("📜 السجل | History"):
        st.session_state.show_history = not st.session_state.get("show_history", False)
        st.rerun()

st.markdown("---")

# Show example questions if enabled
if st.session_state.show_examples and len(st.session_state.messages) == 1:
    examples = get_example_questions()
    st.markdown("#### 💡 جرب هذه الأسئلة | Try these questions:")
    cols = st.columns(2)

    for idx, question in enumerate(examples["arabic"][:2]):
        with cols[idx]:
            if st.button(question, key=f"ex_ar_{idx}", use_container_width=True):
                st.session_state.example_clicked = question
                st.rerun()

    for idx, question in enumerate(examples["english"][:2]):
        with cols[idx]:
            if st.button(question, key=f"ex_en_{idx}", use_container_width=True):
                st.session_state.example_clicked = question
                st.rerun()

    st.markdown("---")

# Show search history if enabled
if st.session_state.get("show_history", False) and st.session_state.search_history:
    st.markdown("#### 📜 سجل البحث | Search History:")
    for idx, item in enumerate(reversed(st.session_state.search_history[-5:])):
        if st.button(
            (
                f"🔍 {item['query'][:50]}..."
                if len(item["query"]) > 50
                else f"🔍 {item['query']}"
            ),
            key=f"hist_{idx}",
            use_container_width=True,
        ):
            st.session_state.history_clicked = item["query"]
            st.rerun()
    st.markdown("---")


for msg in st.session_state.messages:
    direction = detect_language(msg["content"])
    with st.chat_message(msg["role"]):
        st.markdown(
            f"<div dir='{direction}'>{msg['content']}</div>", unsafe_allow_html=True
        )

        # Show metadata for assistant messages
        if msg["role"] == "assistant" and "metadata" in msg:
            metadata = msg["metadata"]
            st.markdown(
                f"<div class='metadata'>⏱️ {metadata.get('response_time', 'N/A')}s | "
                f"🕒 {metadata.get('timestamp', '')}</div>",
                unsafe_allow_html=True,
            )

            # Feedback buttons
            col1, col2, col3 = st.columns([1, 1, 8])
            with col1:
                if st.button("👍", key=f"like_{metadata.get('timestamp', '')}"):
                    st.toast("شكراً لتقييمك! | Thanks for your feedback!", icon="✅")
            with col2:
                if st.button("👎", key=f"dislike_{metadata.get('timestamp', '')}"):
                    st.toast("شكراً لتقييمك! | Thanks for your feedback!", icon="✅")

            # Related questions
            if "related_questions" in metadata and metadata["related_questions"]:
                st.markdown(
                    "<div class='related-questions'><div class='related-title'>❓ أسئلة ذات صلة | Related Questions:</div></div>",
                    unsafe_allow_html=True,
                )
                for idx, rq in enumerate(metadata["related_questions"]):
                    rq_direction = detect_language(rq)
                    if st.button(
                        rq,
                        key=f"related_{metadata.get('timestamp', '')}_{idx}",
                        use_container_width=True,
                    ):
                        st.session_state.related_clicked = rq
                        st.rerun()


# Handle example question clicks
if "example_clicked" in st.session_state:
    prompt = st.session_state.example_clicked
    del st.session_state.example_clicked
elif "history_clicked" in st.session_state:
    prompt = st.session_state.history_clicked
    del st.session_state.history_clicked
elif "related_clicked" in st.session_state:
    prompt = st.session_state.related_clicked
    del st.session_state.related_clicked
else:
    prompt = st.chat_input("اكتب سؤالك هنا... | Type your question here...")

if prompt:
    # Validate input
    is_valid, error_msg = validate_input(prompt)
    if not is_valid:
        st.error(error_msg)
        st.stop()

    st.session_state.show_examples = False
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        direction = detect_language(prompt)
        st.markdown(f"<div dir='{direction}'>{prompt}</div>", unsafe_allow_html=True)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        query_language = detect_language(prompt)
        loading_msg = get_loading_message(query_language)

        # Track response time
        start_time = time.time()

        with st.spinner(loading_msg):
            try:
                resp = requests.post(API_URL, json={"query": prompt}, timeout=300)

                if resp.status_code == 200:
                    data = resp.json()
                    answer_text = data.get("answer", "No answer provided.")
                    related_questions = data.get("related_questions", [])

                    full_response = answer_text
                    direction = detect_language(full_response)

                    # Calculate response time
                    response_time = round(time.time() - start_time, 2)
                    timestamp = datetime.now().strftime("%H:%M")

                    message_placeholder.markdown(
                        f"<div dir='{direction}'>{full_response}</div>",
                        unsafe_allow_html=True,
                    )

                    # Add metadata
                    metadata = {
                        "response_time": response_time,
                        "timestamp": timestamp,
                        "related_questions": related_questions,
                    }

                    # Display metadata
                    st.markdown(
                        f"<div class='metadata'>⏱️ {response_time}s | 🕒 {timestamp}</div>",
                        unsafe_allow_html=True,
                    )

                    # Add feedback buttons
                    col1, col2, col3 = st.columns([1, 1, 8])
                    with col1:
                        if st.button("👍", key=f"like_new"):
                            st.toast(
                                "شكراً لتقييمك! | Thanks for your feedback!", icon="✅"
                            )
                    with col2:
                        if st.button("👎", key=f"dislike_new"):
                            st.toast(
                                "شكراً لتقييمك! | Thanks for your feedback!", icon="✅"
                            )

                    # Display related questions
                    if related_questions:
                        st.markdown(
                            "<div class='related-questions'><div class='related-title'>❓ أسئلة ذات صلة | Related Questions:</div></div>",
                            unsafe_allow_html=True,
                        )
                        for idx, rq in enumerate(related_questions):
                            rq_direction = detect_language(rq)
                            if st.button(
                                rq,
                                key=f"related_new_{idx}",
                                use_container_width=True,
                            ):
                                st.session_state.related_clicked = rq
                                st.rerun()

                else:
                    st.error(f"❌ API Error: {resp.status_code}")
                    full_response = f"Error: {resp.status_code}"
                    metadata = {}
            except requests.Timeout:
                st.error("⏱️ انتهت مهلة الطلب | Request timed out")
                full_response = "Error: Timeout"
                metadata = {}
            except Exception as e:
                st.error(f"❌ Connection Error: {e}")
                full_response = f"Error: {str(e)}"
                metadata = {}

    # Save message with metadata
    message_data = {"role": "assistant", "content": full_response}
    if metadata:
        message_data["metadata"] = metadata

    st.session_state.messages.append(message_data)

    # Add to search history
    if full_response and not full_response.startswith("Error:"):
        st.session_state.search_history.append(
            {
                "query": prompt,
                "timestamp": datetime.now().isoformat(),
                "response_time": metadata.get("response_time", 0),
            }
        )

    # Save to storage
    save_to_storage()

    st.rerun()
