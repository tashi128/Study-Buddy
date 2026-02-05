from typing import List, Dict
import random

class QuestionGenerator:
    """Fallback question generator if AI fails"""

    def generate_question_set(self, topics: List[Dict], num_questions=5) -> List[Dict]:
        questions = []
        for t in topics[:num_questions]:
            correct = "Core concept"
            distractors = ["Unrelated idea", "Historical detail", "Minor application"]
            options = distractors + [correct]
            random.shuffle(options)

            questions.append({
                "question": f"What best describes {t['name']}?",
                "options": options,
                "correct": correct
            })
        return questions

# Global instance
generator = QuestionGenerator()
