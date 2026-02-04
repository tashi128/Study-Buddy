from typing import List, Dict

class QuestionGenerator:
    def generate_question_set(self, topics: List[Dict], num_questions=5):
        questions = []
        for t in topics[:num_questions]:
            questions.append({
                "question": f"What best describes {t['name']}?",
                "options": [
                    "Core concept",
                    "Unrelated idea",
                    "Historical detail",
                    "Minor application"
                ],
                "correct": "Core concept"
            })
        return questions

generator = QuestionGenerator()
