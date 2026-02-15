from typing import List, Dict
import re
from collections import Counter

class DocumentProcessor:
    def extract_topics_from_texts(self, texts: List[str]) -> List[Dict]:
        text = " ".join(texts)

        words = re.findall(r"[A-Za-z]{5,}", text)
        freq = Counter(words)

        common = freq.most_common(5)
        total = sum(c for _, c in common) or 1

        return [
            {
                "name": word.capitalize(),
                "importance_score": round((count / total) * 100, 2)
            }
            for word, count in common
        ]

processor = DocumentProcessor()
