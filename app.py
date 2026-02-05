# app.py - AI Study Buddy

import os
import json
import requests
import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
import docx

from processor import processor
from question_generator import generator

# ================= ENV =================
load_dotenv()
DEEPEEK_API_KEY = os.getenv("DEEPEEK_API_KEY")

# ================= FILE READERS =================

def read_txt(file):
    return file.read().decode("utf-8")

def read_pdf(file):
    reader = PdfReader(file)
    return " ".join(page.extract_text() or "" for page in reader.pages)

def read_docx(file):
    doc = docx.Document(file)
    return "\n".join(p.text for p in doc.paragraphs)

# ================= DEEPSEEK AI =================

def generate_ai_questions(text, topics, n=10):
    url = "https://api.deepseek.com/chat/completions"

    headers = {
        "Authorization": f"Bearer {DEEPEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    topics_block = "\n".join(
        [f"- {t['name']} ({t['importance_score']}%)" for t in topics]
    )

    prompt = f"""
You are an AI study assistant.

Using the notes AND topic importance below, generate {n} exam-style
multiple-choice questions.

RULES:
- Each question MUST relate to one topic
- 4 options per question
- 1 correct answer
- Answers MUST be accurate
- Return ONLY valid JSON

FORMAT:
[
  {{
    "topic": "Topic name",
    "question": "...",
    "options": ["A","B","C","D"],
    "correct": "A"
  }}
]

TOPICS:
{topics_block}

NOTES:
{text[:3500]}
"""

    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=40)
        res.raise_for_status()
        content = res.json()["choices"][0]["message"]["content"]
        return json.loads(content)

    except Exception as e:
        st.warning("AI failed. Using fallback questions.")
        return generator.generate_question_set(topics, num_questions=n)

# ================= STREAMLIT CONFIG =================

st.set_page_config("Study Buddy 🧸", layout="wide")

# ================= SESSION STATE =================

if "notes" not in st.session_state:
    st.session_state.notes = ""
    st.session_state.topics = []
    st.session_state.questions = []
    st.session_state.index = 0
    st.session_state.score = 0
    st.session_state.answers = []

# ================= SIDEBAR =================

menu = st.sidebar.radio("Menu", [
    "Upload Notes",
    "Topics",
    "Practice",
    "Progress"
])

st.title("🎀 Study Buddy")
st.caption("AI-powered study assistant")

# ================= UPLOAD =================

if menu == "Upload Notes":
    file = st.file_uploader("Upload TXT / PDF / DOCX", type=["txt", "pdf", "docx"])

    if file:
        if file.name.endswith(".txt"):
            text = read_txt(file)
        elif file.name.endswith(".pdf"):
            text = read_pdf(file)
        else:
            text = read_docx(file)

        if st.button("Process Notes"):
            st.session_state.notes = text
            st.session_state.topics = processor.extract_topics_from_lectures([text])
            st.success("Notes processed successfully!")

# ================= TOPICS =================

elif menu == "Topics":
    if not st.session_state.topics:
        st.warning("Upload notes first")
    else:
        st.subheader("Extracted Topics")
        for t in st.session_state.topics:
            st.write(f"**{t['name']}** — Importance: {t['importance_score']}%")
            st.progress(t['importance_score'] / 100)

# ================= PRACTICE =================

elif menu == "Practice":
    if not st.session_state.notes:
        st.warning("Upload notes first")
    else:
        if st.button("Start AI Practice"):
            qs = generate_ai_questions(st.session_state.notes, st.session_state.topics, n=10)
            st.session_state.questions = qs
            st.session_state.index = 0
            st.session_state.score = 0
            st.session_state.answers = []
            st.rerun()

        if st.session_state.questions:
            if st.session_state.index >= len(st.session_state.questions):
                st.success("Practice Complete!")
                st.write("Final Score:", st.session_state.score)
                st.subheader("Answer Review")
                for i, q in enumerate(st.session_state.questions):
                    st.write(f"Q{i+1} ({q['topic']})")
                    st.write(q["question"])
                    st.write("Your answer:", st.session_state.answers[i])
                    st.write("Correct answer:", q["correct"])
                    st.divider()
            else:
                q = st.session_state.questions[st.session_state.index]
                ans = st.radio(q["question"], q["options"], key=f"q_{st.session_state.index}")

                if st.button("Submit Answer"):
                    st.session_state.answers.append(ans)
                    if ans == q["correct"]:
                        st.session_state.score += 1
                        st.success("Correct!")
                    else:
                        st.error(f"Wrong! Correct: {q['correct']}")
                    st.session_state.index += 1
                    st.rerun()

# ================= PROGRESS =================

elif menu == "Progress":
    st.metric("Topics", len(st.session_state.topics))
    st.metric("Questions", len(st.session_state.questions))
    st.metric("Score", st.session_state.score)

st.divider()
st.caption("🧸 Study Buddy")
