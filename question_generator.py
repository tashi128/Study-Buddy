import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")


class QuestionGenerator:

    # ================= CALL AI =================
    def call_ai(self, prompt, temperature=0.3):

        if not DEEPSEEK_API_KEY:
            print("❌ DeepSeek API key missing")
            return None

        try:
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": "You are an expert teacher who returns strictly valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": temperature,
                },
                timeout=60
            )

            result = response.json()

            if "choices" not in result:
                print("❌ Unexpected API response:", result)
                return None

            content = result["choices"][0]["message"]["content"]
            return content

        except Exception as e:
            print("❌ AI CALL ERROR:", e)
            return None

    # ================= SAFE JSON PARSER =================
    def safe_parse_json(self, ai_response):

        if not ai_response:
            return None

        cleaned = ai_response.strip()

        # Remove markdown if present
        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```json", "")
            cleaned = cleaned.replace("```", "")
            cleaned = cleaned.strip()

        # Extract JSON array only
        start = cleaned.find("[")
        end = cleaned.rfind("]") + 1

        if start == -1 or end == -1:
            print("⚠ No JSON array found in AI response")
            print("RAW RESPONSE:\n", ai_response)
            return None

        json_text = cleaned[start:end]

        try:
            parsed = json.loads(json_text)
            return parsed
        except Exception as e:
            print("⚠ JSON still invalid:", e)
            print("BROKEN JSON:\n", json_text)
            return None

    # ================= GENERATE QUESTIONS =================
    def generate_smart_questions(self, topics, notes_text):

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
    "question": "...",
    "options": ["A","B","C","D"],
    "correct": "exact correct option text"
  }}
"""

            ai_response = self.call_ai(prompt)

            if not ai_response:
                print("⚠ Skipping topic due to empty AI response")
                continue

            parsed = self.safe_parse_json(ai_response)

            if not parsed:
                print("⚠ Skipping topic due to parsing failure")
                continue

            # Attach topic name
            for q in parsed:
                q["topic"] = topic["name"]

            all_questions.extend(parsed)

        return all_questions

    # ================= GENERATE FLASHCARDS =================
    def generate_flashcards(self, topic_name, notes_text):

        prompt = f"""
Create 6 flashcards for studying.

Topic: {topic_name}

Use ONLY the notes below.

NOTES:
{notes_text[:4000]}

Return ONLY valid JSON.
Do NOT wrap in markdown.
Format:

[
  {{
    "front": "Question or keyword",
    "back": "Clear explanation"
  }}
]
"""

        ai_response = self.call_ai(prompt)

        parsed = self.safe_parse_json(ai_response)

        if not parsed:
            print("⚠ Flashcard generation failed")
            return []

        return parsed


# Global instance
generator = QuestionGenerator()
