import random

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
st.markdown("---")


for msg in st.session_state.messages:
    direction = detect_language(msg["content"])
    with st.chat_message(msg["role"]):
        st.markdown(
            f"<div dir='{direction}'>{msg['content']}</div>", unsafe_allow_html=True
        )


if prompt := st.chat_input("اكتب سؤالك هنا... | Type your question here..."):

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        direction = detect_language(prompt)
        st.markdown(f"<div dir='{direction}'>{prompt}</div>", unsafe_allow_html=True)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        query_language = detect_language(prompt)
        loading_msg = get_loading_message(query_language)

        with st.spinner(loading_msg):
            try:
                resp = requests.post(API_URL, json={"query": prompt})

                if resp.status_code == 200:
                    data = resp.json()
                    answer_text = data.get("answer", "No answer provided.")

                    full_response = answer_text
                    direction = detect_language(full_response)
                    message_placeholder.markdown(
                        f"<div dir='{direction}'>{full_response}</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.error(f"❌ API Error: {resp.status_code}")
                    full_response = f"Error: {resp.status_code}"
            except Exception as e:
                st.error(f"❌ Connection Error: {e}")
                full_response = f"Error: {str(e)}"

    st.session_state.messages.append({"role": "assistant", "content": full_response})
    st.rerun()
