import os
import json
from pathlib import Path
import streamlit as st
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except Exception:
    pass

from PyPDF2 import PdfReader
import docx
from collections import defaultdict
from processor import processor
from question_generator import generator
from utils import clean_text
from auth import init_auth_state, is_authenticated, get_current_user, logout, auth_db
from landing import show_landing_page
from oauth_handler import OAuthHandler

# Initialize authentication state
init_auth_state()

# ================= OAUTH CALLBACK HANDLER =================
# Handle Google OAuth callback
if "error" in st.query_params:
    oauth_error = st.query_params.get("error")
    st.error(f"Google Sign-In failed: {oauth_error}")
    if oauth_error == "redirect_uri_mismatch":
        st.info(f"Using client_id: {OAuthHandler.GOOGLE_CLIENT_ID}")
        st.info(f"Using redirect_uri: {OAuthHandler._get_google_redirect_uri()}")

if "code" in st.query_params and not st.session_state.get("authenticated"):
    # Streamlit query params can return list-like values; normalize to string
    auth_code = st.query_params.get("code")
    if isinstance(auth_code, list):
        auth_code = auth_code[0] if auth_code else None

    if auth_code:
        token_result = OAuthHandler.exchange_google_code_for_token(auth_code)
        if token_result.get("success"):
            user_info_result = OAuthHandler.get_google_user_info(token_result.get("access_token"))
            if user_info_result.get("success"):
                user_info = user_info_result["user_info"]
                email = user_info.get("email", "")
                name = user_info.get("name", "")

                login_result = auth_db.oauth_login_or_register(name, email)
                if not login_result.get("success"):
                    st.error("OAuth login/register failed.")
                    st.info(f"token_result: {token_result}")
                    st.info(f"user_info_result: {user_info_result}")
                    st.info(f"login_result: {login_result}")
                    st.stop()

                st.session_state.authenticated = True
                st.session_state.user_id = login_result.get("user_id")
                st.session_state.user_name = login_result.get("name")
                st.session_state.user_email = email
                st.session_state.session_token = login_result.get("session_token")

                # Remove code from URL, then rerun into authenticated app state
                st.query_params.clear()
                st.rerun()
            else:
                st.error("Failed to fetch Google user profile.")
                st.info(f"user_info_result: {user_info_result}")
        else:
            st.error("Failed to exchange Google authorization code.")
            st.info(f"token_result: {token_result}")

# Check if user is authenticated - if not, show landing page
if not is_authenticated():
    show_landing_page()
    st.stop()

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Study Buddy",
    page_icon="🧠",
    layout="wide"
)

# ================= THEME TOGGLE =================
if "theme" not in st.session_state:
    st.session_state.theme = "Dark"

theme_choice = st.sidebar.toggle("🌗 Dark Mode", value=True)

if theme_choice:
    st.session_state.theme = "Dark"
    bg_color = "#0A0E27"  # Darker, more sophisticated background
    card_color = "#1A1F3A"  # Darker card background
    text_color = "#E8E9F3"  # Lighter text for better contrast (WCAG AA compliant)
    accent_color = "#7C3AED"  # Purple accent
    border_color = "#2D3748"  # Subtle borders
