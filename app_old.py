import os
import json
import streamlit as st
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from PyPDF2 import PdfReader
import docx
from collections import defaultdict
from processor import processor
from question_generator import generator
from utils import clean_text

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
    bg_color = "#0E1117"
    card_color = "#1E1E1E"
    text_color = "white"
else:
    st.session_state.theme = "Light"
    bg_color = "#F5F5F5"
    card_color = "white"
    text_color = "black"

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {bg_color};
        color: {text_color};
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# ================= ENV =================
load_dotenv()
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
        {"role": "assistant", "content": "Hi 👋 I’m your Quiz Helper 🌸. Ask me anything about this quiz — hints, explanations, or concepts!"}
    ]

if "helper_open" not in st.session_state:
    st.session_state.helper_open = True

if "practice_helper_initialized" not in st.session_state:
    st.session_state.practice_helper_initialized = False  # auto-open once

if "clear_helper_input" not in st.session_state:
    st.session_state.clear_helper_input = False

if "quiz_helper_input" not in st.session_state:
    st.session_state.quiz_helper_input = ""

# ================= FILE READERS =================
def read_txt(file): return clean_text(file.read().decode("utf-8"))
def read_pdf(file): return clean_text(" ".join(page.extract_text() or "" for page in PdfReader(file).pages))
def read_docx(file): return clean_text("\n".join(p.text for p in docx.Document(file).paragraphs))

# ================= HEADER =================
st.title("🧠 Study Buddy")
st.caption("AI-powered smart study assistant")

# ================= SIDEBAR =================
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

