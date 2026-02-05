# app.py - AI-Powered Study Buddy
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

# ================= AI QUESTION GENERATOR =================
def generate_ai_questions(text, n=10):
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
Create {n} multiple-choice questions from the text below.
Return ONLY JSON in this format:

[
  {{
    "question": "...",
    "options": ["A","B","C","D"],
    "correct": "A"
  }}
]

TEXT:
{text[:3000]}
"""

    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=30)
        res.raise_for_status()
        content = res.json()["choices"][0]["message"]["content"]
        return json.loads(content)
    except Exception:
        st.warning("AI failed. Using fallback questions.")
        return generator.generate_question_set(st.session_state.topics, n)

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
menu = st.sidebar.radio("Menu", ["Upload Notes", "Topics", "Practice", "Progress"])

st.title("🎀 Study Buddy")
st.caption("AI-powered study assistant")

# ================= UPLOAD NOTES =================
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
            lecture_texts = [text.replace("\n", " ")]  # flatten text for processor
            st.session_state.topics = processor.extract_topics_from_lectures(lecture_texts)
            st.success("Notes processed successfully!")

# ================= TOPICS =================
elif menu == "Topics":
    if not st.session_state.topics:
        st.info("Upload notes first")
    else:
        st.subheader("Extracted Topics with Importance %")
        for t in st.session_state.topics:
            st.info(f"{t['name']} - Importance: {t.get('importance_score',0)}%")

# ================= PRACTICE =================
elif menu == "Practice":
    if not st.session_state.notes:
        st.warning("Upload notes first")
    else:
        if st.button("Start AI Practice"):
            st.session_state.questions = generate_ai_questions(st.session_state.notes, n=10)
            st.session_state.index = 0
            st.session_state.score = 0
            st.session_state.answers = []
            st.rerun()

        if st.session_state.questions:
            if st.session_state.index >= len(st.session_state.questions):
                st.success("Practice Finished!")
                st.write("Score:", st.session_state.score)
                st.subheader("Answer Review")
                for i, q in enumerate(st.session_state.questions):
                    st.write(f"Q{i+1}: {q['question']}")
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
