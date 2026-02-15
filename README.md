# 🎀 AI Study Buddy

**AI Study Buddy** is an intelligent, interactive study assistant built with **Python** and **Streamlit**. It helps students learn efficiently by generating practice questions, flashcards, summaries, and personalized study plans from uploaded notes. It also features an AI-powered doubt chat that answers questions based on your notes and study topics.

---

## 🌟 Features

### 1. **Upload Notes**
- Supports **TXT, PDF, and DOCX** files.
- Automatically extracts key **topics** and their importance scores.
- AI reads your notes and understands the content for practice and summarization.

### 2. **Topics**
- Displays **important topics** with progress bars.
- Shows **topic importance** based on your notes.
- Helps prioritize your study material.

### 3. **Practice Questions**
- Generates AI-driven questions from your notes.
- Supports **MCQs, True/False, fill-in-the-blanks, and short answer questions**.
- Automatically **marks answers**, showing what’s right and wrong.
- Displays a **final score** and topic-wise review.
- Shows **questions answered incorrectly** with correct answers for learning reinforcement.

### 4. **Flashcards**
- Generates AI-powered **flashcards** from notes.
- Displayed in **fancy square card style** for visual appeal.
- Shows “**Generating flashcards...**” during processing.

### 5. **AI Doubt Chat**
- Ask questions related to your study material.
- Answers are **context-aware** based on uploaded notes and topics.
- Can answer relevant study-related questions even if not explicitly mentioned in notes.

### 6. **Notes Summarizer**
- Summarizes uploaded notes into **concise key points**.
- Helps quickly review large documents.

### 7. **Study Plan Generator**
- Creates a **personalized study plan** based on topics and importance.
- Suggests daily or weekly study targets.

### 8. **Progress Report**
- Shows topic-wise **accuracy percentage**.
- Highlights areas needing **more effort**.
- Encourages efficient study with visual progress bars.

### 9. **User Interface**
- Supports **light and dark mode**.
- Clean, professional UI with **cards, badges, and progress bars**.
- Sidebar navigation for easy access to all features.

---

## 🛠️ Technology Stack

- **Backend / AI**: Python, OpenAI API (or DeepSeek)
- **Web Framework**: Streamlit
- **PDF / DOCX Handling**: `PyPDF2`, `python-docx`
- **Environment Variables**: `python-dotenv`
- **Hosting**: Streamlit Cloud / Render / Railway (embed on personal website via iframe)
- **Front-End**: Streamlit custom CSS for cards, badges, dark/light theme, and progress bars.