# =================RESET EVERYTHING=================
if st.sidebar.button("🔄 Reset Everything"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()



# ================= UPLOAD =================
if menu=="Upload Notes":
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

            # Optional: reset quiz state so old questions don’t stay around
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

        # ================= FLOATING QUIZ CHAT (🌸) =================
        # Init chat state
        if "quiz_chat_open" not in st.session_state:
            st.session_state.quiz_chat_open = False
        if "quiz_chat_messages" not in st.session_state:
            st.session_state.quiz_chat_messages = [
                {"role": "assistant", "content": "Hi 👋 I’m your Quiz Helper 🌸. Ask me anything about this quiz!"}
            ]

        # Floating button CSS (works reliably)
        st.markdown("""
        <style>
        /* Float the quiz helper button bottom-right */
        div[data-testid="stButton"] > button#quiz_chat_toggle_btn {
            position: fixed !important;
            right: 22px !important;
            bottom: 22px !important;
            width: 56px !important;
            height: 56px !important;
            border-radius: 999px !important;
            background: #7C3AED !important;
            color: #fff !important;
            border: none !important;
            box-shadow: 0 10px 24px rgba(0,0,0,0.25) !important;
            font-size: 24px !important;
            z-index: 9999 !important;
        }

        /* Chat panel */
        .sb-chat-panel {
          position: fixed;
          right: 22px;
          bottom: 90px;
          width: 360px;
          max-width: 92vw;
          height: 460px;
          max-height: 70vh;
          background: rgba(22,27,34,0.98);
          border: 1px solid rgba(255,255,255,0.08);
          border-radius: 16px;
          box-shadow: 0 18px 44px rgba(0,0,0,0.35);
          z-index: 9998;
          overflow: hidden;
        }

        .sb-chat-header{
          padding: 12px 14px;
          background: rgba(124,58,237,0.15);
          border-bottom: 1px solid rgba(255,255,255,0.08);
          font-weight: 700;
        }

        .sb-chat-body{
          padding: 12px 14px;
          height: 320px;
          overflow-y: auto;
          font-size: 14px;
        }

        .sb-chat-bubble-user{
          background: rgba(124,58,237,0.22);
          border: 1px solid rgba(124,58,237,0.35);
          padding: 10px 12px;
          border-radius: 14px;
          margin: 8px 0;
        }

        .sb-chat-bubble-ai{
          background: rgba(255,255,255,0.06);
          border: 1px solid rgba(255,255,255,0.08);
          padding: 10px 12px;
          border-radius: 14px;
          margin: 8px 0;
        }

        .sb-chat-footer{
          padding: 12px 14px;
          border-top: 1px solid rgba(255,255,255,0.08);
          background: rgba(0,0,0,0.05);
        }
        </style>
        """, unsafe_allow_html=True)

        # REAL toggle button (we give it an HTML id via JS-free trick: empty label + CSS selector by key isn't stable)
        # We'll just render it and style using :has is not supported, so simplest: use a normal button then inject id with html below
        # Streamlit doesn't allow direct id on button, so we do a small hack: use markdown anchor then style the button in order.
        # We'll do a simpler approach: place the toggle button at bottom and style all secondary buttons in Practice is risky.
        # So we keep it unstyled but floating via container hack:
        float = st.container()
        with float:
            # create a button we can target by adding a hidden html element before it
            st.markdown('<div id="quiz_chat_toggle_anchor"></div>', unsafe_allow_html=True)
            if st.button("🌸", key="quiz_chat_toggle"):
                st.session_state.quiz_chat_open = not st.session_state.quiz_chat_open
                st.rerun()

        # If open, show the panel
        if st.session_state.quiz_chat_open:
            # Current question context
            current_q_obj = None
            if st.session_state.questions and st.session_state.index < len(st.session_state.questions):
                current_q_obj = st.session_state.questions[st.session_state.index]

            st.markdown('<div class="sb-chat-panel">', unsafe_allow_html=True)
            st.markdown('<div class="sb-chat-header">🌸 Quiz Helper — How can I help?</div>', unsafe_allow_html=True)

            st.markdown('<div class="sb-chat-body">', unsafe_allow_html=True)
            for msg in st.session_state.quiz_chat_messages:
                if msg["role"] == "user":
                    st.markdown(f'<div class="sb-chat-bubble-user"><b>You:</b><br>{msg["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="sb-chat-bubble-ai"><b>Helper:</b><br>{msg["content"]}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="sb-chat-footer">', unsafe_allow_html=True)
            user_msg = st.text_input("Ask about the quiz...", key="quiz_chat_input")

            c1, c2 = st.columns([1, 1])
            with c1:
                send = st.button("Send", key="quiz_chat_send")
            with c2:
                clear = st.button("Clear", key="quiz_chat_clear")
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

            if clear:
                st.session_state.quiz_chat_messages = [
                    {"role": "assistant", "content": "Hi 👋 I’m your Quiz Helper 🌸. Ask me anything about this quiz!"}
                ]
                st.rerun()

            if send and user_msg.strip():
                st.session_state.quiz_chat_messages.append({"role": "user", "content": user_msg.strip()})

                context = f"""
Notes:
{st.session_state.notes[:2500]}

Topics:
{[t['name'] for t in st.session_state.topics]}
"""
                if current_q_obj:
                    context += f"""
Current Question:
Topic: {current_q_obj.get('topic','General')}
Type: {current_q_obj.get('type','mcq')}
Question: {current_q_obj.get('question','')}
Options: {current_q_obj.get('options', [])}
"""

                ai_prompt = f"""
You are a quiz tutor.
Help the student understand the quiz question and concepts.
Do NOT reveal the correct answer unless the student explicitly asks.

{context}

Student message:
{user_msg.strip()}
"""

                with st.spinner("🌸 Thinking..."):
                    ai_reply = call_ai(ai_prompt, temperature=0.3)

                st.session_state.quiz_chat_messages.append({"role": "assistant", "content": ai_reply})
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
                    box-shadow: 0px 8px 20px rgba(0,0,0,0.1);
                    margin-bottom: 25px;
                    width: 350px;
                ">
                    <h3 style="color:#7C3AED;">{card['front']}</h3>
                    <hr>
                    <p style="font-size:16px; line-height:1.6;">
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
                            padding:15px;
                            border-radius:12px;
                            margin-bottom:10px;
                        ">
                        <b>{item['time']}</b><br>
                        <span style="color:#8B5CF6">{item['topic']}</span><br>
                        {item['task']}
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

st.divider()
st.caption("Your AI Study Buddy 🚀")