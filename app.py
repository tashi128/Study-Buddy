import streamlit as st
import random
from PyPDF2 import PdfReader
import docx
from sklearn.feature_extraction.text import CountVectorizer

# ---------------- FILE READERS ----------------

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
    return "\n".join([p.text for p in doc.paragraphs])

# ---------------- TOPIC EXTRACTION ----------------

def extract_topics(text, n_topics=5):

    if not text.strip():
        return []

    vectorizer = CountVectorizer(
        stop_words="english",
        max_features=30
    )

    X = vectorizer.fit_transform([text])

    words = vectorizer.get_feature_names_out()
    counts = X.toarray()[0]

    topics = []

    for word, count in zip(words, counts):
        topics.append({
            "name": word.title(),
            "importance_score": int(count)
        })

    topics = sorted(topics, key=lambda x: x["importance_score"], reverse=True)

    return topics[:n_topics]

# ---------------- QUESTION GENERATOR ----------------

def generate_questions_from_text(text):

    sentences = [s.strip() for s in text.split(".") if len(s) > 40]
    questions = []

    for s in sentences[:5]:

        words = s.split()

        if len(words) > 6:

            blank_index = random.randint(2, len(words) - 2)

            correct = words[blank_index]
            words[blank_index] = "_____"

            question_text = " ".join(words)

            # Clean options
            possible_words = [w for w in set(words) if w != "_____"]
            random_words = random.sample(possible_words, min(2, len(possible_words)))

            options = list(set([correct] + random_words))
            random.shuffle(options)

            questions.append({
                "question": question_text,
                "options": options,
                "correct": correct
            })

    return questions

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Study Buddy", page_icon="🧸", layout="wide")

# ---------------- SESSION STATE ----------------
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

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.title("🧸 Study Buddy")
    menu = st.radio("", ["Upload Notes", "My Topics", "Practice Game", "Progress", "Settings"])

# ---------------- HEADER ----------------
st.title("🎀 Study Buddy")
st.caption("Your cute AI study companion")

# ============================================================
# PAGE 1 UPLOAD
# ============================================================
if menu == "Upload Notes":

    uploaded = st.file_uploader("Upload Notes", type=["txt", "pdf", "docx"])

    if uploaded:

        st.success(f"{uploaded.name} uploaded")

        # Detect file type
        if uploaded.name.endswith(".txt"):
            text_content = read_txt(uploaded)

        elif uploaded.name.endswith(".pdf"):
            text_content = read_pdf(uploaded)

        elif uploaded.name.endswith(".docx"):
            text_content = read_docx(uploaded)

        else:
            text_content = ""

        if st.button("Process Notes"):

            st.session_state.notes_text = text_content
            st.session_state.topics = extract_topics(text_content)

            st.success("Notes processed!")

# ============================================================
# PAGE 2 TOPICS
# ============================================================
elif menu == "My Topics":

    if not st.session_state.topics:
        st.info("Upload notes first")

    else:
        for t in st.session_state.topics:
            st.markdown(f"""
            <div style="
                background:white;
                padding:20px;
                border-radius:20px;
                border:2px solid #FFE8E8;
                margin-bottom:15px;
                color:#4B2E2E;">
            <h3>📌 {t['name']}</h3>
            Importance Score: {t['importance_score']}
            </div>
            """, unsafe_allow_html=True)

# ============================================================
# PAGE 3 PRACTICE
# ============================================================
elif menu == "Practice Game":

    if not st.session_state.notes_text:
        st.warning("Upload notes first")

    else:

        if st.button("Start Practice"):

            st.session_state.questions = generate_questions_from_text(
                st.session_state.notes_text
            )

            st.session_state.current_question = 0
            st.session_state.score = 0
            st.session_state.user_answers = []
            st.rerun()

        if st.session_state.questions:

            # Quiz Finished
            if st.session_state.current_question >= len(st.session_state.questions):

                st.success("Practice Complete!")
                st.write("Final Score:", st.session_state.score)

                st.subheader("Correct Answers Review")

                for i, q in enumerate(st.session_state.questions):
                    user_ans = st.session_state.user_answers[i]

                    st.write(f"Q{i+1}: {q['question']}")
                    st.write(f"Your Answer: {user_ans}")
                    st.write(f"Correct Answer: {q['correct']}")
                    st.write("---")

            else:

                q = st.session_state.questions[st.session_state.current_question]

                ans = st.radio(
                    q["question"],
                    q["options"],
                    key=f"quiz_{st.session_state.current_question}"
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

# ============================================================
# PAGE 4 PROGRESS
# ============================================================
elif menu == "Progress":

    st.metric("Topics", len(st.session_state.topics))
    st.metric("Questions", len(st.session_state.questions))
    st.metric("Score", st.session_state.score)

# ============================================================
# PAGE 5 SETTINGS
# ============================================================
elif menu == "Settings":

    if st.button("Reset All"):
        st.session_state.clear()
        st.rerun()

# ============================================================
# FOOTER
# ============================================================
st.markdown(f"""
<hr>
<center>
<b>Study Buddy 🎀</b><br>
Topics: {len(st.session_state.topics)} |
Questions: {len(st.session_state.questions)} |
Score: {st.session_state.score}
</center>
""", unsafe_allow_html=True)