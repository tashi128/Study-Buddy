import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")


class QuestionGenerator:
    """
    DeepSeek-powered question/flashcard/study-plan generator.

    Improvements vs original:
    - Robust JSON extraction: supports [] arrays and {} objects
    - Better error handling: raise_for_status + readable logs
    - Optional retries for transient API issues
    - New: mixed quiz (mcq/fill/short) + short-answer grading
    """

    # ================= CALL AI =================
    def call_ai(self, prompt: str, temperature: float = 0.3, timeout: int = 60, retries: int = 2):
        if not DEEPSEEK_API_KEY:
            print("❌ DeepSeek API key missing (DEEPSEEK_API_KEY)")
            return None

        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are an expert teacher. Output strictly valid JSON when asked."},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
        }

        last_err = None
        for attempt in range(retries + 1):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=timeout)
                response.raise_for_status()
                result = response.json()

                if "choices" not in result or not result["choices"]:
                    print("❌ Unexpected API response (no choices):", result)
                    return None

                content = result["choices"][0]["message"]["content"]
                return content

            except Exception as e:
                last_err = e
                print(f"❌ AI CALL ERROR (attempt {attempt+1}/{retries+1}): {e}")
                # tiny backoff for transient errors
                time.sleep(0.8 * (attempt + 1))

        print("❌ AI CALL FAILED FINAL:", last_err)
        return None

    # ================= CLEAN MARKDOWN =================
    def _strip_markdown_fences(self, text: str) -> str:
        if not text:
            return ""
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```json", "").replace("```JSON", "").replace("```", "").strip()
        return cleaned

    # ================= EXTRACT JSON (ARRAY OR OBJECT) =================
    def safe_parse_json(self, ai_response: str):
        """
        Extracts JSON from model output.
        Supports:
          - JSON array [...]
          - JSON object {...}
        Returns parsed python object or None.
        """
        if not ai_response:
            return None

        cleaned = self._strip_markdown_fences(ai_response)

        # Try exact parse first (sometimes the model returns perfect JSON)
        try:
            return json.loads(cleaned)
        except Exception:
            pass

        # Try find array
        a_start = cleaned.find("[")
        a_end = cleaned.rfind("]") + 1
        if a_start != -1 and a_end > a_start:
            slice_text = cleaned[a_start:a_end]
            try:
                return json.loads(slice_text)
            except Exception as e:
                print("⚠ JSON array invalid:", e)
                print("BROKEN ARRAY JSON:\n", slice_text[:1500])

        # Try find object
        o_start = cleaned.find("{")
        o_end = cleaned.rfind("}") + 1
        if o_start != -1 and o_end > o_start:
            slice_text = cleaned[o_start:o_end]
            try:
                return json.loads(slice_text)
            except Exception as e:
                print("⚠ JSON object invalid:", e)
                print("BROKEN OBJECT JSON:\n", slice_text[:1500])

        print("⚠ No valid JSON found in AI response.")
        print("RAW RESPONSE (first 1500 chars):\n", cleaned[:1500])
        return None

    # ================= NORMALIZERS =================
    def _normalize_question(self, q: dict, topic_name: str = "General"):
        """
        Ensures consistent fields exist.
        """
        if not isinstance(q, dict):
            return None

        qtype = str(q.get("type", "mcq")).strip().lower()
        question = str(q.get("question", "")).strip()
        correct = q.get("correct", "")

        if not question:
            return None

        # Default topic
        q["topic"] = str(q.get("topic", topic_name)).strip() or topic_name
        q["type"] = qtype

        # Normalize correct to string
        q["correct"] = str(correct).strip()

        # MCQ needs options
        if qtype == "mcq":
            options = q.get("options", [])
            if not isinstance(options, list) or len(options) < 2:
                # cannot be a valid MCQ
                return None
            q["options"] = [str(o).strip() for o in options if str(o).strip()]

            # Ensure 4 options if possible (but don't crash if not)
            if len(q["options"]) < 2:
                return None

        return q

    # ================= GENERATE QUESTIONS (MCQ ONLY, PER TOPIC) =================
    def generate_smart_questions(self, topics, notes_text: str):
        """
        Your original behavior:
        - Generates MCQs per topic based on importance.
        - Returns list of questions with fields: question/options/correct/topic
        """
        all_questions = []

        if not notes_text:
            print("⚠ No notes provided")
            return []

        for topic in topics:
            importance = topic.get("importance_score", 50)

            if importance > 70:
                num_q = 5
            elif importance > 40:
                num_q = 3
            else:
                num_q = 2

            prompt = f"""
Generate {num_q} multiple choice questions.

Topic: {topic['name']}

Use ONLY the notes below to create the questions.

NOTES:
{notes_text[:4000]}

Rules:
- Return ONLY valid JSON
- Do NOT wrap in markdown
- Do NOT add explanation
- Must start with [ and end with ]
- Each question must have:
  {{
    "type": "mcq",
    "question": "...",
    "options": ["A","B","C","D"],
    "correct": "exact correct option text"
  }}
"""

            ai_response = self.call_ai(prompt, temperature=0.3)

            if not ai_response:
                print("⚠ Skipping topic due to empty AI response")
                continue

            parsed = self.safe_parse_json(ai_response)

            if not parsed or not isinstance(parsed, list):
                print("⚠ JSON parsing failed, skipping topic:", topic["name"])
                continue

            for q in parsed:
                nq = self._normalize_question(q, topic_name=topic["name"])
                if nq:
                    nq["topic"] = topic["name"]
                    # ensure type is mcq for this method
                    nq["type"] = "mcq"
                    all_questions.append(nq)

        return all_questions

    # ================= GENERATE MIXED QUIZ (MCQ + FILL + SHORT) =================
    def generate_mixed_quiz(self, topics, notes_text: str, total_questions: int = 12):
        """
        New:
        Generates a mixed quiz across all notes/topics:
        - mcq
        - fill
        - short
        Output format (list):
        [
          {"type":"mcq","topic":"...","question":"...","options":[...],"correct":"..."},
          {"type":"fill","topic":"...","question":"...","correct":"..."},
          {"type":"short","topic":"...","question":"...","correct":"..."}
        ]
        """
        if not notes_text:
            print("⚠ No notes provided")
            return []

        topic_names = [t.get("name", "General") for t in topics] if topics else ["General"]

        # Keep proportions reasonable
        mcq_n = max(1, int(total_questions * 0.5))
        fill_n = max(1, int(total_questions * 0.25))
        short_n = max(1, total_questions - mcq_n - fill_n)

        prompt = f"""
Generate a mixed practice quiz based ONLY on the notes.

NOTES:
{notes_text[:4000]}

TOPICS (use these as "topic" labels when possible):
{topic_names}

Create exactly {total_questions} questions with this mix:
- {mcq_n} MCQ
- {fill_n} Fill in the blanks
- {short_n} Short answers (1-3 lines)

Return STRICT JSON array only (no markdown, no explanation).

Format:
[
  {{
    "type": "mcq",
    "topic": "Topic name",
    "question": "...",
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
    "correct": "model short answer"
  }}
]
"""

        ai_response = self.call_ai(prompt, temperature=0.2)
        parsed = self.safe_parse_json(ai_response)

        if not parsed or not isinstance(parsed, list):
            print("⚠ Mixed quiz generation failed; falling back to MCQs per topic.")
            return self.generate_smart_questions(topics, notes_text)

        out = []
        for q in parsed:
            topic_guess = q.get("topic", "General")
            nq = self._normalize_question(q, topic_name=topic_guess)
            if nq:
                # Ensure type is one of allowed
                if nq["type"] not in ["mcq", "fill", "short", "definition"]:
                    nq["type"] = "short"
                out.append(nq)

        # If the model returned too few valid items, fallback
        if len(out) < max(3, total_questions // 2):
            print("⚠ Mixed quiz returned too few valid questions; falling back.")
            return self.generate_smart_questions(topics, notes_text)

        return out

    # ================= GRADE SHORT ANSWER =================
    def grade_short_answer(self, question: str, model_answer: str, student_answer: str, notes_text: str = ""):
        """
        New:
        Grades short answers using AI.
        Returns dict:
          {"is_correct": bool, "feedback": "..."}
        """
        prompt = f"""
You are grading a student's short answer.

Use the notes to judge correctness.

NOTES:
{(notes_text or "")[:3000]}

QUESTION:
{question}

MODEL ANSWER:
{model_answer}

STUDENT ANSWER:
{student_answer}

Return STRICT JSON object only (no markdown):
{{
  "is_correct": true/false,
  "feedback": "1-2 short sentences why"
}}
"""
        ai_response = self.call_ai(prompt, temperature=0.0)
        parsed = self.safe_parse_json(ai_response)

        if isinstance(parsed, dict):
            return {
                "is_correct": bool(parsed.get("is_correct", False)),
                "feedback": str(parsed.get("feedback", "")).strip()
            }

        # fallback basic heuristic
        correct = str(model_answer).strip().lower()
        student = str(student_answer).strip().lower()
        is_ok = bool(correct) and correct in student
        return {
            "is_correct": is_ok,
            "feedback": "Auto-checked (basic). Try to include the key points from the model answer."
        }

    # ================= GENERATE FLASHCARDS =================
    def generate_flashcards(self, topic_name: str, notes_text: str):
        prompt = f"""
Create 6 flashcards for studying.

Topic: {topic_name}

Use ONLY the notes below.

NOTES:
{notes_text[:4000]}

Return ONLY valid JSON array.
Do NOT wrap in markdown.
Format:

[
  {{
    "front": "Question or keyword",
    "back": "Clear explanation"
  }}
]
"""
        ai_response = self.call_ai(prompt, temperature=0.3)
        parsed = self.safe_parse_json(ai_response)

        if not parsed or not isinstance(parsed, list):
            print("⚠ Flashcard generation failed")
            return []

        # normalize
        out = []
        for c in parsed:
            if isinstance(c, dict) and str(c.get("front", "")).strip() and str(c.get("back", "")).strip():
                out.append({"front": str(c["front"]).strip(), "back": str(c["back"]).strip()})

        return out

    # ================= GENERATE DETAILED STUDY PLAN =================
    def generate_detailed_study_plan(self, topics, notes, total_days=None, hours_per_day=None, total_hours=None):
        topic_summary = ""
        for t in topics:
            topic_summary += f"- {t['name']} ({t['importance_score']}% importance)\n"

        if total_hours:
            time_instruction = f"""
Student has {total_hours} total hours available.
Create an hourly plan dividing topics smartly based on importance.
"""
        else:
            time_instruction = f"""
Student has {total_days} days.
Each day has approximately {hours_per_day} study hours.
Create a daily + hourly breakdown.
"""

        prompt = f"""
You are an expert academic planner.

Student Notes Summary:
{notes[:4000]}

Topics with importance:
{topic_summary}

{time_instruction}

Rules:
- Allocate more time to higher importance topics
- Include:
  - Concept learning
  - Active recall sessions
  - Practice questions with numbers (e.g., Solve 20 MCQs)
  - Daily revision blocks
  - Final mock test
- Be extremely specific and actionable
- Make it practical and realistic

Return STRICT JSON array format:

[
  {{
    "day": "Day 1",
    "schedule": [
      {{
        "time": "09:00 - 10:00",
        "task": "Study concept of ...",
        "topic": "Topic name"
      }}
    ]
  }}
]

Do NOT wrap in markdown.
Do NOT add explanation.
"""

        ai_response = self.call_ai(prompt, temperature=0.4)
        parsed = self.safe_parse_json(ai_response)

        if not parsed or not isinstance(parsed, list):
            print("⚠ Study plan generation failed")
            return []

        # normalize schedule items
        out = []
        for d in parsed:
            if not isinstance(d, dict):
                continue
            day_name = str(d.get("day", "")).strip() or "Day"
            schedule = d.get("schedule", [])
            if not isinstance(schedule, list):
                continue
            cleaned_schedule = []
            for item in schedule:
                if not isinstance(item, dict):
                    continue
                cleaned_schedule.append({
                    "time": str(item.get("time", "")).strip(),
                    "task": str(item.get("task", "")).strip(),
                    "topic": str(item.get("topic", "")).strip() or "General"
                })
            out.append({"day": day_name, "schedule": cleaned_schedule})

        return out


# Global instance
generator = QuestionGenerator()