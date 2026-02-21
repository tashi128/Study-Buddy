import os
import json
import requests
import streamlit as st
from dotenv import load_dotenv
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
elif menu=="Practice":
    if not st.session_state.notes:
        st.warning("Upload notes first")
    else:
        # Auto-open helper only the first time you enter Practice
        if not st.session_state.practice_helper_initialized:
            st.session_state.helper_open = True
            st.session_state.practice_helper_initialized = True

        # Clear helper input safely BEFORE widget is created
        if st.session_state.clear_helper_input:
            st.session_state.quiz_helper_input = ""
            st.session_state.clear_helper_input = False

        col_quiz, col_side = st.columns([2, 1], gap="large")

        # -------------------- LEFT: QUIZ --------------------
        with col_quiz:
            if st.button("Start AI Practice Test"):
                with st.spinner("Generating Practice Questions..."):
                    topics_list = [t["name"] for t in st.session_state.topics]

                    prompt = f"""
Generate a mixed practice quiz from the notes.

NOTES:
{st.session_state.notes[:4000]}

TOPICS:
{topics_list}

Return STRICT JSON ARRAY ONLY (no markdown, no extra text).

Create 12 questions total with this mix:
- 6 MCQ
- 3 fill in the blanks
- 3 short answers (1-3 lines)

Format examples:
[
  {{
    "type": "mcq",
    "topic": "Topic name",
    "question": "....",
    "options": ["A","B","C","D"],
    "correct": "exact option text"
  }},
  {{
    "type": "fill",
    "topic": "Topic name",
    "question": "The _____ is responsible for ...",
    "correct": "missing word/phrase"
  }},
  {{
    "type": "short",
    "topic": "Topic name",
    "question": "Explain ... in 2-3 lines",
    "correct": "a model short answer"
  }}
]
"""

                    ai_out = call_ai(prompt, temperature=0.2)
                    parsed = extract_json_array(ai_out)

                    if isinstance(parsed, list) and len(parsed) > 0:
                        st.session_state.questions = parsed
                    else:
                        # fallback to your generator if AI JSON fails
                        st.session_state.questions = generator.generate_smart_questions(
                            st.session_state.topics, st.session_state.notes
                        )

                    st.session_state.index = 0
                    st.session_state.score = 0
                    st.session_state.answers = []
                st.rerun()

            if st.session_state.questions:
                total_q = len(st.session_state.questions)
                current_q = st.session_state.index

                # ===== PROGRESS BAR =====
                st.progress(min(current_q / total_q, 1.0))
                st.markdown(f"### Question {min(current_q+1, total_q)} of {total_q}")

                if current_q >= total_q:
                    total = len(st.session_state.questions)
                    score = st.session_state.score
                    st.success(f"Final Score: {score}/{total} ({score/total*100:.1f}%)")
                    st.markdown("## 📋 Review")

                    for a in st.session_state.answers:
                        st.write(f"**Q:** {a['question']}")
                        st.write(f"Your Answer: {a['selected']}")

                        if a.get("is_correct") is True:
                            st.success(f"✅ Correct Answer: {a['correct']}")
                        else:
                            st.error(f"❌ Correct Answer: {a['correct']}")
                            if a.get("feedback"):
                                st.info(f"💡 Feedback: {a['feedback']}")
                        st.divider()

                else:
                    q = st.session_state.questions[current_q]
                    q_type = str(q.get("type", "mcq")).lower().strip()

                    st.markdown(f"**Type:** {q_type.upper()}  •  **Topic:** {q.get('topic','General')}")

                    # Render input by type
                    if q_type == "mcq":
                        ans = st.radio(q["question"], q.get("options", []), key=f"q_{current_q}")
                    elif q_type == "fill":
                        ans = st.text_input(q["question"], key=f"q_{current_q}")
                    else:  # short answer
                        ans = st.text_area(q["question"], key=f"q_{current_q}", height=130)

                    if st.button("Submit Answer"):
                        if not str(ans).strip():
                            st.warning("Select/Enter answer first")
                            st.stop()

                        correct = q.get("correct", "")
                        is_correct = False
                        feedback = ""

                        # MCQ + Fill: case-insensitive exact match
                        if q_type in ["mcq", "fill"]:
                            is_correct = str(ans).strip().lower() == str(correct).strip().lower()
                        else:
                            # Short: quick AI grading (fallback to basic)
                            grade_prompt = f"""
You are grading a student's short answer using the notes.

NOTES:
{st.session_state.notes[:2500]}

QUESTION:
{q.get("question","")}

MODEL ANSWER:
{correct}

STUDENT ANSWER:
{ans}

Return STRICT JSON only:
{{
  "is_correct": true/false,
  "feedback": "1-2 short sentences"
}}
"""
                            grade_out = call_ai(grade_prompt, temperature=0.0)
                            grade_json = None
                            try:
                                grade_json = json.loads(grade_out.replace("```json", "").replace("```", "").strip())
                            except:
                                grade_json = None

                            if isinstance(grade_json, dict):
                                is_correct = bool(grade_json.get("is_correct", False))
                                feedback = str(grade_json.get("feedback", "")).strip()
                            else:
                                # fallback: simple containment
                                is_correct = str(correct).strip().lower() in str(ans).strip().lower()
                                feedback = "Auto-checked (basic). Try to match key points from the model answer."

                        st.session_state.answers.append({
                            "question": q.get("question", ""),
                            "topic": q.get("topic", "General"),
                            "selected": ans,
                            "correct": correct,
                            "type": q_type,
                            "is_correct": is_correct,
                            "feedback": feedback
                        })

                        if is_correct:
                            st.session_state.score += 1
                            st.success("✅ Correct!")
                        else:
                            st.error(f"❌ Correct Answer: {correct}")

                        st.session_state.index += 1
                        st.rerun()

        # -------------------- RIGHT: TIP + QUIZ HELPER CHATBOT --------------------
        with col_side:
            st.markdown(f"""
            <div style="background:{card_color}; padding:15px; border-radius:12px; margin-bottom:10px;">
            <b>💡 Tip</b><br>
            <span style="opacity:0.85;">Use Quiz Helper 🌸 for hints and explanations.</span>
            </div>
            """, unsafe_allow_html=True)

            toggle_label = "Hide 🌸 Quiz Helper" if st.session_state.helper_open else "Show 🌸 Quiz Helper"
            if st.button(toggle_label, key="helper_toggle_btn"):
                st.session_state.helper_open = not st.session_state.helper_open
                st.rerun()

            if st.session_state.helper_open:
                # Current question context
                current_q_obj = None
                if st.session_state.questions and st.session_state.index < len(st.session_state.questions):
                    current_q_obj = st.session_state.questions[st.session_state.index]

                st.markdown(f"""
                <div style="background:{card_color}; padding:15px; border-radius:12px;">
                <b>🌸 Quiz Helper</b><br>
                <span style="opacity:0.85;">Ask for hints, explanations, or concepts. I won’t reveal answers unless you ask.</span>
                </div>
                """, unsafe_allow_html=True)

                st.divider()

                for msg in st.session_state.quiz_chat_messages:
                    with st.chat_message(msg["role"]):
                        st.write(msg["content"])

                user_msg = st.text_input("Ask about the quiz…", key="quiz_helper_input")
                c1, c2 = st.columns([1, 1])
                send = c1.button("Send", key="quiz_helper_send")
                clear = c2.button("Clear", key="quiz_helper_clear")

                if clear:
                    st.session_state.quiz_chat_messages = [
                        {"role": "assistant", "content": "Hi 👋 I’m your Quiz Helper 🌸. Ask me anything about this quiz — hints, explanations, or concepts!"}
                    ]
                    st.session_state.clear_helper_input = True
                    st.rerun()

                if send and str(user_msg).strip():
                    st.session_state.quiz_chat_messages.append({"role": "user", "content": user_msg.strip()})

                    topics_list = [t["name"] for t in st.session_state.topics]
                    context = f"""
NOTES:
{st.session_state.notes[:2500]}

TOPICS:
{topics_list}
"""
                    if current_q_obj:
                        context += f"""
CURRENT QUESTION:
Type: {current_q_obj.get('type','mcq')}
Topic: {current_q_obj.get('topic','General')}
Question: {current_q_obj.get('question','')}
Options: {current_q_obj.get('options', [])}
"""

                    ai_prompt = f"""
You are a quiz tutor. Help the student understand the question and topic.
Do NOT reveal the correct answer directly unless the student asks explicitly.
Give hints, reasoning steps, and examples.

{context}

Student question:
{user_msg.strip()}
"""

                    with st.spinner("🌸 Thinking..."):
                        ai_reply = call_ai(ai_prompt, temperature=0.3)

                    st.session_state.quiz_chat_messages.append({"role": "assistant", "content": ai_reply})
                    st.session_state.clear_helper_input = True
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

st.divider()
st.caption("Your AI Study Buddy 🚀")