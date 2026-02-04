import os
import random
import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
import docx
from sklearn.feature_extraction.text import CountVectorizer
from openai import OpenAI
import json

# ================= ENV =================
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

# ================= FILE READERS =================

def read_txt(file):
    return file.read().decode("utf-8")

def read_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def read_docx(file):
    doc = docx.Document(file)
    return "\n".join(p.text for p in doc.paragraphs)

# ================= TOPIC EXTRACTION =================

def extract_topics(text, n_topics=5):
    if not text.strip():
        return []

    vectorizer = CountVectorizer(stop_words="english", max_features=30)
    X = vectorizer.fit_transform([text])

    words = vectorizer.get_feature_names_out()
    counts = X.toarray()[0]

    topics = [
        {"name": w.title(), "importance_score": int(c)}
        for w, c in zip(words, counts)
    ]

    topics.sort(key=lambda x: x["importance_score"], reverse=True)
    return topics[:n_topics]

# ================= AI QUESTION GENERATOR =================

def generate_ai_questions(text, n=5):
    prompt = f"""
You are an AI study assistant.

From the notes below, generate {n} multiple-choice questions.
Each question must include:
- One correct answer
- Three incorrect but believable answers

Return ONLY valid JSON in this format:
[
  {{
    "question": "...",
    "options": ["A", "B", "C", "D"],
    "correct": "A"
  }}
]

NOTES:
{text[:3000]}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )

        content = response.choices[0].message.content
        return json.loads(content)

    except Exception as e:
        st.error("AI question generation failed. Falling back to basic questions.")
        return []

# ================= PAGE CONFIG =================

st.set_page_config(page_title="Study Buddy", page_icon="🧸", layout="wide")

# ================= SESSION STATE =================

defaults = {
    "topics": [],
    "questions": [],
    "current_question": 0,
    "score": 0,
    "notes_text": "",
    "user_answers": []
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ================= SIDEBAR =================

with st.sidebar:
    st.title("🧸 Study Buddy")
    menu = st.radio("", ["Upload Notes", "My Topics", "Practice Game", "Progress", "Settings"])

# ================= HEADER =================

st.title("🎀 Study Buddy")
st.caption("Your AI-powered study companion")

# ======================================================
# UPLOAD NOTES
# ======================================================

if menu == "Upload Notes":

    uploaded = st.file_uploader("Upload notes", type=["txt", "pdf", "docx"])

    if uploaded:
        st.success(f"{uploaded.name} uploaded")

        if uploaded.name.endswith(".txt"):
            text = read_txt(uploaded)
        elif uploaded.name.endswith(".pdf"):
            text = read_pdf(uploaded)
        elif uploaded.name.endswith(".docx"):
            text = read_docx(uploaded)
        else:
            text = ""

        if st.button("Process Notes"):
            st.session_state.notes_text = text
            st.session_state.topics = extract_topics(text)
            st.success("Notes processed successfully!")

# ======================================================
# TOPICS
# ======================================================

elif menu == "My Topics":

    if not st.session_state.topics:
        st.info("Upload notes first")

    else:
        for t in st.session_state.topics:
            st.markdown(f"""
            <div style="background:white;padding:20px;border-radius:20px;
            border:2px solid #FFE8E8;margin-bottom:15px;color:#4B2E2E;">
            <h3>📌 {t['name']}</h3>
            Importance Score: {t['importance_score']}
            </div>
            """, unsafe_allow_html=True)

# ======================================================
# PRACTICE GAME (AI)
# ======================================================

elif menu == "Practice Game":

    if not st.session_state.notes_text:
        st.warning("Upload notes first")

    else:
        if st.button("Start AI Practice"):
            st.session_state.questions = generate_ai_questions(
                st.session_state.notes_text, n=5
            )
            st.session_state.current_question = 0
            st.session_state.score = 0
            st.session_state.user_answers = []
            st.rerun()

        if st.session_state.questions:

            # Finished
            if st.session_state.current_question >= len(st.session_state.questions):

                st.success("Practice Complete!")
                st.write("Final Score:", st.session_state.score)

                st.subheader("Answer Review")

                for i, q in enumerate(st.session_state.questions):
                    st.write(f"Q{i+1}: {q['question']}")
                    st.write(f"Your Answer: {st.session_state.user_answers[i]}")
                    st.write(f"Correct Answer: {q['correct']}")
                    st.write("---")

            else:
                q = st.session_state.questions[st.session_state.current_question]

                ans = st.radio(
                    q["question"],
                    q["options"],
                    key=f"q_{st.session_state.current_question}"
                )

                if st.button("Submit Answer"):
                    st.session_state.user_answers.append(ans)

                    if ans == q["correct"]:
                        st.session_state.score += 1
                        st.success("Correct!")
                    else:
                        st.error(f"Wrong! Correct answer: {q['correct']}")

                    st.session_state.current_question += 1
                    st.rerun()

# ======================================================
# PROGRESS
# ======================================================

elif menu == "Progress":

    st.metric("Topics", len(st.session_state.topics))
    st.metric("Questions", len(st.session_state.questions))
    st.metric("Score", st.session_state.score)

# ======================================================
# SETTINGS
# ======================================================

elif menu == "Settings":

    if st.button("Reset All"):
        st.session_state.clear()
        st.rerun()

# ================= FOOTER =================

st.markdown(f"""
<hr>
<center>
<b>Study Buddy 🎀</b><br>
Topics: {len(st.session_state.topics)} |
Questions: {len(st.session_state.questions)} |
Score: {st.session_state.score}
</center>
""", unsafe_allow_html=True)