else:
    st.session_state.theme = "Light"
    bg_color = "#F8F9FA"
    card_color = "#FFFFFF"
    text_color = "#1A202C"  # Darker text for light mode
    accent_color = "#7C3AED"
    border_color = "#E2E8F0"

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {bg_color};
        color: {text_color};
    }}
    
    /* Improve text contrast in dark mode */
    .stMarkdown {{
        color: {text_color};
    }}
    
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5 {{
        color: {text_color};
    }}
    
    /* Better button styling - aggressive overrides */
    .stButton > button {{
        color: {text_color} !important;
        border-color: {border_color} !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        background-color: {card_color} !important;
        border: 2px solid {accent_color} !important;
    }}
    
    .stButton > button > p {{
        color: {text_color} !important;
        font-weight: 700 !important;
        font-size: 16px !important;
    }}
    
    .stButton > button:hover {{
        color: {accent_color} !important;
        background-color: {bg_color} !important;
    }}
    
    /* File uploader button styling - multiple selectors to catch it */
    .stFileUploader button,
    .stFileUploader > div > button,
    .stFileUploader section button,
    div[data-testid="stFileUploader"] button,
    .stFileUploader section > label > div > button {{
        color: {text_color} !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        background-color: {card_color} !important;
        border: 2px solid {accent_color} !important;
    }}
    
    .stFileUploader button p,
    .stFileUploader > div > button p {{
        color: {text_color} !important;
        font-weight: 700 !important;
    }}
    
    .stFileUploader label {{
        color: {text_color} !important;
        font-weight: 600 !important;
    }}
    
    /* Reset button - sidebar */
    [data-testid="stSidebar"] .stButton > button {{
        color: {text_color} !important;
        background-color: {card_color} !important;
        border: 2px solid {accent_color} !important;
        font-weight: 700 !important;
    }}
    
    /* Improve input fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {{
        color: {text_color} !important;
        background-color: {card_color} !important;
    }}
    
    /* Better selectbox styling */
    .stSelectbox {{
        color: {text_color};
    }}
    
    /* Improved sidebar */
    [data-testid="stSidebar"] {{
        background-color: {bg_color};
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# ================= ABOUT SECTION STYLING =================
about_card_bg = "rgba(255, 253, 251, 0.78)" if st.session_state.theme == "Light" else "rgba(30, 23, 45, 0.78)"
about_border = "rgba(211, 139, 158, 0.36)" if st.session_state.theme == "Light" else "rgba(213, 165, 188, 0.32)"
about_shadow = "rgba(169, 103, 116, 0.24)" if st.session_state.theme == "Light" else "rgba(21, 8, 34, 0.38)"
about_muted = "rgba(77, 45, 53, 0.84)" if st.session_state.theme == "Light" else "rgba(232, 214, 225, 0.86)"

st.markdown(
    f"""
    <style>
    .about-card {{
        margin-top: 4px;
        border: 1px solid {about_border};
        border-radius: 24px;
        padding: 22px;
        background:
            radial-gradient(circle at 92% 12%, rgba(244, 177, 196, 0.2) 0%, rgba(244, 177, 196, 0) 34%),
            radial-gradient(circle at 10% 90%, rgba(249, 220, 208, 0.2) 0%, rgba(249, 220, 208, 0) 36%),
            {about_card_bg};
        box-shadow: 0 18px 48px {about_shadow};
        backdrop-filter: blur(7px);
    }}
    .about-name {{
        font-size: clamp(30px, 4vw, 42px);
        font-weight: 800;
        line-height: 1.05;
        margin: 0 0 8px 0;
        letter-spacing: -0.5px;
    }}
    .about-role {{
        display: inline-block;
        border-radius: 999px;
        border: 1px solid {about_border};
        padding: 7px 14px;
        font-size: 13px;
        font-weight: 700;
        margin-bottom: 10px;
        color: {about_muted};
        background: rgba(255,255,255,0.22);
    }}
    .about-copy {{
        margin: 0;
        font-size: 15px;
        line-height: 1.72;
        color: {about_muted};
    }}
    .about-metric {{
        display: inline-block;
        margin: 8px 8px 0 0;
        border-radius: 11px;
        border: 1px solid {about_border};
        padding: 7px 10px;
        font-size: 12px;
        font-weight: 700;
        color: {about_muted};
        background: rgba(255,255,255,0.22);
    }}
    .about-photo-wrap {{
        border-radius: 20px;
        border: 1px solid {about_border};
        padding: 8px;
        background: rgba(255,255,255,0.16);
    }}
    .about-note {{
        margin-top: 8px;
        font-size: 12px;
        opacity: 0.8;
    }}
    .about-top-cta {{
        display: flex;
        justify-content: flex-end;
        margin: 2px 0 10px 0;
    }}
    .about-top-link {{
        display: inline-block;
        padding: 9px 18px;
        border-radius: 999px;
        text-decoration: none;
        font-size: 13px;
        font-weight: 800;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        color: #ffffff;
        background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
        box-shadow: 0 8px 24px rgba(124, 58, 237, 0.35);
        border: 1px solid rgba(255, 255, 255, 0.25);
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# ================= ENV =================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# ================= AI CALL FUNCTION =================
def call_ai(prompt, temperature=0.3):
    # lazy import requests so app can import even if requests is missing
    try:
        import requests
    except Exception:
        return "AI Error: missing dependency 'requests' - install with pip install requests"

    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    if not DEEPSEEK_API_KEY:
        return "API key missing."

    try:
        res = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages":[
                    {"role": "system", "content":"You are a helpful academic assistant."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature
            },
            timeout=60
        )
        return res.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"AI Error: {str(e)}"

# ================= SMALL HELPERS (added; does not affect other pages) =================
def extract_json_array(text: str):
    """Try to extract a JSON array from AI output even if it includes extra text."""
    if not text:
        return None
    cleaned = text.strip().replace("```json", "").replace("```", "").strip()
    start = cleaned.find("[")
    end = cleaned.rfind("]") + 1
    if start == -1 or end <= 0:
        return None
    try:
        return json.loads(cleaned[start:end])
    except:
        return None


def _resolve_about_photo():
    """Resolve profile photo from configured fixed path only."""
    candidates = [
        os.getenv("ABOUT_PHOTO_PATH", "").strip(),
        "/Users/tashi/Desktop/ai-study-assistant/about_photo.JPG",
        "/Users/tashi/Desktop/Internship Stuff/about-photo.jpg",
        "/Users/tashi/Desktop/Internship Stuff/about-photo.jpeg",
        "/Users/tashi/Desktop/Internship Stuff/about-photo.png",
        "/Users/tashi/Desktop/Internship Stuff/profile.jpg",
        "/Users/tashi/Desktop/Internship Stuff/profile.jpeg",
        "/Users/tashi/Desktop/Internship Stuff/profile.png",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def render_about_section():
    """Render founder/about hero section on top of the main page."""
    col_photo, col_text = st.columns([1, 2.1], gap="large")

    with col_photo:
        photo = _resolve_about_photo()
        if photo:
            st.image(photo, use_container_width=True)
        else:
            st.markdown(
                f"""
                <div style="
                    width:100%;
                    aspect-ratio: 4 / 5;
                    border-radius:14px;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    font-weight:800;
                    font-size:46px;
                    color:{text_color};
                    background: linear-gradient(145deg, rgba(247,203,212,0.52), rgba(245,228,214,0.52));
                ">ZS</div>
                <p class="about-note">Upload your profile photo from the sidebar.</p>
                """,
                unsafe_allow_html=True
            )

    with col_text:
        st.markdown(
            f"""
            <h2 class="about-name">Zartashia Saleem</h2>
            <div class="about-role">AI & Data Science | BSc Computer Science (Hons), TU Dublin</div>
            <p class="about-copy">
                I build practical AI systems that solve real-world problems, from LLM-powered support assistants
                to data-driven automation workflows. My focus is on designing software that is both technically strong
                and genuinely useful for students, teams, and business operations.
            </p>
            <div style="margin-top: 10px;">
                <span class="about-metric">GPA 3.7 / 4.0</span>
                <span class="about-metric">Python • ML • React • Node.js</span>
                <span class="about-metric">AI Adoption Strategist Intern</span>
                <span class="about-metric">NVIDIA Deep Learning Certified</span>
            </div>
            <p class="about-copy" style="margin-top: 12px;">
                Recently, I led and contributed to projects in chatbot development, inventory optimization, and
                campus-scale platforms, while supporting student communities through technology and communication.
            </p>
            """,
            unsafe_allow_html=True
        )

# ================= SESSION STATE =================
if "notes" not in st.session_state:
    st.session_state.notes = ""
    st.session_state.topics = []
    st.session_state.questions = []
    st.session_state.answers = []
    st.session_state.index = 0
    st.session_state.score = 0
    st.session_state.weak_topics = []

# --- Practice Quiz Helper state (added; only used in Practice) ---
if "quiz_chat_messages" not in st.session_state:
    st.session_state.quiz_chat_messages = [
        {"role": "assistant", "content": "Hi 👋 I'm your Quiz Helper 🌸. Ask me anything about this quiz — hints, explanations, or concepts!"}
    ]

if "quiz_chat_open" not in st.session_state:
    st.session_state.quiz_chat_open = False

if "current_page" not in st.session_state:
    st.session_state.current_page = "Upload Notes"

if "last_sidebar_menu" not in st.session_state:
    st.session_state.last_sidebar_menu = "Upload Notes"

if "last_content_page" not in st.session_state:
    st.session_state.last_content_page = "Upload Notes"

# ================= FILE READERS =================
def read_txt(file): return clean_text(file.read().decode("utf-8"))
def read_pdf(file): return clean_text(" ".join(page.extract_text() or "" for page in PdfReader(file).pages))
def read_docx(file): return clean_text("\n".join(p.text for p in docx.Document(file).paragraphs))

# ================= HEADER =================
header_col1, header_col2 = st.columns([8, 1.2])
with header_col2:
    if st.button("About", key="about_header_btn", use_container_width=True, type="primary"):
        if st.session_state.current_page == "About":
            st.session_state.current_page = st.session_state.last_content_page
        else:
            st.session_state.current_page = "About"
        st.rerun()
st.title("🧠 Study Buddy")
st.caption("AI-powered smart study assistant")

# ================= SIDEBAR =================
user = get_current_user()
st.sidebar.markdown(f"**👤 {user['name']}**")
st.sidebar.caption(user['email'])

menu = st.sidebar.radio(
    "Navigation",
    [
        "Upload Notes",
        "Topics",
        "Practice",
        "Flashcards",
        "AI Doubt Chat",
        "AI Notes Summary",
        "Study Plan",
        "Progress"
    ]
)

sidebar_changed = menu != st.session_state.last_sidebar_menu
if sidebar_changed:
    st.session_state.current_page = menu
    st.session_state.last_content_page = menu
st.session_state.last_sidebar_menu = menu

menu = st.session_state.current_page

# =================RESET EVERYTHING=================
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("🔄 Reset"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

with col2:
    if st.button("🚪 Logout"):
        logout()
        st.rerun()



# ================= ABOUT =================
if menu == "About":
    render_about_section()

# ================= UPLOAD =================
elif menu=="Upload Notes":
    st.markdown("### 📄 Upload Notes or Paste Text")

    file = st.file_uploader("Upload TXT / PDF / DOCX", type=["txt","pdf","docx"])

    pasted = st.text_area(
        "Or paste your notes here",
        height=220,
        placeholder="Paste your notes text here..."
    )

    text = ""

    # 1) Read from file if uploaded
    if file:
        if file.name.endswith(".txt"):
            text = read_txt(file)
        elif file.name.endswith(".pdf"):
            text = read_pdf(file)
        else:
            text = read_docx(file)

    # 2) If pasted text exists, prefer it
    if pasted.strip():
        text = clean_text(pasted)

    if st.button("Analyze Notes"):
        if not text.strip():
            st.warning("Please upload a file or paste some text first.")
        else:
            st.session_state.notes = text
            st.session_state.topics = processor.extract_topics_from_texts([text])

            # Optional: reset quiz state so old questions don't stay around
            st.session_state.questions = []
            st.session_state.answers = []
            st.session_state.index = 0
            st.session_state.score = 0

            st.success("✅ Notes analyzed successfully!")

# ================= TOPICS =================
elif menu=="Topics":
    if not st.session_state.topics: st.info("Upload notes first")
    else:
        for t in st.session_state.topics:
            st.write(f"### {t['name']}")
            st.progress(t["importance_score"]/100)

# ================= PRACTICE =================
elif menu == "Practice":
    if not st.session_state.notes:
        st.warning("Upload notes first")
    else:
        # ---- start quiz ----
        if st.button("Start AI Practice Test"):
            with st.spinner("Generating Practice Questions..."):
                # If you upgraded generator.py, you can use mixed quiz:
                # st.session_state.questions = generator.generate_mixed_quiz(st.session_state.topics, st.session_state.notes, total_questions=12)

                # Otherwise keep your existing:
                st.session_state.questions = generator.generate_smart_questions(
                    st.session_state.topics, st.session_state.notes
                )

                st.session_state.index = 0
                st.session_state.score = 0
                st.session_state.answers = []

            st.rerun()

        # ---- quiz display ----
        if st.session_state.questions:
            total_q = len(st.session_state.questions)
            current_q = st.session_state.index

            # Finished
            if current_q >= total_q:
                score = st.session_state.score
                st.success(f"Final Score: {score}/{total_q} ({score/total_q*100:.1f}%)")

                st.markdown("## 📋 Review")
                for a in st.session_state.answers:
                    st.write(f"**Q:** {a['question']}")
                    st.write(f"Your Answer: {a['selected']}")

                    if str(a["selected"]).strip().lower() == str(a["correct"]).strip().lower():
                        st.success(f"✅ Correct Answer: {a['correct']}")
                    else:
                        st.error(f"❌ Correct Answer: {a['correct']}")

                    st.divider()

            else:
                # Progress bar + counter
                st.progress(current_q / total_q)
                st.markdown(f"### Question {current_q + 1} of {total_q}")

                q = st.session_state.questions[current_q]
                ans_type = q.get("type", "mcq")

                # Input types
                if ans_type == "mcq":
                    ans = st.radio(q["question"], q.get("options", []), key=f"ans_{current_q}")
                elif ans_type in ["fill", "short"]:
                    ans = st.text_input(q["question"], key=f"ans_{current_q}")
                elif ans_type in ["definition", "long"]:
                    ans = st.text_area(q["question"], key=f"ans_{current_q}")
                else:
                    ans = st.text_input(q["question"], key=f"ans_{current_q}")

                # Submit
                if st.button("Submit Answer"):
                    if not str(ans).strip():
                        st.warning("Please enter/select an answer first.")
                        st.stop()

                    st.session_state.answers.append({
                        "question": q["question"],
                        "topic": q.get("topic", "General"),
                        "selected": ans,
                        "correct": q.get("correct", "")
                    })

                    if str(ans).strip().lower() == str(q.get("correct", "")).strip().lower():
                        st.session_state.score += 1
                        st.success("✅ Correct!")
                    else:
                        st.error(f"❌ Correct Answer: {q.get('correct', '')}")

                    st.session_state.index += 1
                    st.rerun()

        # ================= QUIZ HELPER CHAT (🌸 CLEAN VERSION) =================
        # Initialize state
        if "quiz_chat_open" not in st.session_state:
            st.session_state.quiz_chat_open = False

        if "quiz_chat_messages" not in st.session_state:
            st.session_state.quiz_chat_messages = [
                {"role": "assistant", "content": "Hi 👋 I'm your Quiz Helper 🌸. Ask me anything about this quiz!"}
            ]

        st.markdown("---")

        # Toggle Button
        if st.button("🌸 Open Quiz Helper", use_container_width=False):
            st.session_state.quiz_chat_open = not st.session_state.quiz_chat_open

        # Show chat if open
        if st.session_state.quiz_chat_open:

            st.markdown("### 🌸 Quiz Helper — How can I help?")

            chat_container = st.container()

            with chat_container:
                for msg in st.session_state.quiz_chat_messages:
                    if msg["role"] == "user":
                        st.markdown(f"**You:** {msg['content']}")
                    else:
                        st.markdown(f"**Helper:** {msg['content']}")

            user_msg = st.text_input("Ask about the quiz...", key="quiz_chat_input")

            col1, col2 = st.columns([1, 1])

            with col1:
                send = st.button("Send")

            with col2:
                close = st.button("Close Chat")

            if close:
                st.session_state.quiz_chat_open = False
                st.rerun()

            if send and user_msg.strip():
                st.session_state.quiz_chat_messages.append(
                    {"role": "user", "content": user_msg.strip()}
                )

                # Add context of current question
                current_q = None
                if st.session_state.questions and st.session_state.index < len(st.session_state.questions):
                    current_q = st.session_state.questions[st.session_state.index]

                context = f"""
Notes:
{st.session_state.notes[:2500]}

Topics:
{[t['name'] for t in st.session_state.topics]}
"""

                if current_q:
                    context += f"""
Current Question:
Topic: {current_q.get('topic','General')}
Question: {current_q.get('question','')}
Options: {current_q.get('options',[])}
"""

                ai_prompt = f"""
You are a quiz tutor.
Help the student understand the quiz question and concept.
Do NOT directly give the answer unless explicitly asked.

{context}

Student question:
{user_msg}
"""

                with st.spinner("🌸 Thinking..."):
                    ai_reply = call_ai(ai_prompt, temperature=0.3)

                st.session_state.quiz_chat_messages.append(
                    {"role": "assistant", "content": ai_reply}
                )

                st.session_state.quiz_chat_input = ""
                st.rerun()

# ================= FLASHCARDS =================
elif menu == "Flashcards":
    if not st.session_state.notes:
        st.info("Upload notes first")
    else:
        topic_names = [t["name"] for t in st.session_state.topics]
        selected_topic = st.selectbox("Select Topic", topic_names)

        if st.button("Generate Flashcards"):
            with st.spinner("Creating beautiful flashcards..."):
                cards = generator.generate_flashcards(selected_topic, st.session_state.notes)
                st.session_state.flashcards = cards

        if "flashcards" in st.session_state and st.session_state.flashcards:
            for card in st.session_state.flashcards:
                st.markdown(f"""
                <div style="
                    background-color: {card_color};
                    padding: 30px;
                    border-radius: 20px;
                    border: 1px solid {border_color};
                    box-shadow: 0px 8px 20px rgba(0,0,0,0.3);
                    margin-bottom: 25px;
                    width: 350px;
                ">
                    <h3 style="color: {accent_color}; margin-top: 0;">{card['front']}</h3>
                    <hr style="border-color: {border_color};">
                    <p style="font-size:16px; line-height:1.6; color: {text_color};">
                        {card['back']}
                    </p>
                </div>
                """, unsafe_allow_html=True)

# ================= AI DOUBT CHAT =================
elif menu=="AI Doubt Chat":
    if not st.session_state.notes: st.info("Upload notes first")
    else:
        q = st.text_input("Ask your question")
        if st.button("Ask AI"):
            with st.spinner("Generating your answer..."):
                prompt = f"""
You are an academic assistant.

Answer using uploaded notes AND relevant topics intelligently.
If answer is not directly in notes, provide an accurate answer based on the context.

Notes:
{st.session_state.notes[:4000]}

Topics:
{[t['name'] for t in st.session_state.topics]}

Question:
{q}
"""
                response = call_ai(prompt, temperature=0.3)
            st.markdown("### AI Answer")
            st.write(response)

# ================= AI NOTES SUMMARY =================
elif menu=="AI Notes Summary":
    if not st.session_state.notes: st.info("Upload notes first")
    else:
        if st.button("Generate Summary"):
            with st.spinner("Generating Summary..."):
                prompt = f"""
Summarize notes into key points, definitions, and 5-bullet summary.

Notes:
{st.session_state.notes[:4000]}
"""
                summary = call_ai(prompt)
                st.markdown("### 📘 Notes Summary")
                st.write(summary)

# ================= STUDY PLAN =================
elif menu == "Study Plan":
    if not st.session_state.topics: st.info("Upload notes first")
    else:
        st.markdown("## 🗓 Smart Study Planner")
        plan_type = st.radio("Choose Plan Type", ["Total Hours", "Days + Hours Per Day"])

        if plan_type == "Total Hours":
            total_hours = st.slider("How many total hours do you have?", 1, 50, 6)
            if st.button("Generate Smart Plan"):
                with st.spinner("Generating personalized AI study plan..."):
                    plan = generator.generate_detailed_study_plan(
                        st.session_state.topics,
                        st.session_state.notes,
                        total_hours=total_hours
                    )
                    st.session_state.study_plan = plan
        else:
            total_days = st.slider("Number of Days", 1, 14, 3)
            hours_per_day = st.slider("Hours Per Day", 1, 12, 4)
            if st.button("Generate Smart Plan"):
                with st.spinner("Generating personalized AI study plan..."):
                    plan = generator.generate_detailed_study_plan(
                        st.session_state.topics,
                        st.session_state.notes,
                        total_days=total_days,
                        hours_per_day=hours_per_day
                    )
                    st.session_state.study_plan = plan

        if "study_plan" in st.session_state and st.session_state.study_plan:
            for day in st.session_state.study_plan:
                st.markdown(f"### 📅 {day['day']}")
                for item in day["schedule"]:
                    st.markdown(
                        f"""
                        <div style="
                            background:{card_color};
                            border: 1px solid {border_color};
                            padding:15px;
                            border-radius:12px;
                            margin-bottom:10px;
                        ">
                        <b style="color: {text_color};">{item['time']}</b><br>
                        <span style="color:{accent_color}; font-weight: 600;">{item['topic']}</span><br>
                        <span style="color: {text_color};">{item['task']}</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

# ================= PROGRESS =================
elif menu=="Progress":
    if not st.session_state.answers: st.info("Take a test first")
    else:
        st.markdown("## 📊 Progress Report")
        stats = defaultdict(lambda: {"correct":0,"total":0})
        for a in st.session_state.answers:
            stats[a["topic"]]["total"] +=1
            if str(a["selected"]).strip().lower() == str(a["correct"]).strip().lower():
                stats[a["topic"]]["correct"] +=1
        for topic, s in stats.items():
            acc = s["correct"]/s["total"]
            st.write(f"### {topic}: {s['correct']}/{s['total']} correct ({acc*100:.1f}%)")
            if acc>=0.8: st.success("Strong understanding ✅")
            elif acc>=0.5: st.warning("Needs more effort ⚠️")
            else: st.error("High focus required ❗")

st.divider()
st.caption("Your AI Study Buddy 🚀")
