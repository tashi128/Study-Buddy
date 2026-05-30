import os
import json
import time
import re
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

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

    def __init__(self):
        self.last_error = None

    # ================= CALL AI =================
    def call_ai(self, prompt: str, temperature: float = 0.3, timeout: int = 60, retries: int = 2):
        self.last_error = None
        if not DEEPSEEK_API_KEY:
            self.last_error = "DeepSeek API key missing (DEEPSEEK_API_KEY)."
            print(f"❌ {self.last_error}")
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
                # import requests lazily so this module can be imported without requests installed
                try:
                    import requests
                except Exception as e:
                    self.last_error = "Missing dependency: requests."
                    print("⚠ The 'requests' package is required for AI calls. Install it to enable AI features.")
                    return None

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
                self.last_error = str(e)
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

    def _split_note_sentences(self, notes_text: str):
        text = (notes_text or "").strip()
        if not text:
            return []
        parts = re.split(r'(?<=[.!?])\s+|\n+', text)
        cleaned = [p.strip() for p in parts if len(p.strip()) > 30]
        return cleaned

    def _prepare_note_documents(self, notes_text: str = "", note_documents=None):
        documents = []
        for index, doc in enumerate(note_documents or [], start=1):
            text = str(doc.get("text", "")).strip()
            if not text:
                continue
            doc_id = str(doc.get("id") or f"note_{index}")
            display_label = str(doc.get("display_label") or f"Note {index}")
            title = str(doc.get("title") or display_label).strip() or display_label
            documents.append(
                {
                    "id": doc_id,
                    "display_label": display_label,
                    "title": title,
                    "text": text,
                }
            )

        if documents:
            return documents

        fallback_text = str(notes_text or "").strip()
        if not fallback_text:
            return []

        return [
            {
                "id": "note_1",
                "display_label": "Note 1",
                "title": "Combined Notes",
                "text": fallback_text,
            }
        ]

    def _build_notes_context(self, note_documents=None, notes_text: str = "", max_chars: int = 6000):
        documents = self._prepare_note_documents(notes_text=notes_text, note_documents=note_documents)
        if not documents:
            return ""

        chunks = []
        consumed = 0
        for doc in documents:
            excerpt_limit = max(300, min(1800, max_chars // max(1, len(documents))))
            excerpt = doc["text"][:excerpt_limit]
            chunk = (
                f"{doc['display_label']} | ID: {doc['id']} | Title: {doc['title']}\n"
                f"{excerpt}"
            )
            if consumed + len(chunk) > max_chars and chunks:
                break
            chunks.append(chunk)
            consumed += len(chunk)

        return "\n\n".join(chunks)

    def _match_note_ids_for_text(self, text: str, note_documents=None, fallback_limit: int = 2):
        documents = self._prepare_note_documents(note_documents=note_documents)
        query_words = {
            word.lower() for word in re.findall(r"[A-Za-z]{4,}", text or "")
        }

        if not query_words or not documents:
            return [doc["id"] for doc in documents[:fallback_limit]]

        scored = []
        for doc in documents:
            doc_words = {
                word.lower() for word in re.findall(r"[A-Za-z]{4,}", doc["text"][:4000])
            }
            overlap = len(query_words & doc_words)
            if overlap:
                scored.append((overlap, doc["id"]))

        scored.sort(reverse=True)
        matched = [doc_id for _, doc_id in scored[:fallback_limit]]
        return matched or [doc["id"] for doc in documents[:fallback_limit]]

    def _normalize_note_refs(self, note_ids, note_documents=None, fallback_text: str = ""):
        documents = self._prepare_note_documents(note_documents=note_documents)
        valid_ids = {doc["id"] for doc in documents}

        cleaned = []
        for note_id in note_ids or []:
            note_id = str(note_id).strip()
            if note_id and note_id in valid_ids and note_id not in cleaned:
                cleaned.append(note_id)

        if cleaned:
            return cleaned

        return self._match_note_ids_for_text(fallback_text, documents)

    def _fallback_questions(self, topics, notes_text: str, total: int = 8, note_documents=None):
        sentences = self._split_note_sentences(notes_text)
        if not sentences:
            return []

        topic_names = [t.get("name", "General") for t in (topics or [])] or ["General"]
        out = []
        for i in range(min(total, len(sentences))):
            s = sentences[i]
            topic = topic_names[i % len(topic_names)]
            distractor_1 = "This is not supported by the notes."
            distractor_2 = "The notes provide no relevant details."
            distractor_3 = "The exact opposite of the notes is true."
            out.append({
                "type": "mcq",
                "topic": topic,
                "question": f"Which statement best matches your notes about {topic}?",
                "options": [s, distractor_1, distractor_2, distractor_3],
                "correct": s,
                "source_note_ids": self._match_note_ids_for_text(s, note_documents),
            })
        return out

    def _fallback_flashcards(self, topic_name: str, notes_text: str, total: int = 6, note_documents=None):
        sentences = self._split_note_sentences(notes_text)
        cards = []
        for i, s in enumerate(sentences[:total], start=1):
            cards.append({
                "front": f"{topic_name} - Key Point {i}",
                "back": s,
                "source_note_ids": self._match_note_ids_for_text(s, note_documents),
            })
        return cards

    def _fallback_study_plan(self, topics, total_days=None, hours_per_day=None, total_hours=None, note_documents=None):
        if total_hours:
            days = max(1, min(7, total_hours // 2 or 1))
            hpd = max(1, total_hours // days)
        else:
            days = max(1, int(total_days or 3))
            hpd = max(1, int(hours_per_day or 2))

        topic_names = [t.get("name", "General") for t in (topics or [])] or ["General"]
        schedule_out = []
        for d in range(days):
            day_schedule = []
            for h in range(hpd):
                topic = topic_names[(d + h) % len(topic_names)]
                start_hour = 9 + h
                end_hour = start_hour + 1
                day_schedule.append({
                    "time": f"{start_hour:02d}:00 - {end_hour:02d}:00",
                    "task": f"Study and active recall for {topic}, then solve 10 practice questions.",
                    "topic": topic,
                    "source_note_ids": self._match_note_ids_for_text(topic, note_documents),
                })
            schedule_out.append({"day": f"Day {d+1}", "schedule": day_schedule})
        return schedule_out

    # ================= GENERATE QUESTIONS (MCQ ONLY, PER TOPIC) =================
    def generate_smart_questions(self, topics, notes_text: str, note_documents=None):
        """
        Your original behavior:
        - Generates MCQs per topic based on importance.
        - Returns list of questions with fields: question/options/correct/topic
        """
        all_questions = []

        if not notes_text:
            print("⚠ No notes provided")
            return []

        notes_context = self._build_notes_context(note_documents=note_documents, notes_text=notes_text, max_chars=6000)

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
{notes_context}

Rules:
- Return ONLY valid JSON
- Do NOT wrap in markdown
- Do NOT add explanation
- Must start with [ and end with ]
- Each question must have:
  {{
    "type": "mcq",
    "topic": "{topic['name']}",
    "question": "...",
    "options": ["A","B","C","D"],
    "correct": "exact correct option text",
    "source_note_ids": ["exact note id(s) from the notes context above"]
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
                    nq["source_note_ids"] = self._normalize_note_refs(
                        q.get("source_note_ids"),
                        note_documents=note_documents,
                        fallback_text=f"{nq.get('question', '')} {nq.get('correct', '')}",
                    )
                    all_questions.append(nq)

        if not all_questions:
            print("⚠ Falling back to local question generation.")
            return self._fallback_questions(topics, notes_text, total=8, note_documents=note_documents)

        return all_questions

    # ================= GENERATE MIXED QUIZ (MCQ + FILL + SHORT) =================
    def generate_mixed_quiz(self, topics, notes_text: str, total_questions: int = 12, note_documents=None):
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
        notes_context = self._build_notes_context(note_documents=note_documents, notes_text=notes_text, max_chars=6000)

        # Keep proportions reasonable
        mcq_n = max(1, int(total_questions * 0.5))
        fill_n = max(1, int(total_questions * 0.25))
        short_n = max(1, total_questions - mcq_n - fill_n)

        prompt = f"""
Generate a mixed practice quiz based ONLY on the notes.

NOTES:
{notes_context}

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
    "correct": "exact option text",
    "source_note_ids": ["exact note id(s) from the notes context above"]
  }},
  {{
    "type": "fill",
    "topic": "Topic name",
    "question": "The _____ is responsible for ...",
    "correct": "missing word/phrase",
    "source_note_ids": ["exact note id(s) from the notes context above"]
  }},
  {{
    "type": "short",
    "topic": "Topic name",
    "question": "Explain ... in 2-3 lines",
    "correct": "model short answer",
    "source_note_ids": ["exact note id(s) from the notes context above"]
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
                nq["source_note_ids"] = self._normalize_note_refs(
                    q.get("source_note_ids"),
                    note_documents=note_documents,
                    fallback_text=f"{nq.get('question', '')} {nq.get('correct', '')}",
                )
                out.append(nq)

        # If the model returned too few valid items, fallback
        if len(out) < max(3, total_questions // 2):
            print("⚠ Mixed quiz returned too few valid questions; falling back.")
            return self.generate_smart_questions(topics, notes_text, note_documents=note_documents)

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
    def generate_flashcards(self, topic_name: str, notes_text: str, note_documents=None):
        notes_context = self._build_notes_context(note_documents=note_documents, notes_text=notes_text, max_chars=5000)
        prompt = f"""
Create 6 flashcards for studying.

Topic: {topic_name}

Use ONLY the notes below.

NOTES:
{notes_context}

Return ONLY valid JSON array.
Do NOT wrap in markdown.
Format:

[
  {{
    "front": "Question or keyword",
    "back": "Clear explanation",
    "source_note_ids": ["exact note id(s) from the notes context above"]
  }}
]
"""
        ai_response = self.call_ai(prompt, temperature=0.3)
        parsed = self.safe_parse_json(ai_response)

        if not parsed or not isinstance(parsed, list):
            print("⚠ Flashcard generation failed")
            return self._fallback_flashcards(topic_name, notes_text, total=6, note_documents=note_documents)

        # normalize
        out = []
        for c in parsed:
            if isinstance(c, dict) and str(c.get("front", "")).strip() and str(c.get("back", "")).strip():
                out.append({
                    "front": str(c["front"]).strip(),
                    "back": str(c["back"]).strip(),
                    "source_note_ids": self._normalize_note_refs(
                        c.get("source_note_ids"),
                        note_documents=note_documents,
                        fallback_text=f"{c.get('front', '')} {c.get('back', '')}",
                    ),
                })

        if not out:
            return self._fallback_flashcards(topic_name, notes_text, total=6, note_documents=note_documents)

        return out


    # ================= GENERATE DETAILED STUDY PLAN =================
    def generate_detailed_study_plan(self, topics, notes, total_days=None, hours_per_day=None, total_hours=None, note_documents=None):
        topic_summary = ""
        for t in topics:
            topic_summary += f"- {t['name']} ({t['importance_score']}% importance)\n"

        notes_context = self._build_notes_context(note_documents=note_documents, notes_text=notes, max_chars=6000)

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
{notes_context}

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
        "topic": "Topic name",
        "source_note_ids": ["exact note id(s) from the notes context above"]
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
            return self._fallback_study_plan(
                topics,
                total_days=total_days,
                hours_per_day=hours_per_day,
                total_hours=total_hours,
                note_documents=note_documents,
            )

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
                    "topic": str(item.get("topic", "")).strip() or "General",
                    "source_note_ids": self._normalize_note_refs(
                        item.get("source_note_ids"),
                        note_documents=note_documents,
                        fallback_text=f"{item.get('topic', '')} {item.get('task', '')}",
                    ),
                })
            out.append({"day": day_name, "schedule": cleaned_schedule})

        if not out:
            return self._fallback_study_plan(
                topics,
                total_days=total_days,
                hours_per_day=hours_per_day,
                total_hours=total_hours,
                note_documents=note_documents,
            )

        return out


# Global instance
generator = QuestionGenerator()
