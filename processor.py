from typing import List, Dict

class DocumentProcessor:
    """Simple document processor to extract topics with importance %"""

    def extract_topics_from_texts(self, lecture_texts: List[str]) -> List[Dict]:
        """
        Extract topics from a list of lecture texts.
        Returns a list of dicts with 'name' and 'importance_score'
        """
        if not lecture_texts:
            return [{"name": "General Concepts", "importance_score": 50}]

        # Join all texts into a single string
        all_text = " ".join(lecture_texts).lower()

        keywords = [
            "Machine Learning", "Artificial Intelligence", "Neural Networks",
            "Deep Learning", "Data Science", "Computer Vision"
        ]

        topics = []
        for k in keywords:
            count = all_text.count(k.lower())
            if count > 0:
                importance = min(count * 10, 100)
                topics.append({
                    "name": k,
                    "importance_score": importance
                })

        if not topics:
            topics.append({"name": "General Concepts", "importance_score": 50})

        # Sort topics by importance
        topics.sort(key=lambda x: x["importance_score"], reverse=True)
        return topics

processor = DocumentProcessor()
