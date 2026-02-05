from typing import List, Dict

class DocumentProcessor:
    def extract_topics_from_text(self, text: str) -> List[Dict]:
        keywords = [
            "Machine Learning", "Artificial Intelligence", "Neural Networks",
            "Deep Learning", "Data Science", "Computer Vision"
        ]

        topics = []
        for k in keywords:
            if k.lower() in text.lower():
                topics.append({
                    "name": k,
                    "importance_score": text.lower().count(k.lower()) * 10
                })

        if not topics:
            topics.append({"name": "General Concepts", "importance_score": 50})

        return topics

processor = DocumentProcessor()

