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

# ================= SESSION STATE =================
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

# ================= UPLOAD =================
if menu=="Upload Notes":
    file = st.file_uploader("Upload TXT / PDF / DOCX", type=["txt","pdf","docx"])
    if file:
        if file.name.endswith(".txt"): text = read_txt(file)
        elif file.name.endswith(".pdf"): text = read_pdf(file)
        else: text = read_docx(file)
        if st.button("Analyze Notes"):
            st.session_state.notes = text
            st.session_state.topics = processor.extract_topics_from_texts([text])
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
            if st.session_state.index >= len(st.session_state.questions):
                total = len(st.session_state.questions)
                score = st.session_state.score
                st.success(f"Final Score: {score}/{total} ({score/total*100:.1f}%)")
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
                q = st.session_state.questions[st.session_state.index]
                ans_type = q.get("type","mcq")
                if ans_type=="mcq": ans = st.radio(q["question"], q["options"])
                elif ans_type=="fill": ans = st.text_input(q["question"])
                elif ans_type=="definition": ans = st.text_area(q["question"])
                else: ans = st.text_input(q["question"])
                if st.button("Submit Answer"):
                    if not ans: st.warning("Select/Enter answer first"); st.stop()
                    st.session_state.answers.append({
                        "question": q["question"],
                        "topic": q["topic"],
                        "selected": ans,
                        "correct": q["correct"]
                    })
                    if str(ans).strip().lower() == str(q["correct"]).strip().lower():
                        st.session_state.score +=1
                        st.success("✅ Correct!")
                    else:
                        st.error(f"❌ Correct Answer: {q['correct']}")
                    st.session_state.index += 1
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

                cards = generator.generate_flashcards(
                    selected_topic,
                    st.session_state.notes
                )

                st.session_state.flashcards = cards

        # ===== DISPLAY FLASHCARDS =====
        if "flashcards" in st.session_state and st.session_state.flashcards:

            for card in st.session_state.flashcards:

                st.markdown(f"""
                <div style="
                    background-color: #ffffff;
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
elif menu=="Study Plan":
    if not st.session_state.notes: st.info("Upload notes first")
    else:
        weak_topics = st.session_state.get("weak_topics",[])
        if st.button("Generate Study Plan"):
            with st.spinner("Generating Study Plan..."):
                prompt = f"""
Generate a 7-day personalized study plan for a student.

Topics:
{[t['name'] for t in st.session_state.topics]}

Weak Topics:
{weak_topics}

Distribute focus based on importance and weaknesses.
"""
                plan = call_ai(prompt)
                st.markdown("### 📅 Personalized Study Plan")
                st.write(plan)

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
