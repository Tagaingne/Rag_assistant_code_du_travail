# src/question_formatter_agent.py
#
# Prepare la question utilisateur pour la recherche vectorielle :
# 1) enleve les mots parasites (bonjour, peux-tu...)
# 2) decompose en sous-questions atomiques
# 3) genere une reponse hypothetique par sous-question (HyDE), utilisee comme
#    requete de recherche a la place de la question elle-meme

from src.decomposition_agent import DecompositionAgent
from src.hyde_agent import HydeAgent
from src.question_cleaner import QuestionCleaner


class QuestionFormatterAgent:
    def __init__(self):
        self.question_cleaner = QuestionCleaner()
        self.decomposition_agent = DecompositionAgent()
        self.hyde_agent = HydeAgent()

    def format_question(self, question: str) -> list[str]:
        question_nettoyee = self.question_cleaner.clean(question)
        sous_questions = self.decomposition_agent.decompose_question(question_nettoyee)
        return self._generate_search_queries(sous_questions)

    def _generate_search_queries(self, sous_questions: list[str]) -> list[str]:
        return [
            self.hyde_agent.generate_hypothetical_answer(sous_question)
            for sous_question in sous_questions
        ]
