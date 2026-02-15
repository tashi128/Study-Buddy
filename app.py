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

# ================= AI CALL =================
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

# ================= SESSION =================
if "notes" not in st.session_state:
    st.session_state.notes = ""
    st.session_state.topics = []
    st.session_state.questions = []
    st.session_state.answers = []
    st.session_state.index = 0
    st.session_state.score = 0
    st.session_state.weak_topics = []

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

# ================= PRACTICE =================
if menu=="Practice":

    if not st.session_state.notes:
        st.warning("Upload notes first")

    else:
        if st.button("Start AI Practice Test"):
            with st.spinner("Generating Practice Questions..."):
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
            progress_ratio = current_q / total_q
            st.progress(progress_ratio)
            st.markdown(f"### Question {current_q+1} of {total_q}")

            if current_q >= total_q:

                score = st.session_state.score
                st.success(f"Final Score: {score}/{total_q} ({score/total_q*100:.1f}%)")

            else:
                q = st.session_state.questions[current_q]
                ans = st.radio(q["question"], q["options"])

                if st.button("Submit Answer"):
                    if not ans:
                        st.warning("Select an answer")
                        st.stop()

                    st.session_state.answers.append({
                        "question": q["question"],
                        "topic": q["topic"],
                        "selected": ans,
                        "correct": q["correct"]
                    })

                    if ans.strip().lower() == q["correct"].strip().lower():
                        st.session_state.score += 1
                        st.success("✅ Correct!")
                    else:
                        st.error(f"❌ Correct Answer: {q['correct']}")

                    st.session_state.index += 1
                    st.rerun()

# ================= AI DOUBT CHAT =================
elif menu=="AI Doubt Chat":

    if not st.session_state.notes:
        st.info("Upload notes first")

    else:
        question = st.text_input("Ask your question")

        if st.button("Ask AI"):

            with st.spinner("Generating your answer..."):

                prompt = f"""
Answer clearly and concisely.

Notes:
{st.session_state.notes[:4000]}

Question:
{question}
"""

                response = call_ai(prompt)

            st.markdown("### 🤖 AI Answer")
            st.write(response)

# ================= STUDY PLAN =================
elif menu == "Study Plan":

    if not st.session_state.topics:
        st.info("Upload notes first")

    else:
        st.markdown("## 🗓 Smart Study Planner")

        plan_type = st.radio(
            "Choose Plan Type",
            ["Total Hours", "Days + Hours Per Day"]
        )

        if plan_type == "Total Hours":
            total_hours = st.slider("Total Hours", 1, 50, 6)

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

# ================= FOOTER =================
st.divider()
st.caption("Your AI Study Buddy 🚀")
