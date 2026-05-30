from typing import List, Dict
import re
from collections import Counter

class DocumentProcessor:
    STOPWORDS = {
        "about", "after", "again", "being", "below", "between", "could",
        "every", "first", "found", "having", "other", "should", "their",
        "there", "these", "those", "through", "under", "until", "where",
        "which", "while", "would", "because", "before", "during", "notes",
        "study", "topic", "chapter", "section", "introduction", "important",
        "summary", "definition", "concept", "general"
    }

    def _extract_word_frequencies(self, text: str) -> Counter:
        words = re.findall(r"[A-Za-z]{5,}", text or "")
        filtered = [word.lower() for word in words if word.lower() not in self.STOPWORDS]
        return Counter(filtered)

    def extract_topics_from_documents(self, documents: List[Dict], top_n: int = 8) -> List[Dict]:
        aggregate = Counter()
        word_sources = {}

        for doc in documents or []:
            doc_id = doc.get("id")
            doc_title = doc.get("title", "Untitled Note")
            doc_freq = self._extract_word_frequencies(doc.get("text", ""))
            aggregate.update(doc_freq)

            for word in doc_freq:
                source_bucket = word_sources.setdefault(word, {"note_ids": set(), "note_titles": set()})
                if doc_id:
                    source_bucket["note_ids"].add(doc_id)
                source_bucket["note_titles"].add(doc_title)

        common = aggregate.most_common(top_n)
        total = sum(count for _, count in common) or 1

        topics = []
        for word, count in common:
            sources = word_sources.get(word, {"note_ids": set(), "note_titles": set()})
            topics.append(
                {
                    "name": word.capitalize(),
                    "importance_score": round((count / total) * 100, 2),
                    "note_ids": sorted(sources["note_ids"]),
                    "note_titles": sorted(sources["note_titles"]),
                }
            )

        return topics

    def extract_topics_from_texts(self, texts: List[str]) -> List[Dict]:
        documents = [
            {"id": f"text_{index + 1}", "title": f"Text {index + 1}", "text": text}
            for index, text in enumerate(texts or [])
            if (text or "").strip()
        ]
        return self.extract_topics_from_documents(documents)

processor = DocumentProcessor()
