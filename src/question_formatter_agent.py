# src/question_formatter_agent.py
#
# Prepare la question utilisateur pour la recherche vectorielle :
# 1) enleve les mots parasites (bonjour, peux-tu...)
# 2) decompose en sous-questions atomiques
# 3) pour chaque sous-question, cherche avec la sous-question elle-meme ET
#    avec une reponse hypothetique (HyDE). HyDE reste volontairement vague sur
#    les chiffres/faits precis (voir prompts/hyde_prompt_system.txt) : pour une
#    question chiffree ("combien de jours ?"), ca peut l'eloigner de l'article
#    qui donne le chiffre exact. Garder aussi la sous-question brute compense
#    ce cas sans perdre le benefice de HyDE sur les questions plus conceptuelles.
#
# Le retour est groupe par sous-question (pas une liste plate) : RagAgent en a
# besoin pour repartir equitablement le contexte entre sous-questions plutot
# que de les fusionner et trier globalement (un sujet qui matche mieux
# evincerait sinon totalement un autre sujet du contexte final).

from src.decomposition_agent import DecompositionAgent
from src.hyde_agent import HydeAgent
from src.question_cleaner import QuestionCleaner


class QuestionFormatterAgent:
    def __init__(self):
        self.question_cleaner = QuestionCleaner()
        self.decomposition_agent = DecompositionAgent()
        self.hyde_agent = HydeAgent()

    def format_question(self, question: str) -> list[list[str]]:
        question_nettoyee = self.question_cleaner.clean(question)
        sous_questions = self.decomposition_agent.decompose_question(question_nettoyee)
        return [self._build_query_group(sous_question) for sous_question in sous_questions]

    def _build_query_group(self, sous_question: str) -> list[str]:
        return [sous_question, self.hyde_agent.generate_hypothetical_answer(sous_question)]
