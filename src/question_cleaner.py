# src/question_cleaner.py

import re


FILLER_PATTERNS = [
    r"^\s*(bonjour|salut|bonsoir|coucou)[,.!\s]*",
    r"^\s*merci[,.!\s]+",
    r"\s*s'il\s+(vous|te)\s+pla[iî]t[,.!?]?\s*",
    r"^\s*(est[- ]ce que|est-ce qu')\s*",
    r"^\s*(pourriez[- ]vous|pourrais[- ]tu|peux[- ]tu|pouvez[- ]vous|peut[- ]on)\s+(me\s+|m['’]\s*)?(dire|expliquer|savoir)?\s*",
    r"^\s*j'aimerais savoir\s*",
    r"^\s*je (voudrais|veux|souhaite|souhaiterais) savoir\s*",
]


class QuestionCleaner:
    def clean(self, question: str) -> str:
        cleaned = self._strip_filler_patterns(question)
        cleaned = cleaned.strip()
        cleaned = self._capitalize_first_letter(cleaned)
        return cleaned if cleaned else question

    def _strip_filler_patterns(self, question: str) -> str:
        cleaned = question
        for pattern in FILLER_PATTERNS:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
        return cleaned

    def _capitalize_first_letter(self, text: str) -> str:
        if not text:
            return text
        return text[0].upper() + text[1:]
