# question_generator.py - SIMPLE and ERROR-FREE

import json
import random
from typing import List, Dict, Any

class QuestionGenerator:
    """Simple question generator - no database storage issues"""
    
    def __init__(self):
        print("❓ QuestionGenerator ready")
    
    def generate_question_set(self, topics: List[Dict], 
                            num_questions: int = 10) -> List[Dict]:
        """Generate questions - SIMPLE and RELIABLE"""
        print(f"🎯 Generating {num_questions} questions...")
        
        questions = []
        question_types = ["mcq", "true_false", "short_answer"]
        
        for i in range(min(num_questions, len(topics))):
            topic = topics[i % len(topics)]
            topic_name = topic.get("name", "General Topic")
            q_type = question_types[i % len(question_types)]
            
            # Generate question based on type
            if q_type == "mcq":
                question = self._create_mcq(topic_name)
            elif q_type == "true_false":
                question = self._create_true_false(topic_name)
            else:
                question = self._create_short_answer(topic_name)
            
            questions.append(question)
        
        print(f"✅ Generated {len(questions)} questions")
        return questions
    
    def _create_mcq(self, topic: str) -> Dict:
        """Create a multiple choice question"""
        return {
            "topic": topic,
            "question": f"What is the main concept of {topic}?",
            "question_type": "mcq",
            "options": [
                "The fundamental principle behind it",
                "A related but different concept",
                "An application in real world",
                "A historical development"
            ],
            "correct_answer": "The fundamental principle behind it",
            "explanation": f"This question tests your understanding of {topic}.",
            "difficulty": "medium"
        }
    
    def _create_true_false(self, topic: str) -> Dict:
        """Create a true/false question"""
        return {
            "topic": topic,
            "question": f"{topic} is always applicable in every situation.",
            "question_type": "true_false",
            "correct_answer": "False",
            "explanation": f"While {topic} is important, there are usually exceptions or special cases.",
            "difficulty": "easy"
        }
    
    def _create_short_answer(self, topic: str) -> Dict:
        """Create a short answer question"""
        return {
            "topic": topic,
            "question": f"Explain {topic} in your own words.",
            "question_type": "short_answer",
            "correct_answer": f"{topic} is an important concept that involves key principles and applications.",
            "explanation": "A good explanation should cover the main aspects and why it's important.",
            "difficulty": "medium"
        }

# Create instance
generator = QuestionGenerator()